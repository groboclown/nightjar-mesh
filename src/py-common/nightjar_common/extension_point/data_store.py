
"""
Runs the data store extension point.
"""

from typing import Sequence, Literal, Dict, Any, cast
import os
import subprocess
from .cached_document import CachedDocument
from .run_cmd import run_with_backoff
from ..validation import validate_discovery_map, validate_templates

Action = Literal["fetch", "commit"]
DocumentName = Literal["templates", "discovery-map"]
TEMPLATES_DOCUMENT = cast(DocumentName, 'templates')
DISCOVERY_MAP_DOCUMENT = cast(DocumentName, 'discovery-map')
VALID_DOCUMENT_TYPES = (TEMPLATES_DOCUMENT, DISCOVERY_MAP_DOCUMENT,)


class DataStoreRunner:
    """Manages the execution of the data store."""
    __slots__ = (
        '_cached_documents',
        '_executable', 'max_retry_count', 'max_retry_wait_seconds',
    )

    def __init__(self, cmd: Sequence[str], temp_dir: str) -> None:
        self._cached_documents = {
            TEMPLATES_DOCUMENT: CachedDocument(
                'data_store',
                TEMPLATES_DOCUMENT,
                os.path.join(temp_dir, 'templates-cached.json'),
                os.path.join(temp_dir, 'templates-new.json'),
                os.path.join(temp_dir, 'templates-pending.json'),
                validate_templates,
                True,
            ),
            DISCOVERY_MAP_DOCUMENT: CachedDocument(
                'data_store',
                DISCOVERY_MAP_DOCUMENT,
                os.path.join(temp_dir, 'discovery-map-cached.json'),
                os.path.join(temp_dir, 'discovery-map-new.json'),
                os.path.join(temp_dir, 'discovery-map-pending.json'),
                validate_discovery_map,
                True,
            ),
        }
        self._executable = tuple(cmd)
        self.max_retry_count = 5
        self.max_retry_wait_seconds = 60.0

    def fetch_document(self, name: DocumentName) -> Dict[str, Any]:
        """Fetch the document data."""
        result_code = self.run_data_store(
            self._cached_documents[name].update_file,
            'fetch',
            name,
            self._cached_documents[name].last_version,
        )
        return self._cached_documents[name].after_fetch(result_code)

    def commit_document(self, name: DocumentName, data: Dict[str, Any]) -> None:
        """Upload the templates to the data store."""
        self._cached_documents[name].before_commit(data)
        result = self.run_data_store(
            self._cached_documents[name].commit_file,
            "commit", name, '',
        )
        self._cached_documents[name].after_commit(result)

    def run_data_store_once(
            self,
            dest_file: str,
            action: Action, document: DocumentName, last_version: str,
    ) -> int:
        """The most basic invocation of the data store."""
        result = subprocess.run(
            [
                *self._executable,
                '--document=' + document,
                '--action=' + action,
                '--previous-document-version=' + last_version,
                '--action-file=' + dest_file,
                '--api-version=1',
            ],
            check=False,
        )
        return result.returncode

    def run_data_store(
            self,
            dest_file: str,
            action: Action, document: DocumentName, last_version: str,
    ) -> int:
        """Run the data store process, with correct retries.  The downloaded file is
        moved over to the previous file."""

        def run_it() -> int:
            return self.run_data_store_once(
                dest_file, action, document, last_version,
            )

        return run_with_backoff(
            run_it, self.max_retry_count, self.max_retry_wait_seconds,
        )
