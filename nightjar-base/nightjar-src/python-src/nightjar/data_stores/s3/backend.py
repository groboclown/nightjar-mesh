
from typing import Iterable, Dict, Tuple, List, Set, Optional, Any
import datetime
import hashlib
import io
import re

import boto3
from botocore.config import Config  # type: ignore

from .config import S3EnvConfig
from ..abc_backend import (
    AbcDataStoreBackend, ServiceColorEntity, NamespaceEntity, Entity,
    SUPPORTED_ACTIVITIES,
)
from ...msg import note, debug

DEFAULT_SERVICE_NAME = '__default__'
DEFAULT_COLOR_NAME = '__default__'
DEFAULT_NAMESPACE_NAME = '__default__'
MAX_CONTENT_SIZE = 4 * 1024 * 1024  # 4 MB

# Matches namespace, activity, purpose
# Note that this doesn't have any matching for the base path or the version.
NAMESPACE_PATH_RE = re.compile(r'/namespace/([^/]+)/([^/]+)/(.*)$')

# Matches service, color, activity, purpose
# Note that this doesn't have any matching for the base path or the version.
SERVICE_COLOR_PATH_RE = re.compile(r'/service/([^/]+)/([^/]+)/([^/]+)/(.*)$')


class ProcessingVersion:
    count = 0
    uploaded_data: Dict[str, Tuple[Entity, bytes]]
    __slots__ = ('name', 'activity', 'uploaded_data')

    def __init__(self, activity: str) -> None:
        # This isn't thread safe, but additionally this shouldn't be run in multiple threads.
        self.name = '{0}-{1}'.format(activity, ProcessingVersion.count)
        self.activity = activity
        ProcessingVersion.count += 1
        self.uploaded_data = {}

    def add_entity(self, entity: Entity, contents: str) -> None:
        data = contents.encode('utf-8')
        assert len(data) < MAX_CONTENT_SIZE
        self.uploaded_data[get_entity_path('', entity)] = (entity, data)

    def get_final_version_name(self) -> str:
        hashing = hashlib.md5()
        keys = list(self.uploaded_data.keys())
        keys.sort()
        for key in keys:
            hashing.update(self.uploaded_data[key][1])
        now = datetime.datetime.now(datetime.timezone.utc)
        return "{a}/{y:04d}{mo:02d}{d:02d}{hr:02d}{mi:02d}{s:02d}-{hs}".format(
            a=self.activity, hs=hashing.hexdigest(),
            y=now.year, mo=now.month, d=now.day, hr=now.hour, mi=now.minute, s=now.second,
        )

    def clear(self) -> None:
        self.uploaded_data.clear()


