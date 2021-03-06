
"""
Test the generate module.
"""

from typing import List, Dict, Any
import unittest
import os
import platform
import shutil
import json
from nightjar_common.validation import validate_discovery_map, validate_templates
from .. import generate
from ..config import (
    Config,
    ENV__ENVOY_CMD, ENV__DATA_STORE_EXEC, ENV__DISCOVERY_MAP_EXEC,
    GATEWAY_PROXY_MODE, SERVICE_PROXY_MODE,
)


class GeneratorTest(unittest.TestCase):
    """Test the generator functions and classes."""
    # These are all smashed together, because they share the same setup and teardown logic.
    # Yeah, it's a lousy reason to jam them together, but it makes less duplication.

    def setUp(self) -> None:
        noop_cmd = 'where' if platform.system() == 'Windows' else 'echo'
        python_cmd = 'python' if platform.system() == 'Windows' else 'python3'
        self._runnable = [
            python_cmd,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runnable.py'),
        ]
        self._config = Config({
            ENV__ENVOY_CMD: noop_cmd,
            ENV__DISCOVERY_MAP_EXEC: noop_cmd,
            ENV__DATA_STORE_EXEC: noop_cmd,
        })
        self._config.envoy_config_dir = self._config.temp_dir
        self._config.envoy_config_file = os.path.join(
            self._config.envoy_config_dir, self._config.envoy_config_template,
        )
        self._file_index = 0

    def tearDown(self) -> None:
        shutil.rmtree(self._config.temp_dir)

    # -----------------------------------------------------------------------
    def test_create_gateway_generator(self) -> None:
        """Test the create generator with a gateway request."""
        self._config.proxy_mode = GATEWAY_PROXY_MODE
        res = generate.create_generator(self._config)
        self.assertIsInstance(res, generate.GenerateGatewayConfiguration)

    def test_create_service_generator(self) -> None:
        """Test the create generator with a gateway request."""
        self._config.proxy_mode = SERVICE_PROXY_MODE
        res = generate.create_generator(self._config)
        self.assertIsInstance(res, generate.GenerateServiceConfiguration)

    # -----------------------------------------------------------------------
    def test_gateway_template_discovery__no_templates(self) -> None:
        """Test gateway template discovery, when there are no templates."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [],
                'service-templates': [],
            },
        )
        gateway = generate.GenerateGatewayConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual({}, templates)

    def test_gateway_template_discovery__just_default_templates(self) -> None:
        """Test gateway template discovery, when only default templates are given."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [{
                    'namespace': None,
                    'protection': 'public',
                    'purpose': 'abc',
                    'template': 'xyz',
                }],
                'service-templates': [],
            },
        )
        gateway = generate.GenerateGatewayConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual(
            {'abc': 'xyz'},
            templates,
        )

    def test_gateway_template_discovery__mixed_templates(self) -> None:
        """Test gateway template discovery, when a mixture of defalt, current, and other
        namespaces are given."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [{
                    'namespace': None,
                    'protection': 'public',
                    'purpose': 'abc',
                    'template': 'xyz',
                }, {
                    'namespace': 'n1',
                    'protection': 'public',
                    'purpose': 'abc',
                    'template': '123',
                }, {
                    'namespace': None,
                    'protection': 'public',
                    'purpose': 'def',
                    'template': '456',
                }, {
                    'namespace': 'n1',
                    'protection': 'public',
                    'purpose': 'hij',
                    'template': '789',
                }, {
                    'namespace': 'n2',
                    'protection': 'public',
                    'purpose': 'hij',
                    'template': '789',
                }],
                'service-templates': [],
            },
        )
        gateway = generate.GenerateGatewayConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual(
            {'abc': '123', 'hij': '789'},
            templates,
        )

    def test_gateway_generate_file(self) -> None:
        """Test the gateway generate_file function.  Uses a simple setup."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, validate_templates({
                'schema-version': 'v1',
                'document-version': 'x',
                'service-templates': [],
                'gateway-templates': [{
                    'namespace': 'n1',
                    'purpose': 'out-1.txt',
                    'template': '1 {{schema-version}} 2 {{has_admin_port}} 3 {{has_clusters}} 4',
                }, {
                    'namespace': 'n1',
                    'purpose': 'out-2.txt',
                    'template': 'z {{schema-version}} y',
                }],
            }),
        )
        self._config.discovery_map_exec = self._get_runnable_cmd(0, validate_discovery_map({
            'schema-version': 'v1',
            'document-version': 'd1',
            'namespaces': [{
                'namespace': 'n1',
                'network-id': 'nk1',
                'gateways': {'instances': [], 'prefer-gateway': False, 'protocol': 'http1.1'},
                'service-colors': [{
                    'service': 's1',
                    'color': 'c1',
                    'index': 1,
                    'routes': [],
                    'instances': [],
                    'namespace-egress': [],
                }],
            }],
        }))

        gateway = generate.GenerateGatewayConfiguration(self._config)
        res = gateway.generate_file(1, 2)
        self.assertEqual(0, res)

        out_file_1 = os.path.join(self._config.envoy_config_dir, 'out-1.txt')
        self.assertTrue(os.path.isfile(out_file_1))
        out_file_2 = os.path.join(self._config.envoy_config_dir, 'out-2.txt')
        self.assertTrue(os.path.isfile(out_file_2))

        with open(out_file_1, 'r') as f:
            self.assertEqual('1 v1 2 True 3 False 4', f.read())

        with open(out_file_2, 'r') as f:
            self.assertEqual('z v1 y', f.read())

    def test_gateway_generate_file__no_match(self) -> None:
        """Test the gateway generate_file function when the proxy input is None."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, validate_templates({
                'schema-version': 'v1',
                'document-version': 'x',
                'service-templates': [],
                'gateway-templates': [{
                    'namespace': 'n1',
                    'purpose': 'out-1.txt',
                    'template': '1 {{schema-version}} 2 {{has_admin_port}} 3 {{has_clusters}} 4',
                }],
            }),
        )
        self._config.discovery_map_exec = self._get_runnable_cmd(0, validate_discovery_map({
            'schema-version': 'v1',
            'document-version': 'd1',
            'namespaces': [],
        }))

        gateway = generate.GenerateGatewayConfiguration(self._config)
        res = gateway.generate_file(1, 2)
        self.assertEqual(1, res)

    def test_gateway_generate_file__with_error(self) -> None:
        """Test the gateway generate_file function that generates an error."""
        self._config.namespace = 'n1'
        self._config.data_store_exec = self._get_runnable_cmd(
            12, validate_templates({
                'schema-version': 'v1',
                'document-version': 'x',
                'service-templates': [],
                'gateway-templates': [{
                    'namespace': 'n1',
                    'purpose': 'out-1.txt',
                    'template': '1 {{schema-version}} 2 {{has_admin_port}} 3 {{has_clusters}} 4',
                }, {
                    'namespace': 'n1',
                    'purpose': 'out-2.txt',
                    'template': 'z {{schema-version}} y',
                }],
            }),
        )
        self._config.discovery_map_exec = self._get_runnable_cmd(0, validate_discovery_map({
            'schema-version': 'v1',
            'document-version': 'd1',
            'namespaces': [{
                'namespace': 'n1',
                'network-id': 'nk1',
                'gateways': {'instances': [], 'prefer-gateway': False, 'protocol': 'http1.1'},
                'service-colors': [{
                    'service': 's1',
                    'color': 'c1',
                    'index': 12,
                    'routes': [],
                    'instances': [],
                    'namespace-egress': [],
                }],
            }],
        }))

        gateway = generate.GenerateGatewayConfiguration(self._config)
        res = gateway.generate_file(1, 2)
        self.assertEqual(1, res)

        out_file_1 = os.path.join(self._config.envoy_config_dir, 'out-1.txt')
        self.assertFalse(os.path.isfile(out_file_1))
        out_file_2 = os.path.join(self._config.envoy_config_dir, 'out-2.txt')
        self.assertFalse(os.path.isfile(out_file_2))

    # -----------------------------------------------------------------------
    def test_service_get_templates__no_templates(self) -> None:
        """Test the service generator with no template files."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 't1',
                'gateway-templates': [],
                'service-templates': [],
            },
        )
        gateway = generate.GenerateServiceConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual({}, templates)

    def test_service_get_templates__defaults(self) -> None:
        """Test the service generator with no template files."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        combos = (
            (None, None, None,),
            ('n1', None, None,),
            (None, 's1', None,),
            (None, None, 'c1',),
            ('n1', 's1', None,),
            ('n1', None, 'c1',),
            (None, 's1', 'c1',),
            ('n1', 's1', 'c1',),
        )
        for namespace, service, color in combos:
            with self.subTest('{0}-{1}-{2}'.format(namespace, service, color)):
                if os.path.exists(os.path.join(self._config.envoy_config_dir, 'cdb.json')):
                    os.unlink(  # pragma no cover
                        os.path.join(self._config.envoy_config_dir, 'cdb.json')
                    )
                self._config.data_store_exec = self._get_runnable_cmd(
                    0, {
                        'schema-version': 'v1',
                        'document-version': 'x',
                        'gateway-templates': [],
                        'service-templates': [{
                            'namespace': namespace,
                            'service': service,
                            'color': color,
                            'purpose': 'cdb.json',
                            'template': '1234',
                        }],
                    },
                )
                gateway = generate.GenerateServiceConfiguration(self._config)
                templates = gateway.get_templates()
                self.assertEqual({'cdb.json': '1234'}, templates)

    def test_service_get_templates__mix_1(self) -> None:
        """Test the service generator with no template files."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [],
                'service-templates': [{
                    'namespace': 'n1',
                    'service': None,
                    'color': None,
                    'purpose': 'cdb.json',
                    'template': 'n',
                }, {
                    'namespace': None,
                    'service': 's1',
                    'color': None,
                    'purpose': 'cdb.json',
                    'template': 's',
                }, {
                    'namespace': None,
                    'service': None,
                    'color': 'c1',
                    'purpose': 'cdb.json',
                    'template': 'c',
                }],
            },
        )
        gateway = generate.GenerateServiceConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual({'cdb.json': 'n'}, templates)

    def test_service_get_templates__mix_2(self) -> None:
        """Test the service generator with no template files."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, {
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [],
                'service-templates': [{
                    'namespace': 'n1',
                    'service': None,
                    'color': None,
                    'purpose': 'cdb.json',
                    'template': 'n',
                }, {
                    'namespace': None,
                    'service': 's1',
                    'color': 'c1',
                    'purpose': 'cdb.json',
                    'template': 'sc',
                }],
            },
        )
        gateway = generate.GenerateServiceConfiguration(self._config)
        templates = gateway.get_templates()
        self.assertEqual({'cdb.json': 'n'}, templates)

    def test_service_generate_file(self) -> None:
        """Test the service generate_file function.  Uses a simple setup."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, validate_templates({
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [],
                'service-templates': [{
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'index': 199,
                    'purpose': 'out-1.txt',
                    'template': '1 {{schema-version}} 2 {{has_admin_port}} 3 {{has_clusters}} 4',
                }, {
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'index': 199,
                    'purpose': 'out-2.txt',
                    'template': 'z {{schema-version}} y',
                }],
            })
        )
        self._config.discovery_map_exec = self._get_runnable_cmd(0, validate_discovery_map({
            'schema-version': 'v1',
            'document-version': 'd12',
            'namespaces': [{
                'namespace': 'n1',
                'network-id': 'nk1',
                'gateways': {'instances': [], 'prefer-gateway': True, 'protocol': 'http2'},
                'service-colors': [{
                    'service': 's1',
                    'color': 'c1',
                    'index': 199,
                    'routes': [],
                    'instances': [],
                    'namespace-egress': [],
                }],
            }],
        }))

        gateway = generate.GenerateServiceConfiguration(self._config)
        gateway.generate_file(3, 4)

        out_file_1 = os.path.join(self._config.envoy_config_dir, 'out-1.txt')
        self.assertTrue(os.path.isfile(out_file_1))
        out_file_2 = os.path.join(self._config.envoy_config_dir, 'out-2.txt')
        self.assertTrue(os.path.isfile(out_file_2))

        with open(out_file_1, 'r') as f:
            self.assertEqual('1 v1 2 True 3 False 4', f.read())

        with open(out_file_2, 'r') as f:
            self.assertEqual('z v1 y', f.read())

    def test_service_generate_file__no_match(self) -> None:
        """Test the service generate_file function.  Uses a simple setup."""
        self._config.namespace = 'n1'
        self._config.service = 's1'
        self._config.color = 'c1'
        self._config.data_store_exec = self._get_runnable_cmd(
            0, validate_templates({
                'schema-version': 'v1',
                'document-version': 'x',
                'gateway-templates': [],
                'service-templates': [{
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'index': 199,
                    'purpose': 'out-1.txt',
                    'template': '1 {{schema-version}} 2 {{has_admin_port}} 3 {{has_clusters}} 4',
                }],
            })
        )
        self._config.discovery_map_exec = self._get_runnable_cmd(0, validate_discovery_map({
            'schema-version': 'v1',
            'document-version': 'd12',
            'namespaces': [],
        }))

        gateway = generate.GenerateServiceConfiguration(self._config)
        res = gateway.generate_file(3, 4)
        self.assertEqual(1, res)

    def test_generate_envoy_file__no_change(self) -> None:
        """Run generate_envoy_file with no changes to the files."""
        requested_out_file = os.path.join(self._config.envoy_config_dir, 'x.txt')
        with open(requested_out_file, 'w') as f:
            f.write('x')
        generate.generate_envoy_file(self._config, 'x.txt', 'x')
        self.assertTrue(os.path.isfile(requested_out_file))
        with open(requested_out_file, 'r') as f:
            self.assertEqual('x', f.read())

    def test_generate_envoy_file__replaced(self) -> None:
        """Run generate_envoy_file with no changes to the files."""
        requested_out_file = os.path.join(self._config.envoy_config_dir, 'x.txt')
        with open(requested_out_file, 'w') as f:
            f.write('y')
        generate.generate_envoy_file(self._config, 'x.txt', 'x')
        self.assertTrue(os.path.isfile(requested_out_file))
        with open(requested_out_file, 'r') as f:
            self.assertEqual('x', f.read())

    # -----------------------------------------------------------------------
    def _get_runnable_cmd(
            self, exit_code: int, src_contents: Dict[str, Any],
    ) -> List[str]:
        ret = list(self._runnable)
        ret.append(str(exit_code))
        self._file_index += 1
        out = os.path.join(self._config.temp_dir, '{0}-src.json'.format(self._file_index))
        with open(out, 'w') as f:
            json.dump(src_contents, f)
        ret.append(out)
        return ret
