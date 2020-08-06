
"""
Main program.
"""

from typing import Sequence
from nightjar_common import log
from . import data_store_manage
from .config import create_configuration, ONE_TEMPLATE_DOCUMENT_TYPE


def main(args: Sequence[str]) -> int:
    """Main program."""
    config = create_configuration(args)
    if config.document_type == ONE_TEMPLATE_DOCUMENT_TYPE:
        if config.action == 'push':
            return data_store_manage.push_template(config)
        if config.action == 'pull':
            return data_store_manage.pull_template(config)
        if config.action == 'list':
            return data_store_manage.list_template(config)
    if config.action == 'push':
        return data_store_manage.push_file(config)
    if config.action == 'pull':
        return data_store_manage.pull_file(config)

    log.warning('Unknown action `{action}` for this context.', action=config.action)
    return 1
