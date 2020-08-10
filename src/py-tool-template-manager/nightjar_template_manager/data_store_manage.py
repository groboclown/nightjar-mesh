
"""Manage the basic data store process."""

from typing import Dict, Any, Optional, cast
import os
import sys
import tempfile
import shutil
import json
from nightjar_common import log
from nightjar_common.extension_point.errors import ExtensionPointTooManyRetries
from nightjar_common.extension_point.data_store import DataStoreRunner, DocumentName
from .config import Config

TEMPLATES_DOCUMENT = 'templates'
DISPLAY_DEFAULT_TEXT = '<default>'


def push_file(config: Config) -> int:
    """Push the source file to the data store."""
    if config.filename == '-':
        data = json.load(sys.stdin)
    elif not config.filename or not os.path.isfile(config.filename):
        log.warning('No such local file `{file}`', file=config.filename)
        return 9
    else:
        with open(config.filename, 'r') as f:
            data = json.load(f)
    assert isinstance(data, dict)
    return push_document(config, config.document_type, data)


def pull_file(config: Config) -> int:
    """Pull the document into the file."""
    data = pull_document(config, config.document_type)
    if not data:
        log.warning("No existing document.  Not pulling anything")
        return 1
    if config.filename == '-':
        print(json.dumps(data))
    else:
        with open(config.filename, 'w') as f:
            json.dump(data, f)
    return 0


def list_template(config: Config) -> int:
    """List the templates."""
    templates = pull_document(config, TEMPLATES_DOCUMENT)
    if not templates:
        return 0
    output = ""
    if config.category != 'service':
        output += "Gateway-Templates:\n"
        for gateway in templates['gateway-templates']:
            output += "  - namespace: {0}\n".format(gateway['namespace'] or DISPLAY_DEFAULT_TEXT)
            output += "    purpose:   {0}\n".format(gateway['purpose'])
    if config.category != 'gateway':
        output += "Service-Templates:\n"
        for service in templates['service-templates']:
            output += "  - namespace: {0}\n".format(service['namespace'] or DISPLAY_DEFAULT_TEXT)
            output += "    service:   {0}\n".format(service['service'] or DISPLAY_DEFAULT_TEXT)
            output += "    color:     {0}\n".format(service['color'] or DISPLAY_DEFAULT_TEXT)
            output += "    purpose:   {0}\n".format(service['purpose'])
    if not config.filename or config.filename == '-':
        print(output)
    else:
        with open(config.filename, 'w') as f:
            f.write(output)
    return 0


def push_template(config: Config) -> int:
    """Push a piece of the template into the templates document."""
    if not config.purpose:
        log.warning('When pushing a template, the `purpose` argument is required.')
        return 3
    if config.filename == '-':
        source_data = sys.stdin.read()
    elif not config.filename or not os.path.isfile(config.filename):
        log.warning('No such local file `{file}`', file=config.filename)
        return 4
    else:
        with open(config.filename, 'r') as f:
            source_data = f.read()
    log.debug("Pulling current templates")
    templates = pull_document(config, TEMPLATES_DOCUMENT) or create_initial_templates_document()
    if config.category == 'gateway':
        update_gateway_template(templates, source_data, config.namespace, config.purpose)
    elif config.category == 'service':
        update_service_template(
            templates, source_data, config.namespace, config.service, config.color, config.purpose,
        )
    else:
        log.warning('Unknown or unset category `{cat}`', cat=config.category)
        return 5
    push_document(config, TEMPLATES_DOCUMENT, templates)
    return 0


def pull_template(config: Config) -> int:
    """Pull a single template from the templates document."""
    if not config.purpose:
        log.warning('When pushing a template, the `purpose` argument is required.')
        return 6
    templates = pull_document(config, TEMPLATES_DOCUMENT) or create_initial_templates_document()
    if config.category == 'gateway':
        data = extract_gateway_template(templates, config.namespace, config.purpose)
    elif config.category == 'service':
        data = extract_service_template(
            templates, config.namespace, config.service, config.color, config.purpose,
        )
    else:
        log.warning('Unknown category {cat}', cat=config.category)
        return 7
    if data is None:
        log.warning('No such template inside templates document.')
        return 8
    if config.filename == '-':
        print(data)
    else:
        with open(config.filename, 'w') as f:
            f.write(data)
    return 0


def update_gateway_template(
        templates: Dict[str, Any], source_data: str,
        namespace: Optional[str], purpose: str,
) -> None:
    """Add or replace the gateway template for the namespace + purpose."""
    gateway_templates = templates['gateway-templates']
    assert isinstance(gateway_templates, list)
    for gateway_template in gateway_templates:
        if (
                gateway_template.get('namespace') == namespace
                and gateway_template.get('purpose') == purpose
        ):
            gateway_template['template'] = source_data
            return
    gateway_templates.append({
        'namespace': namespace,
        'purpose': purpose,
        'template': source_data,
    })


def update_service_template(
        templates: Dict[str, Any], source_data: str,
        namespace: Optional[str], service: Optional[str], color: Optional[str], purpose: str,
) -> None:
    """Update or add the service template."""
    service_templates = templates['service-templates']
    assert isinstance(service_templates, list)
    for service_template in service_templates:
        if (
                service_template.get('namespace') == namespace
                and service_template.get('service') == service
                and service_template.get('color') == color
                and service_template.get('purpose') == purpose
        ):
            service_template['template'] = source_data
            return
    service_templates.append({
        'namespace': namespace,
        'service': service,
        'color': color,
        'purpose': purpose,
        'template': source_data,
    })


def extract_gateway_template(
        templates: Dict[str, Any], namespace: Optional[str], purpose: str,
) -> Optional[str]:
    """Extract the template, or None if it does not exist."""
    for gateway_template in templates['gateway-templates']:
        if (
                gateway_template['namespace'] == namespace
                and gateway_template['purpose'] == purpose
        ):
            ret = gateway_template['template']
            assert isinstance(ret, str)
            return ret
    return None


def extract_service_template(
        templates: Dict[str, Any],
        namespace: Optional[str], service: Optional[str], color: Optional[str], purpose: str,
) -> Optional[str]:
    """Extract the template, or None if it does not exist."""
    for service_template in templates['service-templates']:
        if (
                service_template['namespace'] == namespace
                and service_template['service'] == service
                and service_template['color'] == color
                and service_template['purpose'] == purpose
        ):
            ret = service_template['template']
            assert isinstance(ret, str)
            return ret
    return None


def push_document(config: Config, document_type: str, data: Dict[str, Any]) -> int:
    """Push the document contents to the data store"""
    temp_dir = tempfile.mkdtemp()
    try:
        runner = DataStoreRunner(config.data_store_exec, temp_dir, config.config_env)
        runner.commit_document(cast(DocumentName, document_type), data)
        return 0
    finally:
        shutil.rmtree(temp_dir)


def pull_document(config: Config, document_type: str) -> Optional[Dict[str, Any]]:
    """Pull the document."""
    temp_dir = tempfile.mkdtemp()
    try:
        runner = DataStoreRunner(config.data_store_exec, temp_dir, config.config_env)
        runner.max_retry_count = 1
        return runner.fetch_document(cast(DocumentName, document_type))
    except ExtensionPointTooManyRetries:
        log.warning("No existing document.")
        return None
    finally:
        shutil.rmtree(temp_dir)


def create_initial_templates_document() -> Dict[str, Any]:
    """Create the empty templates document, which is necessary if this is
    to initialize the data store."""
    return {
        'schema-version': 'v1', 'document-version': '',
        'gateway-templates': [], 'service-templates': [],
    }
