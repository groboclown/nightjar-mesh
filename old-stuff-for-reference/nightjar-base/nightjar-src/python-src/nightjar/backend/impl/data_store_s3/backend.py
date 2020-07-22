
"""Data store backend for S3"""

from typing import Iterable, Dict, Tuple, List, Set, Optional, Any
import datetime
import hashlib
import io
import re

import boto3
from botocore.config import Config  # type: ignore

from .config import S3EnvConfig
from ..data_store_util import wide
from ...api.data_store import ConfigEntity
from ...api.data_store.abc_backend import (
    AbcDataStoreBackend,
    Entity,
    SUPPORTED_ACTIVITIES,
    ACTIVITY_TEMPLATE_DEFINITION,
    ACTIVITY_PROXY_CONFIGURATION,
    ServiceIdConfigEntity,
    ServiceColorTemplateEntity,
    GatewayConfigEntity,
    NamespaceTemplateEntity,
    TemplateEntity,
)
from ....protect import RouteProtection
from ....msg import note, debug

MAX_CONTENT_SIZE = 4 * 1024 * 1024  # 4 MB

# Matches namespace, activity, purpose
# Note that this doesn't have any matching for the base path or the version.
NAMESPACE_PATH_RE = re.compile(r'/namespace/([^/]+)/([^/]+)/(.*)$')

# Matches service, color, activity, purpose
# Note that this doesn't have any matching for the base path or the version.
SERVICE_COLOR_PATH_RE = re.compile(r'/service/([^/]+)/([^/]+)/([^/]+)/(.*)$')


class ProcessingVersion:
    """Processing handler for an activity, before it's committed to s3."""
    count = 0
    uploaded_data: Dict[str, Tuple[Entity, bytes]]
    __slots__ = ('name', 'activity', 'uploaded_data', 'config')

    def __init__(self, config: S3EnvConfig, activity: str) -> None:
        # This isn't thread safe, but additionally this shouldn't be run in multiple threads.
        self.name = '{0}-{1}'.format(activity, ProcessingVersion.count)
        self.activity = activity
        self.config = config
        ProcessingVersion.count += 1
        self.uploaded_data = {}

    def add_entity(self, entity: Entity, contents: str) -> None:
        """Add an entity into this version."""
        data = contents.encode('utf-8')
        assert len(data) < MAX_CONTENT_SIZE
        self.uploaded_data[self.config.get_path(
            wide.get_entity_path(self.name, entity),
        )] = (entity, data,)

    def get_final_version_name(self) -> str:
        """Get the final name for this version.  It's based on a hash of the contents,
        and a timestamp."""
        hashing = hashlib.md5()
        keys = list(self.uploaded_data.keys())
        keys.sort()
        for key in keys:
            hashing.update(self.uploaded_data[key][1])
        now = datetime.datetime.now(datetime.timezone.utc)
        return "{y:04d}{mo:02d}{d:02d}{hr:02d}{mi:02d}{s:02d}-{hs}".format(
            hs=hashing.hexdigest(),
            y=now.year, mo=now.month, d=now.day, hr=now.hour, mi=now.minute, s=now.second,
        )

    def clear(self) -> None:
        """Clear this version's pending data to upload."""
        self.uploaded_data.clear()


