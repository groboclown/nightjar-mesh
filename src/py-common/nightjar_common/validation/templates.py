# DO NOT MODIFY
# AUTO-GENERATED CODE.

# pylint: ignore

from typing import Dict, Any

VERSION = "2.14.4"
from ..fastjsonschema_replacement import JsonSchemaException


NoneType = type(None)

def validate_templates_schema_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, (dict)):
        raise JsonSchemaException("data must be object", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Template data definition.', 'type': 'object', 'required': ['schema-version', 'document-version', 'gateway-templates', 'service-templates'], 'properties': {'schema-version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'document-version': {'description': 'An opaque value indicating the version of this document.', 'type': 'string'}, 'gateway-templates': {'description': 'All templates for the gateways, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, 'service-templates': {'description': 'All templates for the services, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmp93fil6rp/templates-schema.yaml'}, rule='type')
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_len = len(data)
        if not all(prop in data for prop in ['schema-version', 'document-version', 'gateway-templates', 'service-templates']):
            raise JsonSchemaException("data must contain ['schema-version', 'document-version', 'gateway-templates', 'service-templates'] properties", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Template data definition.', 'type': 'object', 'required': ['schema-version', 'document-version', 'gateway-templates', 'service-templates'], 'properties': {'schema-version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'document-version': {'description': 'An opaque value indicating the version of this document.', 'type': 'string'}, 'gateway-templates': {'description': 'All templates for the gateways, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, 'service-templates': {'description': 'All templates for the services, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmp93fil6rp/templates-schema.yaml'}, rule='required')
        data_keys = set(data.keys())
        if "schema-version" in data_keys:
            data_keys.remove("schema-version")
            data__schemaversion = data["schema-version"]
            if data__schemaversion != "v1":
                raise JsonSchemaException("data.schema-version must be same as const definition", value=data__schemaversion, name="data.schema-version", definition={'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, rule='const')
        if "document-version" in data_keys:
            data_keys.remove("document-version")
            data__documentversion = data["document-version"]
            if not isinstance(data__documentversion, (str)):
                raise JsonSchemaException("data.document-version must be string", value=data__documentversion, name="data.document-version", definition={'description': 'An opaque value indicating the version of this document.', 'type': 'string'}, rule='type')
        if "gateway-templates" in data_keys:
            data_keys.remove("gateway-templates")
            data__gatewaytemplates = data["gateway-templates"]
            if not isinstance(data__gatewaytemplates, (list, tuple)):
                raise JsonSchemaException("data.gateway-templates must be array", value=data__gatewaytemplates, name="data.gateway-templates", definition={'description': 'All templates for the gateways, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, rule='type')
            data__gatewaytemplates_is_list = isinstance(data__gatewaytemplates, (list, tuple))
            if data__gatewaytemplates_is_list:
                data__gatewaytemplates_len = len(data__gatewaytemplates)
                for data__gatewaytemplates_x, data__gatewaytemplates_item in enumerate(data__gatewaytemplates):
                    if not isinstance(data__gatewaytemplates_item, (dict)):
                        raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+" must be object", value=data__gatewaytemplates_item, name=""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='type')
                    data__gatewaytemplates_item_is_dict = isinstance(data__gatewaytemplates_item, dict)
                    if data__gatewaytemplates_item_is_dict:
                        data__gatewaytemplates_item_len = len(data__gatewaytemplates_item)
                        if not all(prop in data__gatewaytemplates_item for prop in ['namespace', 'purpose', 'template']):
                            raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+" must contain ['namespace', 'purpose', 'template'] properties", value=data__gatewaytemplates_item, name=""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='required')
                        data__gatewaytemplates_item_keys = set(data__gatewaytemplates_item.keys())
                        if "namespace" in data__gatewaytemplates_item_keys:
                            data__gatewaytemplates_item_keys.remove("namespace")
                            data__gatewaytemplates_item__namespace = data__gatewaytemplates_item["namespace"]
                            if not isinstance(data__gatewaytemplates_item__namespace, (str, NoneType)):
                                raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}].namespace".format(**locals())+" must be string or null", value=data__gatewaytemplates_item__namespace, name=""+"data.gateway-templates[{data__gatewaytemplates_x}].namespace".format(**locals())+"", definition={'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, rule='type')
                        if "purpose" in data__gatewaytemplates_item_keys:
                            data__gatewaytemplates_item_keys.remove("purpose")
                            data__gatewaytemplates_item__purpose = data__gatewaytemplates_item["purpose"]
                            if not isinstance(data__gatewaytemplates_item__purpose, (str)):
                                raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}].purpose".format(**locals())+" must be string", value=data__gatewaytemplates_item__purpose, name=""+"data.gateway-templates[{data__gatewaytemplates_x}].purpose".format(**locals())+"", definition={'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, rule='type')
                        if "template" in data__gatewaytemplates_item_keys:
                            data__gatewaytemplates_item_keys.remove("template")
                            data__gatewaytemplates_item__template = data__gatewaytemplates_item["template"]
                            if not isinstance(data__gatewaytemplates_item__template, (str)):
                                raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}].template".format(**locals())+" must be string", value=data__gatewaytemplates_item__template, name=""+"data.gateway-templates[{data__gatewaytemplates_x}].template".format(**locals())+"", definition={'description': 'The template text.', 'type': 'string'}, rule='type')
        if "service-templates" in data_keys:
            data_keys.remove("service-templates")
            data__servicetemplates = data["service-templates"]
            if not isinstance(data__servicetemplates, (list, tuple)):
                raise JsonSchemaException("data.service-templates must be array", value=data__servicetemplates, name="data.service-templates", definition={'description': 'All templates for the services, along with descriptive metadata.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, rule='type')
            data__servicetemplates_is_list = isinstance(data__servicetemplates, (list, tuple))
            if data__servicetemplates_is_list:
                data__servicetemplates_len = len(data__servicetemplates)
                for data__servicetemplates_x, data__servicetemplates_item in enumerate(data__servicetemplates):
                    if not isinstance(data__servicetemplates_item, (dict)):
                        raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+" must be object", value=data__servicetemplates_item, name=""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='type')
                    data__servicetemplates_item_is_dict = isinstance(data__servicetemplates_item, dict)
                    if data__servicetemplates_item_is_dict:
                        data__servicetemplates_item_len = len(data__servicetemplates_item)
                        if not all(prop in data__servicetemplates_item for prop in ['namespace', 'service', 'color', 'purpose', 'template']):
                            raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+" must contain ['namespace', 'service', 'color', 'purpose', 'template'] properties", value=data__servicetemplates_item, name=""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='required')
                        data__servicetemplates_item_keys = set(data__servicetemplates_item.keys())
                        if "namespace" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("namespace")
                            data__servicetemplates_item__namespace = data__servicetemplates_item["namespace"]
                            if not isinstance(data__servicetemplates_item__namespace, (str, NoneType)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].namespace".format(**locals())+" must be string or null", value=data__servicetemplates_item__namespace, name=""+"data.service-templates[{data__servicetemplates_x}].namespace".format(**locals())+"", definition={'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, rule='type')
                        if "service" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("service")
                            data__servicetemplates_item__service = data__servicetemplates_item["service"]
                            if not isinstance(data__servicetemplates_item__service, (str, NoneType)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].service".format(**locals())+" must be string or null", value=data__servicetemplates_item__service, name=""+"data.service-templates[{data__servicetemplates_x}].service".format(**locals())+"", definition={'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, rule='type')
                        if "color" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("color")
                            data__servicetemplates_item__color = data__servicetemplates_item["color"]
                            if not isinstance(data__servicetemplates_item__color, (str, NoneType)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].color".format(**locals())+" must be string or null", value=data__servicetemplates_item__color, name=""+"data.service-templates[{data__servicetemplates_x}].color".format(**locals())+"", definition={'description': 'Color of this template, or `null` if this is the default service color template.\n', 'type': ['string', 'null']}, rule='type')
                        if "purpose" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("purpose")
                            data__servicetemplates_item__purpose = data__servicetemplates_item["purpose"]
                            if not isinstance(data__servicetemplates_item__purpose, (str)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].purpose".format(**locals())+" must be string", value=data__servicetemplates_item__purpose, name=""+"data.service-templates[{data__servicetemplates_x}].purpose".format(**locals())+"", definition={'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace/service/color.\n', 'type': 'string'}, rule='type')
                        if "template" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("template")
                            data__servicetemplates_item__template = data__servicetemplates_item["template"]
                            if not isinstance(data__servicetemplates_item__template, (str)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].template".format(**locals())+" must be string", value=data__servicetemplates_item__template, name=""+"data.service-templates[{data__servicetemplates_x}].template".format(**locals())+"", definition={'description': 'The template text.', 'type': 'string'}, rule='type')
    return data