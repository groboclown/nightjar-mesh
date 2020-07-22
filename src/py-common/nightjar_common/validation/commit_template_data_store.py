# DO NOT MODIFY
# AUTO-GENERATED CODE.

# pylint: ignore

from typing import Dict, Any

VERSION = "2.14.4"
from ..fastjsonschema_replacement import JsonSchemaException


NoneType = type(None)

def validate_commit_template_data_store_schema_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, (dict)):
        raise JsonSchemaException("data must be object", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Entry data committed into the data store.', 'type': 'object', 'required': ['version', 'activity', 'gateway-templates', 'service-templates'], 'properties': {'version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'activity': {'description': 'The activity associated with the entries.  Must be "template".', 'const': 'template'}, 'gateway-templates': {'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'protection': {'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, 'service-templates': {'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmpkhgdcc97/commit-template-data-store-schema.yaml'}, rule='type')
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_len = len(data)
        if not all(prop in data for prop in ['version', 'activity', 'gateway-templates', 'service-templates']):
            raise JsonSchemaException("data must contain ['version', 'activity', 'gateway-templates', 'service-templates'] properties", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Entry data committed into the data store.', 'type': 'object', 'required': ['version', 'activity', 'gateway-templates', 'service-templates'], 'properties': {'version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'activity': {'description': 'The activity associated with the entries.  Must be "template".', 'const': 'template'}, 'gateway-templates': {'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'protection': {'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, 'service-templates': {'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmpkhgdcc97/commit-template-data-store-schema.yaml'}, rule='required')
        data_keys = set(data.keys())
        if "version" in data_keys:
            data_keys.remove("version")
            data__version = data["version"]
            if data__version != "v1":
                raise JsonSchemaException("data.version must be same as const definition", value=data__version, name="data.version", definition={'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, rule='const')
        if "activity" in data_keys:
            data_keys.remove("activity")
            data__activity = data["activity"]
            if data__activity != "template":
                raise JsonSchemaException("data.activity must be same as const definition", value=data__activity, name="data.activity", definition={'description': 'The activity associated with the entries.  Must be "template".', 'const': 'template'}, rule='const')
        if "gateway-templates" in data_keys:
            data_keys.remove("gateway-templates")
            data__gatewaytemplates = data["gateway-templates"]
            if not isinstance(data__gatewaytemplates, (list, tuple)):
                raise JsonSchemaException("data.gateway-templates must be array", value=data__gatewaytemplates, name="data.gateway-templates", definition={'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'protection': {'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, rule='type')
            data__gatewaytemplates_is_list = isinstance(data__gatewaytemplates, (list, tuple))
            if data__gatewaytemplates_is_list:
                data__gatewaytemplates_len = len(data__gatewaytemplates)
                for data__gatewaytemplates_x, data__gatewaytemplates_item in enumerate(data__gatewaytemplates):
                    if not isinstance(data__gatewaytemplates_item, (dict)):
                        raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+" must be object", value=data__gatewaytemplates_item, name=""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'protection': {'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='type')
                    data__gatewaytemplates_item_is_dict = isinstance(data__gatewaytemplates_item, dict)
                    if data__gatewaytemplates_item_is_dict:
                        data__gatewaytemplates_item_len = len(data__gatewaytemplates_item)
                        if not all(prop in data__gatewaytemplates_item for prop in ['namespace', 'protection', 'purpose', 'template']):
                            raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+" must contain ['namespace', 'protection', 'purpose', 'template'] properties", value=data__gatewaytemplates_item, name=""+"data.gateway-templates[{data__gatewaytemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'protection': {'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='required')
                        data__gatewaytemplates_item_keys = set(data__gatewaytemplates_item.keys())
                        if "namespace" in data__gatewaytemplates_item_keys:
                            data__gatewaytemplates_item_keys.remove("namespace")
                            data__gatewaytemplates_item__namespace = data__gatewaytemplates_item["namespace"]
                            if not isinstance(data__gatewaytemplates_item__namespace, (str, NoneType)):
                                raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}].namespace".format(**locals())+" must be string or null", value=data__gatewaytemplates_item__namespace, name=""+"data.gateway-templates[{data__gatewaytemplates_x}].namespace".format(**locals())+"", definition={'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, rule='type')
                        if "protection" in data__gatewaytemplates_item_keys:
                            data__gatewaytemplates_item_keys.remove("protection")
                            data__gatewaytemplates_item__protection = data__gatewaytemplates_item["protection"]
                            if not isinstance(data__gatewaytemplates_item__protection, (str, NoneType)):
                                raise JsonSchemaException(""+"data.gateway-templates[{data__gatewaytemplates_x}].protection".format(**locals())+" must be string or null", value=data__gatewaytemplates_item__protection, name=""+"data.gateway-templates[{data__gatewaytemplates_x}].protection".format(**locals())+"", definition={'description': 'Protection for this namespace. `null` means default protection level.', 'type': ['string', 'null']}, rule='type')
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
                raise JsonSchemaException("data.service-templates must be array", value=data__servicetemplates, name="data.service-templates", definition={'description': 'Template values comitted.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}}, rule='type')
            data__servicetemplates_is_list = isinstance(data__servicetemplates, (list, tuple))
            if data__servicetemplates_is_list:
                data__servicetemplates_len = len(data__servicetemplates)
                for data__servicetemplates_x, data__servicetemplates_item in enumerate(data__servicetemplates):
                    if not isinstance(data__servicetemplates_item, (dict)):
                        raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+" must be object", value=data__servicetemplates_item, name=""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='type')
                    data__servicetemplates_item_is_dict = isinstance(data__servicetemplates_item, dict)
                    if data__servicetemplates_item_is_dict:
                        data__servicetemplates_item_len = len(data__servicetemplates_item)
                        if not all(prop in data__servicetemplates_item for prop in ['namespace', 'service', 'color', 'purpose', 'template']):
                            raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+" must contain ['namespace', 'service', 'color', 'purpose', 'template'] properties", value=data__servicetemplates_item, name=""+"data.service-templates[{data__servicetemplates_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'template'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'service': {'description': 'Service of this template, or `null` if this is the default service template.', 'type': ['string', 'null']}, 'color': {'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'template': {'description': 'The template text.', 'type': 'string'}}}, rule='required')
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
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].color".format(**locals())+" must be string or null", value=data__servicetemplates_item__color, name=""+"data.service-templates[{data__servicetemplates_x}].color".format(**locals())+"", definition={'description': 'Color of this template, or `null` if this is the default service color template.  Note that if `service` is "null", then this must also be "null".\n', 'type': ['string', 'null']}, rule='type')
                        if "purpose" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("purpose")
                            data__servicetemplates_item__purpose = data__servicetemplates_item["purpose"]
                            if not isinstance(data__servicetemplates_item__purpose, (str)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].purpose".format(**locals())+" must be string", value=data__servicetemplates_item__purpose, name=""+"data.service-templates[{data__servicetemplates_x}].purpose".format(**locals())+"", definition={'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, rule='type')
                        if "template" in data__servicetemplates_item_keys:
                            data__servicetemplates_item_keys.remove("template")
                            data__servicetemplates_item__template = data__servicetemplates_item["template"]
                            if not isinstance(data__servicetemplates_item__template, (str)):
                                raise JsonSchemaException(""+"data.service-templates[{data__servicetemplates_x}].template".format(**locals())+" must be string", value=data__servicetemplates_item__template, name=""+"data.service-templates[{data__servicetemplates_x}].template".format(**locals())+"", definition={'description': 'The template text.', 'type': 'string'}, rule='type')
    return data