class S3Backend(AbcDataStoreBackend):
    """
    This implementation uses per-S3 object to store each object.

    The stored objects is based on paths.

    - versions:  The list of versions, by activity, is in the path 'version/(activity)/(id)'.
        The contents of the object is not important.  Only when something is committed is the id
        added into the list.  The ID is the md5 sum of the contents added to the version.

    - namespace entities: the files are stored in
      '(version)/namespace/(namespace)/(template or extracted)/(purpose)'.

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
        """Get the S3 client."""
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
            raise ValueError(
                'invalid activity {0}; valid values are {1}'.format(activity, SUPPORTED_ACTIVITIES)
            )
        most_recent: Optional[datetime.datetime] = None
        active_version: str = activity + '-first'
        for version, last_modified in self._get_versions(activity):
            if not most_recent or last_modified > most_recent:
                active_version = version
                most_recent = last_modified
        return active_version

    def get_template_entities(self, version: str) -> Iterable[TemplateEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(wide.get_activity_prefix(
                    version, ACTIVITY_TEMPLATE_DEFINITION,
                ))
        ):
            entity = wide.parse_template_path(version, self.config.split_key_to_path(key))
            if entity:
                yield entity

    def get_config_entities(self, version: str) -> Iterable[ConfigEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(
                    wide.get_activity_prefix(version, ACTIVITY_PROXY_CONFIGURATION)
                )
        ):
            entity = wide.parse_config_path(version, self.config.split_key_to_path(key))
            if entity:
                yield entity

    def get_namespace_template_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[NamespaceTemplateEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(wide.get_namespace_template_prefix(version))
        ):
            n_s = wide.parse_namespace_template_path(version, self.config.split_key_to_path(key))
            if not n_s:
                continue
            if (
                    (namespace is None or namespace == n_s.namespace)
                    and (protection is None or protection == n_s.protection)
                    and (purpose is None or purpose == n_s.purpose)
            ):
                yield n_s

    def get_gateway_config_entities(
            self, version: str, namespace: Optional[str] = None,
            protection: Optional[RouteProtection] = None, purpose: Optional[str] = None,
    ) -> Iterable[GatewayConfigEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(wide.get_gateway_config_prefix(version))
        ):
            g_c = wide.parse_gateway_config_path(version, self.config.split_key_to_path(key))
            if not g_c:
                continue
            if (
                    (namespace is None or namespace == g_c.namespace_id)
                    and (protection is None or protection == g_c.protection)
                    and (purpose is None or purpose == g_c.purpose)
            ):
                yield g_c

    def get_service_color_template_entities(
            self,
            version: str,
            namespace: Optional[str] = None,
            service: Optional[str] = None,
            color: Optional[str] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[ServiceColorTemplateEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(wide.get_service_color_template_prefix(version))
        ):
            s_c = wide.parse_service_color_template_path(
                version, self.config.split_key_to_path(key),
            )
            if not s_c:
                continue
            if (
                    (namespace is None or namespace == s_c.namespace)
                    and (service is None or service == s_c.service)
                    and (color is None or color == s_c.color)
                    and (purpose is None or purpose == s_c.purpose)
            ):
                yield s_c

    def get_service_id_config_entities(
            self,
            version: str,
            namespace_id: Optional[str] = None,
            service_id: Optional[str] = None,
            service: Optional[str] = None,
            color: Optional[str] = None,
            purpose: Optional[str] = None,
    ) -> Iterable[ServiceIdConfigEntity]:
        for key, _ in self._list_entries(
                self.config.get_path(wide.get_service_id_config_prefix(version))
        ):
            s_c = wide.parse_service_id_config_path(version, self.config.split_key_to_path(key))
            if not s_c:
                debug('Skipped item {s}', s=key)
                continue
            if (
                    (namespace_id is None or namespace_id == s_c.namespace_id)
                    and (service_id is None or service_id == s_c.service_id)
                    and (service is None or service == s_c.service)
                    and (color is None or color == s_c.color)
                    and (purpose is None or purpose == s_c.purpose)
            ):
                yield s_c
            else:
                debug('Not match: {s}', s=s_c)

    def download(self, version: str, entity: Entity) -> str:
        path = self.config.get_path(wide.get_entity_path(version, entity))
        return self._download(path)

    # -----------------------------------------------------------------------
    # Write Actions

    def start_changes(self, activity: str) -> str:
        if activity not in SUPPORTED_ACTIVITIES:
            raise ValueError(
                'invalid activity {0}; valid values are {1}'.format(activity, SUPPORTED_ACTIVITIES)
            )
        version = ProcessingVersion(self.config, activity)
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
                path = self.config.get_path(wide.get_entity_path(final_version, entity))
                self._upload(path, data)
                uploaded_paths.append(path)
            self._upload(
                self.config.get_path(wide.get_version_reference_path(
                    activity_version.activity, final_version,
                )),
                final_version.encode('utf-8')
            )
        except Exception:
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
        for key, when in self._list_entries(
                self.config.get_path(wide.get_version_reference_prefix(activity))
        ):
            version = wide.parse_version_reference_path(
                activity, self.config.split_key_to_path(key),
            )
            if version:
                yield version, when

    def _clean_old_versions(
            self, activity: str,
            purge_older_than_days: int,
            do_not_remove_versions: Set[str],
    ) -> None:
        # This should remove any version older than (some old date), but always leave
        # the previously active version around, in case anything is actively pulling from it.
        # That is, delete all versions before date except for previously_active_version and
        # final_version.
        older_than = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(days=purge_older_than_days)
        )
        for version, when in self._get_versions(activity):
            if version not in do_not_remove_versions and when < older_than:
                note('Removing old activity {a} version {v}', a=activity, v=version)
                to_delete = [
                    d[0]
                    for d in self._list_entries(
                        self.config.get_path(wide.get_activity_prefix(version, activity))
                    )
                ]
                # don't forget the reference to this version!
                to_delete.append(
                    self.config.get_path(wide.get_version_reference_path(activity, version))
                )
                self._delete(to_delete)

    def _list_entries(self, path: str) -> Iterable[Tuple[str, datetime.datetime]]:
        debug("Listing entries under {p}", p=path)
        paginator = self.get_client().get_paginator('list_objects_v2')
        response_iterator = paginator.paginate(
            Bucket=self.config.bucket,
            EncodingType='url',
            Prefix=path,
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
        # Shouldn't be necessary due to the construction of the path argument...
        # this is defensive coding.
        while path[0] == '/':
            path = path[1:]
        print("Uploading {0}".format(path))
        inp = io.BytesIO(contents)
        self.get_client().upload_fileobj(inp, self.config.bucket, path)

    def _download(self, path: str) -> str:
        # Shouldn't be necessary due to the construction of the path argument...
        # this is defensive coding.
        while path[0] == '/':
            path = path[1:]
        out = io.BytesIO()
        self.get_client().download_fileobj(self.config.bucket, path, out)
        return out.getvalue().decode('utf-8')

    def _delete(self, keys: List[str]) -> None:
        if len(keys) <= 0:
            return
        if len(keys) > 1000:
            raise Exception("Cannot handle > 1000 paths right now.")
        self.get_client().delete_objects(
            Bucket=self.config.bucket,
            Delete={
                'Objects': [{'Key': p} for p in keys],
            }
        )
