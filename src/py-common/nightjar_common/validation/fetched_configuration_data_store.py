# DO NOT MODIFY
# AUTO-GENERATED CODE.

# pylint: ignore

from typing import Dict, Any

VERSION = "2.14.4"
from ..fastjsonschema_replacement import JsonSchemaException


NoneType = type(None)

def validate_fetched_configuration_data_store_schema_yaml(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, (dict)):
        raise JsonSchemaException("data must be object", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Entry data fetched from the data store.', 'type': 'object', 'required': ['version', 'commit-version', 'activity', 'gateway-configurations', 'service-configurations'], 'properties': {'version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'commit-version': {'description': 'Opaque ID for the commit version.  Allows for atomic commits on multiple data storage types.', 'type': 'string'}, 'activity': {'description': 'The activity associated with the entries.  Must be "configuration".', 'const': 'configuration'}, 'gateway-configurations': {'description': 'Gateway configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}, 'service-configurations': {'description': 'Service configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmpg7y5z_1m/fetched-configuration-data-store-schema.yaml'}, rule='type')
    data_is_dict = isinstance(data, dict)
    if data_is_dict:
        data_len = len(data)
        if not all(prop in data for prop in ['version', 'commit-version', 'activity', 'gateway-configurations', 'service-configurations']):
            raise JsonSchemaException("data must contain ['version', 'commit-version', 'activity', 'gateway-configurations', 'service-configurations'] properties", value=data, name="data", definition={'$schema': 'https://json-schema.org/draft-07/schema', 'description': 'Entry data fetched from the data store.', 'type': 'object', 'required': ['version', 'commit-version', 'activity', 'gateway-configurations', 'service-configurations'], 'properties': {'version': {'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, 'commit-version': {'description': 'Opaque ID for the commit version.  Allows for atomic commits on multiple data storage types.', 'type': 'string'}, 'activity': {'description': 'The activity associated with the entries.  Must be "configuration".', 'const': 'configuration'}, 'gateway-configurations': {'description': 'Gateway configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}, 'service-configurations': {'description': 'Service configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}}, '$id': 'file:/tmp/tmpg7y5z_1m/fetched-configuration-data-store-schema.yaml'}, rule='required')
        data_keys = set(data.keys())
        if "version" in data_keys:
            data_keys.remove("version")
            data__version = data["version"]
            if data__version != "v1":
                raise JsonSchemaException("data.version must be same as const definition", value=data__version, name="data.version", definition={'description': 'Version of this document\'s schema.  The value must be the string value "v1".', 'const': 'v1'}, rule='const')
        if "commit-version" in data_keys:
            data_keys.remove("commit-version")
            data__commitversion = data["commit-version"]
            if not isinstance(data__commitversion, (str)):
                raise JsonSchemaException("data.commit-version must be string", value=data__commitversion, name="data.commit-version", definition={'description': 'Opaque ID for the commit version.  Allows for atomic commits on multiple data storage types.', 'type': 'string'}, rule='type')
        if "activity" in data_keys:
            data_keys.remove("activity")
            data__activity = data["activity"]
            if data__activity != "configuration":
                raise JsonSchemaException("data.activity must be same as const definition", value=data__activity, name="data.activity", definition={'description': 'The activity associated with the entries.  Must be "configuration".', 'const': 'configuration'}, rule='const')
        if "gateway-configurations" in data_keys:
            data_keys.remove("gateway-configurations")
            data__gatewayconfigurations = data["gateway-configurations"]
            if not isinstance(data__gatewayconfigurations, (list, tuple)):
                raise JsonSchemaException("data.gateway-configurations must be array", value=data__gatewayconfigurations, name="data.gateway-configurations", definition={'description': 'Gateway configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}, rule='type')
            data__gatewayconfigurations_is_list = isinstance(data__gatewayconfigurations, (list, tuple))
            if data__gatewayconfigurations_is_list:
                data__gatewayconfigurations_len = len(data__gatewayconfigurations)
                for data__gatewayconfigurations_x, data__gatewayconfigurations_item in enumerate(data__gatewayconfigurations):
                    if not isinstance(data__gatewayconfigurations_item, (dict)):
                        raise JsonSchemaException(""+"data.gateway-configurations[{data__gatewayconfigurations_x}]".format(**locals())+" must be object", value=data__gatewayconfigurations_item, name=""+"data.gateway-configurations[{data__gatewayconfigurations_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}, rule='type')
                    data__gatewayconfigurations_item_is_dict = isinstance(data__gatewayconfigurations_item, dict)
                    if data__gatewayconfigurations_item_is_dict:
                        data__gatewayconfigurations_item_len = len(data__gatewayconfigurations_item)
                        if not all(prop in data__gatewayconfigurations_item for prop in ['namespace', 'protection', 'purpose', 'configuration']):
                            raise JsonSchemaException(""+"data.gateway-configurations[{data__gatewayconfigurations_x}]".format(**locals())+" must contain ['namespace', 'protection', 'purpose', 'configuration'] properties", value=data__gatewayconfigurations_item, name=""+"data.gateway-configurations[{data__gatewayconfigurations_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'protection', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}, rule='required')
                        data__gatewayconfigurations_item_keys = set(data__gatewayconfigurations_item.keys())
                        if "namespace" in data__gatewayconfigurations_item_keys:
                            data__gatewayconfigurations_item_keys.remove("namespace")
                            data__gatewayconfigurations_item__namespace = data__gatewayconfigurations_item["namespace"]
                            if not isinstance(data__gatewayconfigurations_item__namespace, (str, NoneType)):
                                raise JsonSchemaException(""+"data.gateway-configurations[{data__gatewayconfigurations_x}].namespace".format(**locals())+" must be string or null", value=data__gatewayconfigurations_item__namespace, name=""+"data.gateway-configurations[{data__gatewayconfigurations_x}].namespace".format(**locals())+"", definition={'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, rule='type')
                        if "purpose" in data__gatewayconfigurations_item_keys:
                            data__gatewayconfigurations_item_keys.remove("purpose")
                            data__gatewayconfigurations_item__purpose = data__gatewayconfigurations_item["purpose"]
                            if not isinstance(data__gatewayconfigurations_item__purpose, (str)):
                                raise JsonSchemaException(""+"data.gateway-configurations[{data__gatewayconfigurations_x}].purpose".format(**locals())+" must be string", value=data__gatewayconfigurations_item__purpose, name=""+"data.gateway-configurations[{data__gatewayconfigurations_x}].purpose".format(**locals())+"", definition={'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, rule='type')
                        if "configuration" in data__gatewayconfigurations_item_keys:
                            data__gatewayconfigurations_item_keys.remove("configuration")
                            data__gatewayconfigurations_item__configuration = data__gatewayconfigurations_item["configuration"]
                            if not isinstance(data__gatewayconfigurations_item__configuration, (str)):
                                raise JsonSchemaException(""+"data.gateway-configurations[{data__gatewayconfigurations_x}].configuration".format(**locals())+" must be string", value=data__gatewayconfigurations_item__configuration, name=""+"data.gateway-configurations[{data__gatewayconfigurations_x}].configuration".format(**locals())+"", definition={'description': 'The configured text.', 'type': 'string'}, rule='type')
        if "service-configurations" in data_keys:
            data_keys.remove("service-configurations")
            data__serviceconfigurations = data["service-configurations"]
            if not isinstance(data__serviceconfigurations, (list, tuple)):
                raise JsonSchemaException("data.service-configurations must be array", value=data__serviceconfigurations, name="data.service-configurations", definition={'description': 'Service configuration values fetched.', 'type': 'array', 'items': {'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}}, rule='type')
            data__serviceconfigurations_is_list = isinstance(data__serviceconfigurations, (list, tuple))
            if data__serviceconfigurations_is_list:
                data__serviceconfigurations_len = len(data__serviceconfigurations)
                for data__serviceconfigurations_x, data__serviceconfigurations_item in enumerate(data__serviceconfigurations):
                    if not isinstance(data__serviceconfigurations_item, (dict)):
                        raise JsonSchemaException(""+"data.service-configurations[{data__serviceconfigurations_x}]".format(**locals())+" must be object", value=data__serviceconfigurations_item, name=""+"data.service-configurations[{data__serviceconfigurations_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}, rule='type')
                    data__serviceconfigurations_item_is_dict = isinstance(data__serviceconfigurations_item, dict)
                    if data__serviceconfigurations_item_is_dict:
                        data__serviceconfigurations_item_len = len(data__serviceconfigurations_item)
                        if not all(prop in data__serviceconfigurations_item for prop in ['namespace', 'service', 'color', 'purpose', 'configuration']):
                            raise JsonSchemaException(""+"data.service-configurations[{data__serviceconfigurations_x}]".format(**locals())+" must contain ['namespace', 'service', 'color', 'purpose', 'configuration'] properties", value=data__serviceconfigurations_item, name=""+"data.service-configurations[{data__serviceconfigurations_x}]".format(**locals())+"", definition={'type': 'object', 'required': ['namespace', 'service', 'color', 'purpose', 'configuration'], 'properties': {'namespace': {'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, 'purpose': {'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, 'configuration': {'description': 'The configured text.', 'type': 'string'}}}, rule='required')
                        data__serviceconfigurations_item_keys = set(data__serviceconfigurations_item.keys())
                        if "namespace" in data__serviceconfigurations_item_keys:
                            data__serviceconfigurations_item_keys.remove("namespace")
                            data__serviceconfigurations_item__namespace = data__serviceconfigurations_item["namespace"]
                            if not isinstance(data__serviceconfigurations_item__namespace, (str, NoneType)):
                                raise JsonSchemaException(""+"data.service-configurations[{data__serviceconfigurations_x}].namespace".format(**locals())+" must be string or null", value=data__serviceconfigurations_item__namespace, name=""+"data.service-configurations[{data__serviceconfigurations_x}].namespace".format(**locals())+"", definition={'description': 'Namespace of this template, or `null` if this is the default gateway template.', 'type': ['string', 'null']}, rule='type')
                        if "purpose" in data__serviceconfigurations_item_keys:
                            data__serviceconfigurations_item_keys.remove("purpose")
                            data__serviceconfigurations_item__purpose = data__serviceconfigurations_item["purpose"]
                            if not isinstance(data__serviceconfigurations_item__purpose, (str)):
                                raise JsonSchemaException(""+"data.service-configurations[{data__serviceconfigurations_x}].purpose".format(**locals())+" must be string", value=data__serviceconfigurations_item__purpose, name=""+"data.service-configurations[{data__serviceconfigurations_x}].purpose".format(**locals())+"", definition={'description': 'The purpose of this template, which is usually the destination file name, such as "cds.yaml" or "lds.yaml".  Multiple of these can be provided per namespace.\n', 'type': 'string'}, rule='type')
                        if "configuration" in data__serviceconfigurations_item_keys:
                            data__serviceconfigurations_item_keys.remove("configuration")
                            data__serviceconfigurations_item__configuration = data__serviceconfigurations_item["configuration"]
                            if not isinstance(data__serviceconfigurations_item__configuration, (str)):
                                raise JsonSchemaException(""+"data.service-configurations[{data__serviceconfigurations_x}].configuration".format(**locals())+" must be string", value=data__serviceconfigurations_item__configuration, name=""+"data.service-configurations[{data__serviceconfigurations_x}].configuration".format(**locals())+"", definition={'description': 'The configured text.', 'type': 'string'}, rule='type')
    return data