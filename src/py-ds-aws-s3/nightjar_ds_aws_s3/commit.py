
"""Commits files to the S3 backend."""

from typing import Dict, Tuple, Sequence, List, Union, Any
import json
import hashlib
import uuid
import datetime
from .config import Config
from .util import is_data_file, is_meta_file, get_version_from_data_key_name
from . import s3


DOCUMENT_VERSION_KEY = 'document-version'
OLD_FILE_TIME_DAYS = 1
OLD_FILE_TIME = datetime.timedelta(days=OLD_FILE_TIME_DAYS)


def commit(config: Config, document: str, src_file: str) -> int:
    """Commit the document to the backend.

    Committing files is a multi-step process.

    1. The document source is prepared for commit.
    2. An inventory is taken of all existing versions of the document and their metadata files.
      Only files that are pairs are considered.
    3. The new files are written to S3 (document, then metadata).
    4. The old file pairs are removed, singleton metadata files are removed
        outright (there should be a document then metadata).  Document files that have an "old"
        date are removed.
    """
    if config.is_test_mode:
        return 12

    # Prepare for commit
    info = load_document_information(document, src_file)
    if isinstance(info, int):
        return info
    version, metadata, data = info
    metadata_bytes = json_binary_dump(metadata)
    data_bytes = json_binary_dump(data)

    # Get original keys
    original_entries = list(s3.list_entries(config, s3.get_document_s3_path(config, document)))

    # Upload document then metadata
    res = s3.upload(config, s3.get_version_file_s3_key(config, document, version), data_bytes)
    if res != 0:
        return res
    res = s3.upload(config, s3.get_meta_file_s3_key(config, document, version), metadata_bytes)
    if res != 0:
        # This isn't a good state.  It will hopefully be cleaned up later.
        return res

    # Remove old keys
    s3.delete(config, filter_old_document_entries(original_entries))

    return 0


def load_document_information(
        document: str, src_file: str,
) -> Union[int, Tuple[str, Dict[str, Any], Dict[str, Any]]]:
    """Load the document contents from disk, and extract the metadata information."""
    try:
        with open(src_file, 'r') as f:
            metadata, doc = create_document_metadata(document, json.load(f))
        return metadata['document-version'], metadata, doc
    except ValueError as err:
        print("[nightjar-ds-aws-s3] Invalid source file format: " + repr(err))
        return 1


def create_document_metadata(
        document_name: str, data: Dict[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Create the unique document version, and attach it to the document data."""

    # The hash and size are based on the data with a blank version value.
    data[DOCUMENT_VERSION_KEY] = ''
    raw_data = json_binary_dump(data)
    data_size = len(raw_data)

    # Get the hash of the contents.
    # MD5 is not cryptographically strong, but it's strong enough
    # in combination with the timestamp.
    hashing = hashlib.md5()
    hashing.update(raw_data)
    hash_text = hashing.hexdigest()

    # Get the current time.  Note that this is the UTC time.
    now = datetime.datetime.utcnow()

    # Create the version
    version = uuid.uuid1().hex

    data[DOCUMENT_VERSION_KEY] = version
    return {
        'document': document_name,
        'document-version': version,
        'bare-contents-md5': hash_text,
        'bare-contents-size': data_size,
        'local-time': now.isoformat(),
    }, data


def filter_old_document_entries(entries: Sequence[Tuple[str, datetime.datetime]]) -> List[str]:
    """Select the old S3 keys that will need to be removed after the commit completes."""
    # Note that we're comparing S3 files against the UTC time, because we need the timezone
    # component for correct comparison.
    now = datetime.datetime.now(datetime.timezone.utc)

    groups: Dict[str, List[str]] = {}
    by_time: Dict[str, datetime.datetime] = {}
    for key, when in entries:
        if not is_data_file(key) and not is_meta_file(key):
            # Not a file we're interested in.  Skip it.
            continue
        version = get_version_from_data_key_name(key)
        if version not in groups:
            groups[version] = []
        groups[version].append(key)
        by_time[key] = when

    # Now that we have the data split up, we'll analyze it.
    ret: List[str] = []
    for paths in groups.values():
        if len(paths) >= 2:
            # There's enough here to remove them.
            ret.extend(paths)
        elif paths:
            # We have a dangler.
            key = paths[0]
            # If it's a meta file, then outright remove it.
            if is_meta_file(key):
                ret.append(key)
            else:
                # If the file is "old", then remove it.
                when = by_time[key]
                if now - when > OLD_FILE_TIME:
                    ret.append(key)
    return ret


def json_binary_dump(doc: Dict[str, Any]) -> bytes:
    """Dump the document as a JSON format, encoded in UTF-8."""
    return json.dumps(doc).encode('utf-8', 'replace')
