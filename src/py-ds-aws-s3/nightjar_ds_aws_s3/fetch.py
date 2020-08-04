
"""Fetch files from the S3 backend."""

from typing import Dict, Set, Tuple, Iterable, Union, Optional
import datetime
from . import s3
from .config import Config
from .util import get_version_from_data_key_name, is_data_file, is_meta_file


def fetch(config: Config, document: str, output_file: str, previous_version: str) -> int:
    """Fetch the document into the output file.

    Because of the multi-stage method for getting the file, the fetch may
    require a retry.

    1. Pull a list of the entries from S3.
    2. From the pulled list, find the .data entry that has the most recent
        commit date.  If there isn't one, need a retry.
    3. From the pulled list, find the .meta entry that matches the .data
        entry.  If there isn't one, need a retry.
    4. Download the .data file.  If it doesn't exist, need a retry.
    """
    if config.is_test_mode:
        return 13

    res = find_top_data_entry(config, document)
    if isinstance(res, int):
        return res

    key, version = res
    if version.strip() == previous_version.strip():
        return 30
    data = s3.download(config, key)
    if isinstance(data, int):
        return data

    with open(output_file, 'wb') as f:
        f.write(data)

    return 0


def find_top_data_entry(config: Config, document: str) -> Union[int, Tuple[str, str]]:
    """Pull the list of S3 entries and find the best candidates, or return 30 if a
    retry is needed."""

    entries = s3.list_entries(config, s3.get_document_s3_path(config, document))
    data_entries, known_meta_versions = get_data_meta_entries(entries)
    latest_data, latest_version = find_latest_data_version(data_entries, known_meta_versions)

    if not latest_data:
        # Recoverable error
        return 31
    return latest_data, latest_version


def find_latest_data_version(
        data_entries: Dict[str, datetime.datetime],
        known_meta_versions: Set[str],
) -> Tuple[Optional[str], str]:
    """Find the latest version of the data entries' key and version.'"""
    latest_data: Optional[str] = None
    latest_data_version: str = ''
    latest_data_date: Optional[datetime.datetime] = None
    for key, when in data_entries.items():
        version = get_version_from_data_key_name(key)
        if version in known_meta_versions and (not latest_data_date or when > latest_data_date):
            latest_data = key
            latest_data_version = version
            latest_data_date = when
    return latest_data, latest_data_version


def get_data_meta_entries(
        entries: Iterable[Tuple[str, datetime.datetime]],
) -> Tuple[Dict[str, datetime.datetime], Set[str]]:
    """Get all the data entries with their time stamp, and the meta entries' versions."""
    known_meta_versions: Set[str] = set()
    data_entries: Dict[str, datetime.datetime] = {}

    # The `entries` iterable is usually a generator, so we get one pass on it.
    for key, when in entries:
        if is_data_file(key):
            data_entries[key] = when
        elif is_meta_file(key):
            version = get_version_from_data_key_name(key)
            known_meta_versions.add(version)

    return data_entries, known_meta_versions
