
"""
Configuration settings for the standalone.
"""

from typing import Dict, Sequence, Optional
import os
import sys
import argparse
import configparser
import tempfile
import shutil
import platform
from nightjar_common import log
from nightjar_common.extension_point.run_cmd import get_env_executable_cmd

ONE_TEMPLATE_DOCUMENT_TYPE = 'one-template'
ARG_DEFAULT_VALUE = 'default'

ENV__DATA_STORE_EXEC = 'DATA_STORE_EXEC'
ENV__DISCOVERY_MAP_EXEC = 'DISCOVERY_MAP_EXEC'


class Config:
    """Configuration settings"""
    __slots__ = (
        'data_store_exec',
        'document_type', 'filename',
        'category', 'namespace', 'service', 'color',
        'action', 'config_env', 'purpose', 'cache_dir',
        '_is_temp_dir',
    )

    def __init__(self, args: argparse.Namespace, env: Dict[str, str]) -> None:
        self.config_env = env
        self.data_store_exec = get_data_store_exec(env)
        self.document_type = args.document
        self.filename = args.local_file
        self.category = args.category
        self.purpose = args.purpose
        self.namespace = get_namespace(args.namespace)
        self.service = get_service(args.service)
        self.color = get_color(args.color)
        self.action = args.action
        cache_dir = env.get('CACHE_DIR', None)
        if cache_dir is None:
            self.cache_dir = tempfile.mkdtemp()
            self._is_temp_dir = True
        else:
            self.cache_dir = cache_dir
            self._is_temp_dir = False

    def __del__(self) -> None:
        if self._is_temp_dir and os.path.isdir(self.cache_dir):
            sys.stderr.write(
                "[nightjar-template-manager] Removing cache dir {d}.\n".format(d=self.cache_dir),
            )
            shutil.rmtree(self.cache_dir)


def get_namespace(orig: str) -> Optional[str]:
    """Get the actual namespace as used by templates."""
    return None if not orig or orig == ARG_DEFAULT_VALUE else orig


def get_service(orig: str) -> Optional[str]:
    """Get the actual service as used by templates."""
    return None if not orig or orig == ARG_DEFAULT_VALUE else orig


def get_color(orig: str) -> Optional[str]:
    """Get the actual color as used by templates."""
    return None if not orig or orig == ARG_DEFAULT_VALUE else orig


def create_configuration(vargs: Sequence[str]) -> Config:
    """Create and load the configuration."""
    log.EXECUTE_MODEL = 'nightjar-template-manager'

    parser = argparse.ArgumentParser(
        prog="template-manager",
        description="Tool for managing templates (and other documents) in the data store.",
    )
    parser.add_argument(
        '--config', '-C', action='store', default='local-data-store-profiles.ini', type=str,
        help="Configuration (.ini) file, each section defines a profile.",
    )
    parser.add_argument(
        '--profile', '-P', action='store', default=ARG_DEFAULT_VALUE, type=str,
        help=(
            "Profile section within the config file that sets up the properties used for "
            "the data store invocation."
        ),
    )
    parser.add_argument(
        '--document-type', '-D', action='store', default=ONE_TEMPLATE_DOCUMENT_TYPE,
        type=str, dest="document",
        help=(
            "The document type to store; the supported types are defined by the data store, but, "
            "at a minimum, `templates` and `discovery-map` are guaranteed to be supported.  "
            "The special value, `{0}` (the default value) is for managing a single "
            "template within the templates document, and requires additional arguments.".format(
                ONE_TEMPLATE_DOCUMENT_TYPE,
            )
        ),
    )
    parser.add_argument(
        '--file', '-f', action='store', type=str, dest="local_file",
        help="Local file to read or write.  Use `-` to send to stdout.",
    )
    parser.add_argument(
        '--category', '-y', action='store', type=str, default="",
        choices=['', 'gateway', 'service'],
        help="Template category to use (required for single templates)",
    )
    parser.add_argument(
        '--purpose', '-p', action='store', type=str, default="",
        help="The output file name, or `purpose` of the template.",
    )
    parser.add_argument(
        '--namespace', '-n', action='store', type=str, default=ARG_DEFAULT_VALUE,
        help="Namespace for the stored template.  Only used for single template management.",
    )
    parser.add_argument(
        '--service', '-s', action='store', type=str, default=ARG_DEFAULT_VALUE,
        help="Service name.  Only used for service category single template management.",
    )
    parser.add_argument(
        '--color', '-c', action='store', type=str, default=ARG_DEFAULT_VALUE,
        help="Color name.  Only used for service category single template management.",
    )
    parser.add_argument(
        'action',
        choices=['push', 'pull', 'list'],
        help=(
            "Action to perform on the document.  `push` commits the document into the data store, "
            "and `pull` extracts it from the data store."
        ),
    )

    args = parser.parse_args(vargs[1:])
    return Config(args, get_profile(args.config, args.profile))


def get_profile(config_filename: str, profile_name: str) -> Dict[str, str]:
    """Gets the profile from the ini file."""
    if not os.path.isfile(config_filename):
        log.warning('No such configuration file {name}', name=config_filename)
        return {}
    config = configparser.ConfigParser()
    config.read(config_filename)
    if profile_name not in config:
        log.warning(
            'No profile `{profile}` in configuration file {name}',
            name=config_filename,
            profile=profile_name,
        )
        return {}

    ret: Dict[str, str] = dict(os.environ)

    # ini files force the key name to be lower-cased,
    # and environment variables should be upper-cased.
    for key, value in config[profile_name].items():
        ret[key.upper()] = value
    return ret


def get_data_store_exec(env: Dict[str, str]) -> Sequence[str]:
    """This is a hack for allowing execution on Windows.
    The underlying process is written under the assumption that it's running on
    Unix.  However, for Windows, the command-line parsing is broken (known limitation
    with the library).  For people running on Windows, the best alternative is to run
    this manager through a container."""
    if platform.system() == 'Windows' and ENV__DATA_STORE_EXEC in env:
        line = env[ENV__DATA_STORE_EXEC]  # pragma no cover
        env[ENV__DATA_STORE_EXEC] = line.replace('\\', '\\\\')  # pragma no cover
    return get_env_executable_cmd(env, ENV__DATA_STORE_EXEC)
