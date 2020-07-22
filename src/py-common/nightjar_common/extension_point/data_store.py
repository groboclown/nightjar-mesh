
"""
Runs the data store extension point.
"""

from typing import Sequence, Literal, Dict, Any
import os
import json
import subprocess
from .run_cmd import run_with_backoff
from .exceptions import ExtensionPointRuntimeError, ExtensionPointTooManyRetries
from ..validation import (
    validate_commit_configuration_data_store,
    validate_commit_template_data_store,
    validate_fetched_configuration_data_store,
    validate_fetched_template_data_store,
)

Action = Literal["fetch", "commit"]
Activity = Literal["template", "configuration"]


class DataStoreRunner:
    """Manages the execution of the data store."""
    __slots__ = (
        '_last_version_template', '_last_version_configuration',
        '_executable', 'max_retry_count', 'max_retry_wait_seconds', '_tmp_dir',
    )

    def __init__(self, cmd: Sequence[str], temp_dir: str) -> None:
        self._last_version_template = ''
        self._last_version_configuration = ''
        self._executable = tuple(cmd)
        self.max_retry_count = 5
        self.max_retry_wait_seconds = 60.0
        self._tmp_dir = temp_dir

    def fetch_templates(self) -> Dict[str, Any]:
        """Fetch the template data."""
        downloaded = os.path.join(self._tmp_dir, 'fetch-templates-new.json')
        previous = os.path.join(self._tmp_dir, 'fetch-templates.json')
        data = self.fetch_from_data_store(
            downloaded, previous, "template", self._last_version_template,
        )
        validate_fetched_template_data_store(data)
        self._last_version_template = data['commit-version']
        return data

    def fetch_configurations(self) -> Dict[str, Any]:
        """Fetch the configuration data."""
        downloaded = os.path.join(self._tmp_dir, 'fetch-configurations-new.json')
        previous = os.path.join(self._tmp_dir, 'fetch-configurations.json')
        data = self.fetch_from_data_store(
            downloaded, previous, "configuration", self._last_version_configuration,
        )
        validate_fetched_configuration_data_store(data)
        self._last_version_configuration = data['commit-version']
        return data

    def commit_templates(self, data: Dict[str, Any]) -> None:
        """Upload the templates to the data store."""
        validate_commit_template_data_store(data)
        source_file = os.path.join(self._tmp_dir, 'commit-templates.json')
        with open(source_file, 'w') as f:
            json.dump(data, f)
        result = self.run_data_store(source_file, "commit", "template", '')
        if result == 31:
            raise ExtensionPointTooManyRetries('data store', 'commit templates')
        if result != 0:
            raise ExtensionPointRuntimeError('data store', 'commit templates', result)

    def commit_configurations(self, data: Dict[str, Any]) -> None:
        """Upload the templates to the data store."""
        validate_commit_configuration_data_store(data)
        source_file = os.path.join(self._tmp_dir, 'commit-configs.json')
        with open(source_file, 'w') as f:
            json.dump(data, f)
        result = self.run_data_store(source_file, "commit", "configuration", '')
        if result == 31:
            raise ExtensionPointTooManyRetries('data store', 'commit configurations')
        if result != 0:
            raise ExtensionPointRuntimeError('data store', 'commit configurations', result)

    def run_data_store_once(
            self, dest_file: str, action: Action, activity: Activity, last_version: str,
    ) -> int:
        """The most basic invocation of the data store."""
        result = subprocess.run(
            [
                *self._executable,
                '--activity=' + activity,
                '--action=' + action,
                '--previous-document-version=' + last_version,
                '--action-file=' + dest_file,
                '--api-version=1',
            ],
            check=False,
        )
        return result.returncode

    def fetch_from_data_store(
            self,
            dest_file: str, prev_file: str, activity: Activity, last_version: str,
    ) -> Dict[str, Any]:
        """Fetch data from the data store."""
        result = self.run_data_store(dest_file, "fetch", activity, last_version)
        if result == 30:
            if not os.path.isfile(prev_file):
                raise RuntimeError('data store requested reuse of non-existent old version')
            dest_file = prev_file
        elif result == 31:
            raise ExtensionPointTooManyRetries('data store', 'fetch ' + activity)
        elif result != 0:
            raise ExtensionPointRuntimeError('data store', 'fetch ' + activity, result)
        else:
            os.replace(dest_file, prev_file)
            dest_file = prev_file
        with open(dest_file, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        return data

    def run_data_store(
            self, dest_file: str, action: Action, activity: Activity, last_version: str,
    ) -> int:
        """Run the data store process, with correct retries.  The downloaded file is
        moved over to the previous file."""

        def run_it() -> int:
            return self.run_data_store_once(dest_file, action, activity, last_version)

        def should_retry(return_code: int) -> bool:
            return return_code == 31

        return run_with_backoff(
            run_it, should_retry, self.max_retry_count, self.max_retry_wait_seconds,
        )
