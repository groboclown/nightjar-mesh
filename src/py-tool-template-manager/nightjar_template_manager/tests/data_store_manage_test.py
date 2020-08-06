
"""Test the data_store_manage module."""

from typing import Dict, List, Any
import unittest
import os
import io
import sys
import tempfile
import shutil
import json
import platform
import argparse
from .. import data_store_manage
from ..config import Config


class DataStoreManageTest(unittest.TestCase):  # pylint: disable=R0904
    """Test the data_store_manage functions."""

    def setUp(self) -> None:
        python_cmd = 'python' if platform.system() == 'Windows' else 'python3'
        self._runnable = [
            python_cmd,
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'runnable.py'),
        ]
        self._temp_dir = tempfile.mkdtemp()
        self._file_index = 1
        self._orig_stdin = sys.stdin
        self.received_file = ''

    def tearDown(self) -> None:
        shutil.rmtree(self._temp_dir)
        sys.stdin = self._orig_stdin

    def test_update_gateway_template__update(self) -> None:
        """Test update_gateway_template with an update operation."""
        templates = _mk_templates([{
            'namespace': 'n1',
            'purpose': 'p1',
            'template': 'tuna',
        }], [])
        data_store_manage.update_gateway_template(templates, 'marlin', 'n1', 'p1')
        self.assertEqual(_mk_templates([{
            'namespace': 'n1',
            'purpose': 'p1',
            'template': 'marlin',
        }], []), templates)

    def test_update_gateway_template__insert(self) -> None:
        """Test update_gateway_template with an insert operation."""
        templates = _mk_templates([{
            'namespace': 'n1',
            'purpose': 'p1',
            'template': 'tuna',
        }], [])
        data_store_manage.update_gateway_template(templates, 'marlin', 'n1', 'p2')
        self.assertEqual(_mk_templates([{
            'namespace': 'n1',
            'purpose': 'p1',
            'template': 'tuna',
        }, {
            'namespace': 'n1',
            'purpose': 'p2',
            'template': 'marlin',
        }], []), templates)

    def test_update_service_template__update(self) -> None:
        """Test update_service_template with an update operation."""
        templates = _mk_templates([], [{
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p1',
            'template': 'tuna',
        }])
        data_store_manage.update_service_template(templates, 'marlin', 'n1', 's1', 'c1', 'p1')
        self.assertEqual(_mk_templates([], [{
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p1',
            'template': 'marlin',
        }]), templates)

    def test_update_service_template__insert(self) -> None:
        """Test update_service_template with an insert operation."""
        templates = _mk_templates([], [{
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p1',
            'template': 'tuna',
        }])
        data_store_manage.update_service_template(templates, 'marlin', 'n1', 's1', 'c1', 'p2')
        self.assertEqual(_mk_templates([], [{
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p1',
            'template': 'tuna',
        }, {
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p2',
            'template': 'marlin',
        }]), templates)

    def test_extract_gateway_template__exists(self) -> None:
        """Test extract_service_template for an existing service template"""
        templates = _mk_templates([{
            'namespace': 'n1',
            'purpose': 'p1',
            'template': 'tuna',
        }], [])
        res = data_store_manage.extract_gateway_template(templates, 'n1', 'p1')
        self.assertEqual('tuna', res)

    def test_extract_gateway_template__not_exists(self) -> None:
        """Test extract_service_template for a non-existing service template"""
        templates = _mk_templates([], [])
        res = data_store_manage.extract_gateway_template(templates, 'n1', 'p1')
        self.assertIsNone(res)

    def test_extract_service_template__exists(self) -> None:
        """Test extract_service_template for an existing service template"""
        templates = _mk_templates([], [{
            'namespace': 'n1',
            'service': 's1',
            'color': 'c1',
            'purpose': 'p1',
            'template': 'tuna',
        }])
        res = data_store_manage.extract_service_template(templates, 'n1', 's1', 'c1', 'p1')
        self.assertEqual('tuna', res)

    def test_extract_service_template__not_exists(self) -> None:
        """Test extract_service_template for a non-existing service template"""
        templates = _mk_templates([], [])
        res = data_store_manage.extract_service_template(templates, 'n1', 's1', 'c1', 'p1')
        self.assertIsNone(res)

    def test_push_template__no_purpose(self) -> None:
        """Test push_template with no purpose."""
        config = self._setup_config(_mk_templates([], []))
        res = data_store_manage.push_template(config)
        self.assertEqual(3, res)

    def test_push_template__no_local_file(self) -> None:
        """Test push_template with no local file."""
        config = self._setup_config(_mk_templates([], []))
        config.purpose = 'x.txt'
        res = data_store_manage.push_template(config)
        self.assertEqual(4, res)

    def test_push_template__no_category(self) -> None:
        """Test push_template with no category."""
        local_file = os.path.join(self._temp_dir, 'f.txt')
        with open(local_file, 'w') as f:
            f.write('blah')
        config = self._setup_config(_mk_templates([], []))
        config.purpose = 'x.txt'
        config.filename = local_file
        res = data_store_manage.push_template(config)
        self.assertEqual(5, res)

    def test_push_template__gateway(self) -> None:
        """Test push_template with a gateway"""
        config = self._setup_config(_mk_templates([], []))
        result_file = self.received_file
        config.filename = os.path.join(self._temp_dir, 'x.txt')
        with open(config.filename, 'w') as f:
            f.write('foo')
        config.purpose = 'x'
        config.category = 'gateway'
        config.namespace = 'n1'
        res = data_store_manage.push_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(result_file))
        with open(result_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(_mk_templates([{
            'namespace': 'n1',
            'purpose': 'x',
            'template': 'foo',
        }], []), data)

    def test_push_template__service_stdin(self) -> None:
        """Test push_template with a service"""
        config = self._setup_config(_mk_templates([], []))
        result_file = self.received_file
        config.filename = '-'
        sys.stdin = io.StringIO('foo')
        config.purpose = 'x'
        config.category = 'service'
        config.namespace = 'n1'
        config.service = 'a'
        config.color = 'b'
        res = data_store_manage.push_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(result_file))
        with open(result_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(_mk_templates([], [{
            'namespace': 'n1',
            'service': 'a',
            'color': 'b',
            'purpose': 'x',
            'template': 'foo',
        }]), data)

    def test_pull_template__no_purpose(self) -> None:
        """Test pull_template with no purpose."""
        config = self._setup_config(_mk_templates([], []))
        res = data_store_manage.pull_template(config)
        self.assertEqual(6, res)

    def test_pull_template__no_category(self) -> None:
        """Test pull_template with no category."""
        local_file = os.path.join(self._temp_dir, 'f.txt')
        with open(local_file, 'w') as f:
            f.write('blah')
        config = self._setup_config(_mk_templates([], []))
        config.purpose = 'x.txt'
        config.filename = local_file
        res = data_store_manage.pull_template(config)
        self.assertEqual(7, res)

    def test_pull_template__gateway_no_namespace(self) -> None:
        """Test pull_template for a gateway with no such namespace."""
        local_file = os.path.join(self._temp_dir, 'f.txt')
        with open(local_file, 'w') as f:
            f.write('blah')
        config = self._setup_config(_mk_templates([], []))
        config.purpose = 'x.txt'
        config.category = 'gateway'
        config.filename = local_file
        res = data_store_manage.pull_template(config)
        self.assertEqual(8, res)

    def test_pull_template__service_no_namespace(self) -> None:
        """Test pull_template for a gateway with no such namespace."""
        local_file = os.path.join(self._temp_dir, 'f.txt')
        with open(local_file, 'w') as f:
            f.write('blah')
        config = self._setup_config(_mk_templates([], []))
        config.purpose = 'x.txt'
        config.category = 'service'
        config.filename = local_file
        res = data_store_manage.pull_template(config)
        self.assertEqual(8, res)

    def test_pull_template__print(self) -> None:
        """Test pull_template for a gateway with no such namespace."""
        config = self._setup_config(_mk_templates([{
            'namespace': 'n1',
            'purpose': 'p',
            'template': 'blah',
        }], []))
        config.category = 'gateway'
        config.purpose = 'p'
        config.namespace = 'n1'
        config.filename = '-'
        res = data_store_manage.pull_template(config)
        self.assertEqual(0, res)

    def test_pull_template__write(self) -> None:
        """Test pull_template for a gateway with no such namespace."""
        config = self._setup_config(_mk_templates([{
            'namespace': 'n1',
            'purpose': 'p',
            'template': 'blah',
        }], []))
        config.category = 'gateway'
        config.purpose = 'p'
        config.namespace = 'n1'
        config.filename = os.path.join(self._temp_dir, 'out.txt')
        res = data_store_manage.pull_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(config.filename))
        with open(config.filename, 'r') as f:
            self.assertEqual('blah', f.read())

    def test_push_file__stdin(self) -> None:
        """Test push_file, using stdin as the file source."""
        config = self._setup_config({})
        out_file = self.received_file
        templates = _mk_templates([], [])
        sys.stdin = io.StringIO(json.dumps(templates))
        config.document_type = 'templates'
        config.filename = '-'
        res = data_store_manage.push_file(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(out_file))
        with open(out_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(templates, data)

    def test_push_file__file(self) -> None:
        """Test push_file, using a file as the file source."""
        config = self._setup_config({})
        out_file = self.received_file
        templates = _mk_templates([], [])
        inp = os.path.join(self._temp_dir, 'out.json')
        with open(inp, 'w') as f:
            json.dump(templates, f)
        config.document_type = 'templates'
        config.filename = inp
        res = data_store_manage.push_file(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(out_file))
        with open(out_file, 'r') as f:
            data = json.load(f)
        self.assertEqual(templates, data)

    def test_pull_file__stdout(self) -> None:
        """Test pull_file, extracting to stdout"""
        config = self._setup_config(_mk_templates([], []))
        config.document_type = 'templates'
        config.filename = '-'
        res = data_store_manage.pull_file(config)
        self.assertEqual(0, res)

    def test_pull_file__file(self) -> None:
        """Test pull_file, extracting to a file"""
        templates = _mk_templates([], [])
        config = self._setup_config(templates)
        config.document_type = 'templates'
        config.filename = os.path.join(self._temp_dir, 'out.json')
        res = data_store_manage.pull_file(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(config.filename))
        with open(config.filename, 'r') as f:
            data = json.load(f)
        self.assertEqual(templates, data)

    def test_list_template__stdout(self) -> None:
        """Test list_template to stdout"""
        config = self._setup_config(_mk_templates([], []))
        config.filename = '-'
        res = data_store_manage.list_template(config)
        self.assertEqual(0, res)

    def test_list_template__file_gateway_service(self) -> None:
        """Test list_template to a file for both gateways and services"""
        templates = _mk_templates(
            [
                {
                    'namespace': 'n1',
                    'purpose': 'p1',
                    'template': 'g1',
                },
                {
                    'namespace': 'n2',
                    'purpose': 'p2',
                    'template': 'g2',
                },
            ], [
                {
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'purpose': 'p1',
                    'template': 'sc1',
                },
                {
                    'namespace': 'n2',
                    'service': 's2',
                    'color': 'c2',
                    'purpose': 'p2',
                    'template': 'sc2',
                },
            ],
        )
        config = self._setup_config(templates)
        config.filename = os.path.join(self._temp_dir, 'out.json')
        res = data_store_manage.list_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(config.filename))
        with open(config.filename, 'r') as f:
            data = f.read()
        self.assertEqual(
            """Gateway-Templates:
  - namespace: n1
    purpose:   p1
  - namespace: n2
    purpose:   p2
Service-Templates:
  - namespace: n1
    service:   s1
    color:     c1
    purpose:   p1
  - namespace: n2
    service:   s2
    color:     c2
    purpose:   p2
""",
            data,
        )

    def test_list_template__file_gateway(self) -> None:
        """Test list_template to a file for just gateways"""
        templates = _mk_templates(
            [
                {
                    'namespace': 'n1',
                    'purpose': 'p1',
                    'template': 'g1',
                },
                {
                    'namespace': 'n2',
                    'purpose': 'p2',
                    'template': 'g2',
                },
            ], [
                {
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'purpose': 'p1',
                    'template': 'sc1',
                },
                {
                    'namespace': 'n2',
                    'service': 's2',
                    'color': 'c2',
                    'purpose': 'p2',
                    'template': 'sc2',
                },
            ],
        )
        config = self._setup_config(templates)
        config.filename = os.path.join(self._temp_dir, 'out.json')
        config.category = 'gateway'
        res = data_store_manage.list_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(config.filename))
        with open(config.filename, 'r') as f:
            data = f.read()
        self.assertEqual(
            """Gateway-Templates:
  - namespace: n1
    purpose:   p1
  - namespace: n2
    purpose:   p2
""",
            data,
        )

    def test_list_template__file_service(self) -> None:
        """Test list_template to a file for just services"""
        templates = _mk_templates(
            [
                {
                    'namespace': 'n1',
                    'purpose': 'p1',
                    'template': 'g1',
                },
                {
                    'namespace': 'n2',
                    'purpose': 'p2',
                    'template': 'g2',
                },
            ], [
                {
                    'namespace': 'n1',
                    'service': 's1',
                    'color': 'c1',
                    'purpose': 'p1',
                    'template': 'sc1',
                },
                {
                    'namespace': 'n2',
                    'service': 's2',
                    'color': 'c2',
                    'purpose': 'p2',
                    'template': 'sc2',
                },
            ],
        )
        config = self._setup_config(templates)
        config.filename = os.path.join(self._temp_dir, 'out.json')
        config.category = 'service'
        res = data_store_manage.list_template(config)
        self.assertEqual(0, res)
        self.assertTrue(os.path.isfile(config.filename))
        with open(config.filename, 'r') as f:
            data = f.read()
        self.assertEqual(
            """Service-Templates:
  - namespace: n1
    service:   s1
    color:     c1
    purpose:   p1
  - namespace: n2
    service:   s2
    color:     c2
    purpose:   p2
""",
            data,
        )

    def _setup_config(self, fetched_contents: Dict[str, Any]) -> Config:
        self.received_file = os.path.join(self._temp_dir, '{0}-out.json'.format(self._file_index))
        generate = os.path.join(self._temp_dir, '{0}-out.json'.format(self._file_index))
        self._file_index += 1
        with open(generate, 'w') as f:
            json.dump(fetched_contents, f)
        command = list(self._runnable)
        command.append('0')
        command.append(self.received_file)
        command.append(generate)

        return Config(
            argparse.Namespace(
                document='',
                local_file='',
                category='',
                purpose='',
                namespace='default',
                service='default',
                color='default',
                action='none',
            ),
            {
                'CACHE_DIR': self._temp_dir,
                'DATA_STORE_EXEC': ' '.join(command),
            },
        )


def _mk_templates(
        gateways: List[Dict[str, Any]], services: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        'schema-version': 'v1',
        'document-version': '1',
        'gateway-templates': gateways,
        'service-templates': services,
    }
