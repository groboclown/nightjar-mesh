
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
from ..cached_document import DOCUMENT_VERSION_KEY
from ..errors import ExtensionPointRuntimeError, ExtensionPointTooManyRetries


class DiscoveryMapRunnerTest(unittest.TestCase):
    """Test the DiscoveryMapRunner class."""

    def setUp(self) -> None:
        self._tempdir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self._tempdir, 'mesh-cache.json')
        self.fetch_file = os.path.join(self._tempdir, 'mesh-fetching.json')

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
        res = runner.run_discovery_map_once(action_file, '')
        self.assertEqual(0, res)
        self.assertEqual(
            [[
                '--action-file=' + os.path.join(self._tempdir, 'x.txt'),
                '--previous-document-version=',
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
        try:
            runner.run_discovery_map()
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointTooManyRetries as err:
            self.assertEqual('discovery_map', err.source)
            self.assertEqual('fetch discovery-map', err.action)
        self.assertEqual(
            [
                [
                    '--action-file=' + self.fetch_file,
                    '--previous-document-version=',
                    '--api-version=1',
                ],
                [
                    '--action-file=' + self.fetch_file,
                    '--previous-document-version=',
                    '--api-version=1',
                ],
                [
                    '--action-file=' + self.fetch_file,
                    '--previous-document-version=',
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
        try:
            runner.run_discovery_map()
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('discovery_map', err.source)
            self.assertEqual('fetch discovery-map', err.action)
            self.assertEqual(1, err.exit_code)
        self.assertEqual(
            [[
                '--action-file=' + self.fetch_file,
                '--previous-document-version=',
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_get_mesh__success(self) -> None:
        """Ensure the get_mesh works with valid results."""
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: '1',
            'namespaces': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(invoker.prepare_runnable([0]), self._tempdir)
        # Due to clean logic, need to create the cache file AFTER runner creation.
        with open(self.fetch_file, 'w') as f:
            json.dump(expected_data, f)
        # No fall-back cache version to use.

        res = runner.get_mesh()

        self.assertEqual(expected_data, res)
        self.assertEqual(
            [[
                '--action-file=' + self.fetch_file,
                '--previous-document-version=',
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # Ensure the file isn't deleted after being pulled.
        self.assertTrue(self.cache_file)

    def test_get_mesh__use_cached(self) -> None:
        """Ensure the get_mesh works with valid results."""

        # First, create the cached version.
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: 'doc-1',
            'namespaces': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(invoker.prepare_runnable([0, 30]), self._tempdir)
        # Due to clean logic, need to create the cache file AFTER runner creation.
        with open(self.fetch_file, 'w') as f:
            json.dump(expected_data, f)
        res = runner.get_mesh()
        self.assertEqual(expected_data, res)
        self.assertEqual(
            [[
                '--action-file=' + self.fetch_file,
                '--previous-document-version=',
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # Ensure the cached file still exists.
        self.assertTrue(os.path.isfile(self.cache_file))

        # Now run with a "use cache result.
        invoker.clear_arguments()
        res = runner.get_mesh()
        self.assertEqual(expected_data, res)
        self.assertEqual(
            [[
                '--action-file=' + self.fetch_file,
                '--previous-document-version=doc-1',
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # Ensure the cached file still exists.
        self.assertTrue(os.path.isfile(self.cache_file))

    def test_get_mesh__failed_validation(self) -> None:
        """Ensure the get_mesh works with valid results."""
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: '1',
            'gateways': [],
            'services': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = discovery_map.DiscoveryMapRunner(invoker.prepare_runnable([0]), self._tempdir)
        # Due to clean logic, need to create the cache file AFTER runner creation.

        # The "fetching" is what's returned by the discovery map extension point.
        with open(os.path.join(self._tempdir, 'mesh-fetching.json'), 'w') as f:
            f.write('not json')

        # The "cached" is what's supposedly already present.
        with open(os.path.join(self._tempdir, 'mesh-cache.json'), 'w') as f:
            json.dump(expected_data, f)

        # The validation problem will cause the runner to report a warning but fall back on
        # the cached version.
        res = runner.get_mesh()

        self.assertEqual(expected_data, res)
        self.assertEqual(
            [[
                '--action-file=' + os.path.join(self._tempdir, 'mesh-fetching.json'),
                '--previous-document-version=',
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

        # Ensure the cached version still exists.
        self.assertTrue(os.path.isfile(os.path.join(self._tempdir, 'mesh-cache.json')))
