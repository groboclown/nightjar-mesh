
"""
Tests the data_store module.
"""

import unittest
import os
import tempfile
import shutil
import json
from .invoke_runnable import RunnableInvoker
from .. import data_store
from ..cached_document import DOCUMENT_VERSION_KEY
from ..errors import ExtensionPointTooManyRetries, ExtensionPointRuntimeError
from ...fastjsonschema_replacement import JsonSchemaException


class DataStoreRunnerTest(unittest.TestCase):
    """Tests the DataStoreRunner class"""

    def setUp(self) -> None:
        self._tempdir = tempfile.mkdtemp()
        self.template_cache_file = os.path.join(self._tempdir, 'templates-cached.json')
        self.template_fetch_file = os.path.join(self._tempdir, 'templates-new.json')
        self.template_commit_file = os.path.join(self._tempdir, 'templates-pending.json')
        self.dm_cache_file = os.path.join(self._tempdir, 'discovery-map-cached.json')
        self.dm_fetch_file = os.path.join(self._tempdir, 'discovery-map-new.json')
        self.dm_commit_file = os.path.join(self._tempdir, 'discovery-map-pending.json')

    def tearDown(self) -> None:
        shutil.rmtree(self._tempdir)

    def test_runnable_works(self) -> None:
        """Ensures the runnable works, and also exercises the run once method."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(
            invoker.prepare_runnable([0]),
            self._tempdir,
        )
        action_file = os.path.join(self._tempdir, 'x.txt')
        res = runner.run_data_store_once(action_file, 'fetch', 'templates', '1')
        self.assertEqual(0, res)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=fetch',
                '--previous-document-version=1',
                '--action-file=' + action_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__success(self) -> None:
        """Tests the commit_document for templates with successful result."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        runner.commit_document('templates', {
            DOCUMENT_VERSION_KEY: '1',
            'schema-version': 'v1',
            'activity': 'template',
            'gateway-templates': [],
            'service-templates': [],
        })
        self.assertEqual(
            [[
                '--document=templates',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.template_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__failure(self) -> None:
        """Tests the commit_document for templates with invoke failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([2]), self._tempdir)
        try:
            runner.commit_document('templates', {
                'schema-version': 'v1',
                DOCUMENT_VERSION_KEY: '2',
                'activity': 'template',
                'gateway-templates': [],
                'service-templates': [],
            })
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data_store', err.source)
            self.assertEqual('commit templates', err.action)
            self.assertEqual(2, err.exit_code)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.template_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__retry_failure(self) -> None:
        """Tests commit_document for templates with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 1
        try:
            runner.commit_document('templates', {
                'schema-version': 'v1',
                DOCUMENT_VERSION_KEY: 'asdf',
                'gateway-templates': [],
                'service-templates': [],
            })
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data_store', err.source)
            self.assertEqual('commit templates', err.action)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.template_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__validation_error(self) -> None:
        """Tests the commit_document for templates with data validation errors."""
        runner = data_store.DataStoreRunner([], self._tempdir)
        try:
            runner.commit_document('templates', {})
            self.fail('Should have raised an exception')  # pragma no cover
        except JsonSchemaException:
            pass

    def test_commit_discovery_map__success_and_use_cache(self) -> None:
        """Tests the commit_document for a discovery map with successful result."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0, 0]), self._tempdir)
        with open(self.dm_cache_file, 'w') as f:
            f.write('boo')
        runner.commit_document('discovery-map', {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: '123',
            'namespaces': [],
        })
        self.assertEqual(
            [[
                '--document=discovery-map',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.dm_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        # The cached version should be removed after a commit.
        self.assertFalse(os.path.isfile(self.dm_cache_file))

        cached_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: '345',
            'namespaces': [],
        }
        with open(self.dm_fetch_file, 'w') as f:
            json.dump(cached_data, f)
        invoker.clear_arguments()
        res = runner.fetch_document('discovery-map')
        self.assertEqual(
            [[
                '--document=discovery-map',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.dm_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        self.assertEqual(cached_data, res)

    def test_commit_discovery_map__failure(self) -> None:
        """Tests the commit_document for a discovery-map with invoke failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([2]), self._tempdir)
        try:
            runner.commit_document('discovery-map', {
                'schema-version': 'v1',
                DOCUMENT_VERSION_KEY: 'xyz',
                'namespaces': [],
            })
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data_store', err.source)
            self.assertEqual('commit discovery-map', err.action)
            self.assertEqual(2, err.exit_code)
        self.assertEqual(
            [[
                '--document=discovery-map',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.dm_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_discovery_map__retry_failure(self) -> None:
        """Tests fetch_document for discovery-map with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 1
        try:
            runner.commit_document('discovery-map', {
                'schema-version': 'v1',
                DOCUMENT_VERSION_KEY: '33',
                'namespaces': [],
            })
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data_store', err.source)
            self.assertEqual('commit discovery-map', err.action)
        self.assertEqual(
            [[
                '--document=discovery-map',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + self.dm_commit_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_discovery_map__validation_error(self) -> None:
        """Tests the commit_document with data validation errors."""
        runner = data_store.DataStoreRunner([], self._tempdir)
        try:
            runner.commit_document('discovery-map', {})
            self.fail('Should have raised an exception')  # pragma no cover
        except JsonSchemaException:
            pass

    def test_fetch_templates__success(self) -> None:
        """Tests fetch_document for templates with successful return and data validation."""
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: '1',
            'gateway-templates': [],
            'service-templates': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        with open(self.template_fetch_file, 'w') as f:
            json.dump(expected_data, f)
        data = runner.fetch_document('templates')
        self.assertEqual(expected_data, data)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.template_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        self.assertTrue(os.path.isfile(self.template_cache_file))
        with open(self.template_cache_file, 'r') as f:
            self.assertEqual(expected_data, json.load(f))

    def test_fetch_templates__repeated_same_version(self) -> None:
        """Tests fetch_document for templates with same version return code."""
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: 'x1x',
            'gateway-templates': [],
            'service-templates': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0, 30]), self._tempdir)
        with open(os.path.join(self.template_fetch_file), 'w') as f:
            json.dump(expected_data, f)

        # Make the call with no cached version.  The call will exit with 0.
        data = runner.fetch_document('templates')
        self.assertEqual(expected_data, data)
        self.assertFalse(os.path.isfile(self.template_fetch_file))
        self.assertTrue(os.path.isfile(self.template_cache_file))

        # Make the call again with version x1x.  The call will exit with 30.
        data = runner.fetch_document('templates')
        self.assertEqual(expected_data, data)
        self.assertFalse(os.path.isfile(self.template_fetch_file))
        self.assertTrue(os.path.isfile(self.template_cache_file))
        self.assertEqual(
            [
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + self.template_fetch_file,
                    '--api-version=1',
                ],
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=x1x',
                    '--action-file=' + self.template_fetch_file,
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__failure(self) -> None:
        """Tests fetch_templates with failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([1]), self._tempdir)
        try:
            runner.fetch_document('templates')
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data_store', err.source)
            self.assertEqual('fetch templates', err.action)
            self.assertEqual(1, err.exit_code)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.template_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        self.assertFalse(os.path.isfile(self.template_cache_file))

    def test_fetch_templates__retry_with_no_previous(self) -> None:
        """Tests fetch_document for templates with failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([30]), self._tempdir)
        try:
            runner.fetch_document('templates')
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointRuntimeError as err:  # pylint: disable=W0703
            self.assertEqual('data_store', err.source)
            self.assertEqual('fetch templates', err.action)
            self.assertEqual(30, err.exit_code)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.template_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__retry_failure(self) -> None:
        """Tests fetch_document for templates with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31, 31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 2
        try:
            runner.fetch_document('templates')
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data_store', err.source)
            self.assertEqual('fetch templates', err.action)
        self.assertEqual(
            [
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + self.template_fetch_file,
                    '--api-version=1',
                ],
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + self.template_fetch_file,
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__validation_error(self) -> None:
        """Tests fetch_document for templates with successful return and data validation."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        with open(self.template_fetch_file, 'w') as f:
            json.dump({"blah": "woo"}, f)
        try:
            runner.fetch_document('templates')
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data_store', err.source)
            self.assertEqual('create file', err.action)
            self.assertEqual(0, err.exit_code)
        self.assertEqual(
            [[
                '--document=templates',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.template_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        self.assertFalse(os.path.isfile(self.template_cache_file))

    def test_fetch_discovery_map__success(self) -> None:
        """Tests fetch_document for discovery-map with successful return and data validation."""
        expected_data = {
            'schema-version': 'v1',
            DOCUMENT_VERSION_KEY: 'x',
            'namespaces': [],
        }
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        with open(self.dm_fetch_file, 'w') as f:
            json.dump(expected_data, f)
        data = runner.fetch_document('discovery-map')
        self.assertEqual(expected_data, data)
        self.assertEqual(
            [[
                '--document=discovery-map',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + self.dm_fetch_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )
        self.assertTrue(os.path.isfile(self.dm_cache_file))
        with open(self.dm_cache_file, 'r') as f:
            self.assertEqual(expected_data, json.load(f))

    def test_runnable_with_backoff__error(self) -> None:
        """Ensures the backoff invocation, with an eventual error, works as expected."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(
            invoker.prepare_runnable([31, 31, 2]),
            self._tempdir,
        )
        runner.max_retry_wait_seconds = 0.05
        action_file = os.path.join(self._tempdir, 'x.txt')
        res = runner.run_data_store(action_file, 'fetch', 'templates', '1')
        self.assertEqual(2, res)
        self.assertEqual(
            [
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
                [
                    '--document=templates',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )
