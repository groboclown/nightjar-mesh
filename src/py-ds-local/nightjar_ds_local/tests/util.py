
"""
Test utilities
"""

from typing import Dict, Any
import os
import tempfile
import shutil
import json
from ..config import Config, ENV_NAME__LOCAL_TEMPLATE_FILE, ENV_NAME__LOCAL_CONFIGURATION_FILE


class Local:
    """Local data helper."""

    def __init__(self) -> None:
        self._orig_env = dict(os.environ)
        self.temp_dir = tempfile.mkdtemp()
        self.template_file = os.path.join(self.temp_dir, 'template.json')
        self.config_file = os.path.join(self.temp_dir, 'config.json')
        self.action_file = os.path.join(self.temp_dir, 'action.json')
        self.config = Config({
            ENV_NAME__LOCAL_TEMPLATE_FILE: self.template_file,
            ENV_NAME__LOCAL_CONFIGURATION_FILE: self.config_file,
        })

    def tear_down(self) -> None:
        """On test tearDown."""
        os.environ.clear()
        os.environ.update(self._orig_env)
        shutil.rmtree(self.temp_dir)

    def write_template(self, data: Dict[str, Any]) -> None:
        """Create the template file with the given data."""
        with open(self.template_file, 'w') as f:
            json.dump(data, f)

    def read_template(self) -> Dict[str, Any]:
        """Read the template data."""
        return Local._read_file(self.template_file)

    def does_template_exist(self) -> bool:
        """Does the template file exist?"""
        return os.path.isfile(self.template_file)

    def write_config(self, data: Dict[str, Any]) -> None:
        """Create the config file with the given data."""
        with open(self.config_file, 'w') as f:
            json.dump(data, f)

    def read_config(self) -> Dict[str, Any]:
        """Read the config data."""
        return Local._read_file(self.config_file)

    def does_config_exist(self) -> bool:
        """Does the config file exist?"""
        return os.path.isfile(self.config_file)

    def write_action_file(self, data: Dict[str, Any]) -> None:
        """Create the action file with the given data."""
        with open(self.action_file, 'w') as f:
            json.dump(data, f)

    def read_action_file(self) -> Dict[str, Any]:
        """Read the action file."""
        return Local._read_file(self.action_file)

    def does_action_file_exist(self) -> bool:
        """Does the action file exist?"""
        return os.path.isfile(self.action_file)

    @staticmethod
    def _read_file(filename: str) -> Dict[str, Any]:
        with open(filename, 'r') as f:
            data = json.load(f)
        assert isinstance(data, dict)
        return data
