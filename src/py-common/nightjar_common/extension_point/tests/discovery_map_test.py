
"""
Test the discovery_map module.
"""

import unittest
import os
import tempfile
import shutil
import json
from .invoke_runnable import RunnableInvoker
from .. import discovery_map
from ..exceptions import ExtensionPointRuntimeError, ExtensionPointTooManyRetries
from ...fastjsonschema_replacement import JsonSchemaException


class DiscoveryMapRunnerTest(unittest.TestCase):
    """Test the DiscoveryMapRunner class."""

    def setUp(self) -> None:
        self._tempdir = tempfile.mkdtemp()

    def tearDown(self) -> None:
        shutil.rmtree(self._tempdir)

    def test_runnable_works(self) -> None:
        """Ensures the runnable works, and also exercises the run once method."""
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(
            invoker.prepare_runnable([0]),
            self._tempdir,
        )
        action_file = os.path.join(self._tempdir, 'x.txt')
        res = runner.run_discovery_map_once(action_file)
        self.assertEqual(0, res)
        self.assertEqual(
            [[
                '--output-file=' + os.path.join(self._tempdir, 'x.txt'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_run_discovery_map__retry_fails(self) -> None:
        """Ensures the runnable works, and also exercises the run once method."""
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(
            invoker.prepare_runnable([31, 31, 31]),
            self._tempdir,
        )
        runner.max_retry_count = 3
        runner.max_retry_wait_seconds = 0.05
        action_file = os.path.join(self._tempdir, 'x.txt')
        try:
            runner.run_discovery_map(action_file)
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointTooManyRetries as err:
            self.assertEqual('discovery map', err.source)
            self.assertEqual('retrieve', err.action)
        self.assertEqual(
            [
                [
                    '--output-file=' + os.path.join(self._tempdir, 'x.txt'),
                    '--api-version=1',
                ],
                [
                    '--output-file=' + os.path.join(self._tempdir, 'x.txt'),
                    '--api-version=1',
                ],
                [
                    '--output-file=' + os.path.join(self._tempdir, 'x.txt'),
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )

    def test_run_discovery_map__error(self) -> None:
        """Ensures the runnable works, and also exercises the run once method."""
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(
            invoker.prepare_runnable([1]),
            self._tempdir,
        )
        action_file = os.path.join(self._tempdir, 'x.txt')
        try:
            runner.run_discovery_map(action_file)
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('discovery map', err.source)
            self.assertEqual('retrieve', err.action)
            self.assertEqual(1, err.exit_code)
        self.assertEqual(
            [[
                '--output-file=' + os.path.join(self._tempdir, 'x.txt'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_get_mesh__success(self) -> None:
        """Ensure the get_mesh works with valid results."""
        expected_data = {
            'version': 'v1',
            'namespaces': [],
        }
        with open(os.path.join(self._tempdir, 'mesh.json'), 'w') as f:
            json.dump(expected_data, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(invoker.prepare_runnable([0]), self._tempdir)
        res = runner.get_mesh()
        self.assertEqual(expected_data, res)
        self.assertEqual(
            [[
                '--output-file=' + os.path.join(self._tempdir, 'mesh.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # Ensure the file isn't deleted after being pulled.
        self.assertTrue(os.path.isfile(os.path.join(self._tempdir, 'mesh.json')))

    def test_get_mesh__failed_validation(self) -> None:
        """Ensure the get_mesh works with valid results."""
        expected_data = {
            'version': 'v-1',
            'gateways': [],
            'services': [],
        }
        with open(os.path.join(self._tempdir, 'mesh.json'), 'w') as f:
            json.dump(expected_data, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(invoker.prepare_runnable([0]), self._tempdir)
        try:
            runner.get_mesh()
            self.fail('Did not generate a schema error')  # pragma no cover
        except JsonSchemaException:
            pass
        self.assertEqual(
            [[
                '--output-file=' + os.path.join(self._tempdir, 'mesh.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # Ensure the file isn't deleted after being pulled.
        self.assertTrue(os.path.isfile(os.path.join(self._tempdir, 'mesh.json')))
