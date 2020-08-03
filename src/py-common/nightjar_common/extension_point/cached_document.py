
"""
Runs the data store extension point.
"""

from typing import Dict, Optional, Callable, Any
import os
import json
from .errors import ExtensionPointTooManyRetries, ExtensionPointRuntimeError
from ..log import warning


DOCUMENT_VERSION_KEY = 'document-version'


class CachedDocument:
    """Manages a document which can be cached and versioned.  The cached versions are
    stored on disk."""
    __slots__ = (
        'last_version', 'cached_file', 'update_file',
        'validator', 'commit_file', 'document_name',
        'extension_point_name',
    )

    def __init__(
            self, extension_point_name: str, document_name: str,
            cached_file: str, update_file: str, commit_file: str,
            validator: Callable[[Dict[str, Any]], Dict[str, Any]],
            clean: bool,
    ) -> None:
        self.last_version = ''
        self.extension_point_name = extension_point_name
        self.document_name = document_name
        self.validator = validator
        self.cached_file = os.path.abspath(cached_file)
        self.update_file = os.path.abspath(update_file)
        self.commit_file = os.path.abspath(commit_file)
        os.makedirs(os.path.dirname(self.cached_file), exist_ok=True)
        if clean:
            for name in (self.cached_file, self.update_file, self.commit_file):
                if os.path.isfile(name):
                    os.unlink(name)

    def after_fetch(self, result_code: int) -> Dict[str, Any]:
        """
        On cache update calls, the call included an output file, and if the
        update call returns code 30, then the existing cached version is used.
        If the return code is 0, then the cached version is replaced with the update
        file.  The update_file will be removed after this call.

        The document MUST have the `document-version` field equal to a string.

        Either the cached version is returned or the updated file.

        @param result_code:
        @return:
        """
        # Do not raise exceptions on fetch errors unless there is no cache.

        if os.path.isfile(self.update_file):
            if result_code == 0:
                # The file is maybe valid.
                value: Optional[Dict[str, Any]] = None
                err: Optional[Exception] = None
                try:
                    with open(self.update_file, 'r') as f:
                        ret = json.load(f)
                    if isinstance(ret, dict) and DOCUMENT_VERSION_KEY in ret:
                        value = self.validator(ret)
                except ValueError as value_error:
                    err = value_error
                if value is None:
                    warning(
                        'Updated {name} file {file} is not valid: {err}',
                        name=self.document_name,
                        file=self.update_file,
                        err=err or 'not a JSON dictionary',
                    )
                    # Fall through to use the cached file instead.
                else:
                    # Use the updated file.  Move the file, which is atomic.
                    os.replace(self.update_file, self.cached_file)
                    self.last_version = str(ret[DOCUMENT_VERSION_KEY])
                    return value
            else:
                # Do not use the updated file.
                os.unlink(self.update_file)

        # Use the cached file instead.
        if not os.path.isfile(self.cached_file):
            self.check_run_error(result_code, 'fetch')
            raise ExtensionPointRuntimeError(self.extension_point_name, 'create file', 0)

        # The cached file is already valid.
        with open(self.cached_file, 'r') as f:
            ret = json.load(f)
        assert isinstance(ret, dict)
        return ret

    def before_commit(self, data: Dict[str, Any]) -> None:
        """Called before the commit happens.  The document-version must be the new version."""
        data = self.validator(data)
        # The commit operation can perform any kind of operation on this
        # commit version.
        with open(self.commit_file, 'w') as f:
            json.dump(data, f)

    def after_commit(self, result_code: int) -> None:
        """Called after committing the commit file.  This assumes the file is valid."""
        self.check_run_error(result_code, 'commit')
        # If the commit was successful, then clear our cache.
        # Any fetch will require pulling the new version, because the version number
        # and document contents may have been altered on commit.
        self.last_version = ''
        if os.path.isfile(self.cached_file):
            os.unlink(self.cached_file)

    def check_run_error(self, result_code: int, action: str) -> None:
        """Check for an error code."""
        if result_code == 31:
            raise ExtensionPointTooManyRetries(
                self.extension_point_name, '{0} {1}'.format(action, self.document_name),
            )
        if result_code != 0:
            raise ExtensionPointRuntimeError(
                self.extension_point_name, '{0} {1}'.format(action, self.document_name),
                result_code,
            )