class S3Backend(AbcDataStoreBackend):
    """
    This implementation uses per-S3 object to store each object.

    The stored objects is based on paths.

    - versions:  The list of versions, by activity, is in the path 'version/(activity)/(id)'.
        The contents of the object is not important.  Only when something is committed is the id
        added into the list.  The ID is the md5 sum of the contents added to the version.

    - namespace entities: the files are stored in '(version)/namespace/(namespace)/(template or extracted)/(purpose)'.

    - service/color entities: the files are stored under the path
      '(version)/service/(service)/(color)/(template or extracted)/(purpose)'.
    """
    active_versions: Dict[str, ProcessingVersion]
    client: Optional[Any]  # mypy_boto3.s3.S3Client

    def __init__(self, config: S3EnvConfig) -> None:
        self.config = config
        self.client = None
        self.active_versions = {}

    def get_client(self) -> Any:
        if not self.client:
            self.client = boto3.session.Session(
                region_name=self.config.aws_region,
                profile_name=self.config.aws_profile,  # type: ignore
            ).client('s3', config=Config(
                max_pool_connections=1,
                retries=dict(max_attempts=2)
            ))
        return self.client

    # -----------------------------------------------------------------------
    # Read Actions

    def get_active_version(self, activity: str) -> str:
        if activity not in SUPPORTED_ACTIVITIES:
            raise ValueError('invalid activity {0}; valid values are {1}'.format(activity, SUPPORTED_ACTIVITIES))
        most_recent: Optional[datetime.datetime] = None
        active_key: str = 'first'
        for key, last_modified in self._get_versions(activity):
            if not most_recent or last_modified > most_recent:
                active_key = key
                most_recent = last_modified
        return active_key

    def download(self, version: str, entity: Entity) -> str:
        path = get_entity_path(version, entity)
        return self._download(path)

    def get_namespace_entities(
            self, version: str, namespace: Optional[str] = None, purpose: Optional[str] = None,
            is_template: Optional[bool] = None
    ) -> Iterable[NamespaceEntity]:
        prefix = '{0}/namespace'.format(version)
        if namespace:
            # We can add the namespace to our search qualification.
            prefix += '/' + namespace
            if is_template is not None:
                # We can only add is-template if namespace is also specified.
                prefix += '/' + ('template' if is_template else 'extracted')
                # We can only add purpose if namespace and is_template are also specified.
                if purpose:
                    prefix += '/' + purpose
        debug(
            "Searching for namespace entities ({n}, {p}, {t}) with prefix {x}/",
            n=namespace, p=purpose, t=is_template, x=prefix
        )
        for path, when in self._list_entries(prefix + '/'):
            # Because the match does not require matching everything at the start, this uses "search".
            match = NAMESPACE_PATH_RE.search(path)
            if match:
                m_namespace: Optional[str] = match.group(1)
                if m_namespace == DEFAULT_NAMESPACE_NAME:
                    m_namespace = None
                # We're searching, so if namespace is None, then we want all the namespace templates.
                if namespace is None or namespace == m_namespace:
                    m_activity = match.group(2)
                    m_is_template = m_activity == 'template'
                    if is_template is None or is_template == m_is_template:
                        m_purpose = match.group(3)
                        if purpose is None or purpose == m_purpose:
                            yield NamespaceEntity(m_namespace, m_purpose, m_is_template)
            else:
                debug("no match for object {p}", p=path)

    def get_service_color_entities(
            self, version: str, service: Optional[str] = None, color: Optional[str] = None,
            purpose: Optional[str] = None, is_template: Optional[bool] = None
    ) -> Iterable[ServiceColorEntity]:
        prefix = '{0}/service'.format(version)
        if service:
            # We can add the service to our search qualification.
            prefix += '/' + service
            if color is not None:
                # We can only add the color if service is also specified.
                prefix += '/' + color
                if is_template is not None:
                    # We can only add is-template if service and color are also specified.
                    prefix += '/' + ('template' if is_template else 'extracted')
                    # We can only add purpose if service, color, and is_template are also specified.
                    if purpose:
                        prefix += '/' + purpose
        for path, when in self._list_entries(prefix):
            # Because the match does not require matching everything at the start, this uses "search".
            match = SERVICE_COLOR_PATH_RE.search(path)
            if match:
                m_service: Optional[str] = match.group(1)
                if m_service == DEFAULT_SERVICE_NAME:
                    m_service = None
                if service is None or service == m_service:
                    m_color: Optional[str] = match.group(2)
                    if m_color == DEFAULT_COLOR_NAME:
                        m_color = None
                    if color is None or color == m_color:
                        m_activity = match.group(3)
                        m_is_template = m_activity == 'template'
                        if is_template is None or is_template == m_is_template:
                            m_purpose = match.group(4)
                            if purpose is None or purpose == m_purpose:
                                yield ServiceColorEntity(m_service, m_color, m_purpose, m_is_template)

    # -----------------------------------------------------------------------
    # Write Actions

    def start_changes(self, activity: str) -> str:
        if activity not in SUPPORTED_ACTIVITIES:
            raise ValueError('invalid activity {0}; valid values are {1}'.format(activity, SUPPORTED_ACTIVITIES))
        version = ProcessingVersion(activity)
        self.active_versions[version.name] = version
        return version.name

    def commit_changes(self, version: str) -> None:
        activity_version = self.active_versions[version]
        del self.active_versions[version]

        # Grab the last active version, so that it can be preserved when performing
        # an old-version purge.
        previously_active_version = self.get_active_version(activity_version.activity)

        # The data is only written when the commit happens.
        # That's the only way we'll make sure we have all the data necessary to
        # compute the checksum.  This can mean lots of extra memory usage, though,
        # so this isn't great.
        final_version = activity_version.get_final_version_name()
        uploaded_paths = []
        try:
            for entity, data in activity_version.uploaded_data.values():
                path = get_entity_path(final_version, entity)
                self._upload(path, data)
                uploaded_paths.append(path)
            self._upload(
                'version/{0}'.format(final_version),
                final_version.encode('utf-8')
            )
        except Exception as err:
            self._delete(uploaded_paths)
            raise

        # Clean up our memory before moving on.
        activity_version.clear()

        if self.config.purge_old_versions:
            self._clean_old_versions(
                activity_version.activity,
                self.config.purge_older_than_days,
                {final_version, previously_active_version},
            )

    def rollback_changes(self, version: str) -> None:
        """Performed on error, to revert any uploads."""
        # Because uploads are delayed until commit, this does nothing with
        # s3 store.
        if version in self.active_versions:
            del self.active_versions[version]

    def upload(self, version: str, entity: Entity, contents: str) -> None:
        activity_version = self.active_versions[version]
        activity_version.add_entity(entity, contents)

    # -----------------------------------------------------------------------
    # Support

    def _get_versions(self, activity: str) -> Iterable[Tuple[str, datetime.datetime]]:
        for key, when in self._list_entries('version/{0}/'.format(activity)):
            if '/' in key:
                key = key[key.rindex('/') + 1:]
                if key:
                    yield activity + '/' + key, when

    def _clean_old_versions(
            self, activity: str,
            purge_older_than_days: int,
            do_not_remove_versions: Set[str],
    ) -> None:
        # This should remove any version older than (some old date), but always leave
        # the previously active version around, in case anything is actively pulling from it.
        # That is, delete all versions before date except for previously_active_version and
        # final_version.
        older_than = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=purge_older_than_days)
        for version, when in self._get_versions(activity):
            if version not in do_not_remove_versions and when < older_than:
                note('Removing old activity {a} version {v}', a=activity, v=version)
                to_delete = [d[0] for d in self._list_entries(version + '/')]
                # version string includes the activity...
                to_delete.append('version/{0}'.format(version))
                self._delete(to_delete)

    def _list_entries(self, path: str) -> Iterable[Tuple[str, datetime.datetime]]:
        while path[0] == '/':
            path = path[1:]
        full_path = self.config.base_path + '/' + path
        debug("Listing entries under {p}", p=full_path)
        paginator = self.get_client().get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(
            Bucket=self.config.bucket,
            EncodingType='url',
            Prefix=full_path,
            FetchOwner=False,
        )
        for page in response_iterator:
            if 'Contents' not in page:
                continue
            for info in page['Contents']:
                key = info.get('Key', '')
                modified = info.get('LastModified', None)
                if key and modified and info.get('Size', 0) < MAX_CONTENT_SIZE:
                    yield key, modified

    def _upload(self, path: str, contents: bytes) -> None:
        assert len(contents) < MAX_CONTENT_SIZE
        # Shouldn't be necessary due to the construction of the path argument... this is defensive coding.
        while path[0] == '/':
            path = path[1:]
        full_path = self.config.base_path + '/' + path
        print("Uploading {0}".format(full_path))
        inp = io.BytesIO(contents)
        self.get_client().upload_fileobj(inp, self.config.bucket, full_path)

    def _download(self, path: str) -> str:
        # Shouldn't be necessary due to the construction of the path argument... this is defensive coding.
        while path[0] == '/':
            path = path[1:]
        out = io.BytesIO()
        self.get_client().download_fileobj(self.config.bucket, self.config.base_path + '/' + path, out)
        return out.getvalue().decode('utf-8')

    def _delete(self, paths: List[str]) -> None:
        if len(paths) <= 0:
            return
        if len(paths) > 1000:
            raise Exception("Cannot handle > 1000 paths right now.")
        keys = []
        for path in paths:
            if path[0] == '/':
                keys.append(path)
            else:
                keys.append(self.config.base_path + '/' + path)
        self.get_client().delete_objects(
            Bucket=self.config.bucket,
            Delete={
                'Objects': [{'Key': p} for p in keys]
            }
        )


def get_entity_path(version: str, entity: Entity) -> str:
    if isinstance(entity, ServiceColorEntity):
        return '{0}/service/{1}/{2}/{3}/{4}'.format(
            version, entity.service or DEFAULT_SERVICE_NAME, entity.color or DEFAULT_COLOR_NAME,
            'template' if entity.is_template else 'extracted',
            entity.purpose
        )
    assert isinstance(entity, NamespaceEntity)
    return '{0}/namespace/{1}/{2}/{3}'.format(
        version, entity.namespace or DEFAULT_NAMESPACE_NAME,
        'template' if entity.is_template else 'extracted',
        entity.purpose
    )
