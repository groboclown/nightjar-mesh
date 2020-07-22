
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
from ..exceptions import ExtensionPointTooManyRetries, ExtensionPointRuntimeError
from ...fastjsonschema_replacement import JsonSchemaException


class DataStoreRunnerTest(unittest.TestCase):
    """Tests the DataStoreRunner class"""

    def setUp(self) -> None:
        self._tempdir = tempfile.mkdtemp()

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
        res = runner.run_data_store_once(action_file, 'fetch', 'template', '1')
        self.assertEqual(0, res)
        self.assertEqual(
            [[
                '--activity=template',
                '--action=fetch',
                '--previous-document-version=1',
                '--action-file=' + action_file,
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__success(self) -> None:
        """Tests the commit_templates with successful result."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        runner.commit_templates({
            'version': 'v1',
            'activity': 'template',
            'gateway-templates': [],
            'service-templates': [],
        })
        self.assertEqual(
            [[
                '--activity=template',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-templates.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__failure(self) -> None:
        """Tests the commit_templates with invoke failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([2]), self._tempdir)
        try:
            runner.commit_templates({
                'version': 'v1',
                'activity': 'template',
                'gateway-templates': [],
                'service-templates': [],
            })
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data store', err.source)
            self.assertEqual('commit templates', err.action)
            self.assertEqual(2, err.exit_code)
        self.assertEqual(
            [[
                '--activity=template',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-templates.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__retry_failure(self) -> None:
        """Tests fetch_templates with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 1
        try:
            runner.commit_templates({
                'version': 'v1',
                'activity': 'template',
                'gateway-templates': [],
                'service-templates': [],
            })
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data store', err.source)
            self.assertEqual('commit templates', err.action)
        self.assertEqual(
            [[
                '--activity=template',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-templates.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_templates__validation_error(self) -> None:
        """Tests the commit_templates with data validation errors."""
        runner = data_store.DataStoreRunner([], self._tempdir)
        try:
            runner.commit_templates({})
            self.fail('Should have raised an exception')  # pragma no cover
        except JsonSchemaException:
            pass

    def test_commit_configurations__success(self) -> None:
        """Tests the commit_configurations with successful result."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        runner.commit_configurations({
            'version': 'v1',
            'activity': 'configuration',
            'gateway-configurations': [],
            'service-configurations': [],
        })
        self.assertEqual(
            [[
                '--activity=configuration',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-configs.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_configurations__failure(self) -> None:
        """Tests the commit_configurations with invoke failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([2]), self._tempdir)
        try:
            runner.commit_configurations({
                'version': 'v1',
                'activity': 'configuration',
                'gateway-configurations': [],
                'service-configurations': [],
            })
            self.fail('Should have raised an exception')  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data store', err.source)
            self.assertEqual('commit configurations', err.action)
            self.assertEqual(2, err.exit_code)
        self.assertEqual(
            [[
                '--activity=configuration',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-configs.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_configurations__retry_failure(self) -> None:
        """Tests fetch_templates with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 1
        try:
            runner.commit_configurations({
                'version': 'v1',
                'activity': 'configuration',
                'gateway-configurations': [],
                'service-configurations': [],
            })
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data store', err.source)
            self.assertEqual('commit configurations', err.action)
        self.assertEqual(
            [[
                '--activity=configuration',
                '--action=commit',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'commit-configs.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_commit_configurations__validation_error(self) -> None:
        """Tests the commit_configurations with data validation errors."""
        runner = data_store.DataStoreRunner([], self._tempdir)
        try:
            runner.commit_configurations({})
            self.fail('Should have raised an exception')  # pragma no cover
        except JsonSchemaException:
            pass

    def test_fetch_templates__success(self) -> None:
        """Tests fetch_templates with successful return and data validation."""
        expected_data = {
            'version': 'v1',
            'commit-version': '1',
            'activity': 'template',
            'gateway-templates': [],
            'service-templates': [],
        }
        with open(os.path.join(self._tempdir, 'fetch-templates-new.json'), 'w') as f:
            json.dump(expected_data, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        data = runner.fetch_templates()
        self.assertEqual(expected_data, data)
        self.assertEqual(
            [[
                '--activity=template',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__repeated_same_version(self) -> None:
        """Tests fetch_templates with same version return code."""
        expected_data = {
            'version': 'v1',
            'commit-version': 'x1x',
            'activity': 'template',
            'gateway-templates': [],
            'service-templates': [],
        }
        with open(os.path.join(self._tempdir, 'fetch-templates-new.json'), 'w') as f:
            json.dump(expected_data, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0, 30]), self._tempdir)

        # Make the call with no cached version.  The call will exit with 0.
        data = runner.fetch_templates()
        self.assertEqual(expected_data, data)
        self.assertFalse(os.path.isfile(os.path.join(self._tempdir, 'fetch-templates-new.json')))
        self.assertTrue(os.path.isfile(os.path.join(self._tempdir, 'fetch-templates.json')))

        # Make the call again with version x1x.  The call will exit with 3.
        data = runner.fetch_templates()
        self.assertEqual(expected_data, data)
        self.assertFalse(os.path.isfile(os.path.join(self._tempdir, 'fetch-templates-new.json')))
        self.assertTrue(os.path.isfile(os.path.join(self._tempdir, 'fetch-templates.json')))
        self.assertEqual(
            [
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                    '--api-version=1',
                ],
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=x1x',
                    '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
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
            runner.fetch_templates()
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointRuntimeError as err:
            self.assertEqual('data store', err.source)
            self.assertEqual('fetch template', err.action)
            self.assertEqual(1, err.exit_code)
        self.assertEqual(
            [[
                '--activity=template',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__retry_with_no_previous(self) -> None:
        """Tests fetch_templates with failure code."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([30]), self._tempdir)
        try:
            runner.fetch_templates()
            self.fail("Did not raise an exception")  # pragma no cover
        except RuntimeError as err:  # pylint: disable=W0703
            self.assertEqual(
                "RuntimeError('data store requested reuse of non-existent old version')",
                repr(err),
            )
        self.assertEqual(
            [[
                '--activity=template',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__retry_failure(self) -> None:
        """Tests fetch_templates with too-many retries."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([31, 31]), self._tempdir)
        runner.max_retry_wait_seconds = 0.1
        runner.max_retry_count = 2
        try:
            runner.fetch_templates()
            self.fail("Did not raise an exception")  # pragma no cover
        except ExtensionPointTooManyRetries as err:  # pylint: disable=W0703
            self.assertEqual('data store', err.source)
            self.assertEqual('fetch template', err.action)
        self.assertEqual(
            [
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                    '--api-version=1',
                ],
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=',
                    '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_templates__validation_error(self) -> None:
        """Tests fetch_templates with successful return and data validation."""
        with open(os.path.join(self._tempdir, 'fetch-templates-new.json'), 'w') as f:
            json.dump({"blah": "woo"}, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        try:
            runner.fetch_templates()
            self.fail("Did not raise an exception")  # pragma no cover
        except JsonSchemaException:
            pass
        self.assertEqual(
            [[
                '--activity=template',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'fetch-templates-new.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_fetch_configurations__success(self) -> None:
        """Tests fetch_templates with successful return and data validation."""
        expected_data = {
            'version': 'v1',
            'commit-version': '1',
            'activity': 'configuration',
            'gateway-configurations': [],
            'service-configurations': [],
        }
        with open(os.path.join(self._tempdir, 'fetch-configurations-new.json'), 'w') as f:
            json.dump(expected_data, f)
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(invoker.prepare_runnable([0]), self._tempdir)
        data = runner.fetch_configurations()
        self.assertEqual(expected_data, data)
        self.assertEqual(
            [[
                '--activity=configuration',
                '--action=fetch',
                '--previous-document-version=',
                '--action-file=' + os.path.join(self._tempdir, 'fetch-configurations-new.json'),
                '--api-version=1',
            ]],
            invoker.get_invoked_arguments(),
        )

    def test_runnable_with_backoff__error(self) -> None:
        """Ensures the backoff invocation, with an eventual error, works as expected."""
        invoker = RunnableInvoker(self._tempdir)
        runner = data_store.DataStoreRunner(
            invoker.prepare_runnable([31, 31, 2]),
            self._tempdir,
        )
        runner.max_retry_wait_seconds = 0.05
        action_file = os.path.join(self._tempdir, 'x.txt')
        res = runner.run_data_store(action_file, 'fetch', 'template', '1')
        self.assertEqual(2, res)
        self.assertEqual(
            [
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
                [
                    '--activity=template',
                    '--action=fetch',
                    '--previous-document-version=1',
                    '--action-file=' + action_file,
                    '--api-version=1',
                ],
            ],
            invoker.get_invoked_arguments(),
        )
