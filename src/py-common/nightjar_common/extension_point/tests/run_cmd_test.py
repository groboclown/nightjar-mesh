
"""
Test the run_cmd module.
"""

from typing import List, Tuple, Union
import unittest
import os
from .. import run_cmd


class RunCmdTest(unittest.TestCase):
    """Test the run_cmd functions."""

    def setUp(self) -> None:
        self._env = dict(os.environ)

    def tearDown(self) -> None:
        existing = list(os.environ.keys())
        for key in existing:
            if key not in self._env:
                del os.environ[key]
        for key, value in self._env.items():
            os.environ[key] = value

    def test_get_env_executable_cmd__no_value(self) -> None:
        """Test get_env_executable_cmd with no env value set."""
        if 'blah_blah_blah' in os.environ:
            del os.environ['blah_blah_blah']  # pragma no cover

        try:
            run_cmd.get_env_executable_cmd('blah_blah_blah')
            self.fail("Did not raise exception")  # pragma no cover
        except Exception as err:  # pylint: disable=W0703
            self.assertEqual("Exception('No environment variable `blah_blah_blah`')", repr(err))

    def test_get_env_executable_cmd__not_found(self) -> None:
        """Test get_env_executable_cmd with a non-executable file."""
        os.environ['blah_blah_blah'] = '/this/is/not-an-executable-file.txt'
        self.assertFalse(os.path.isfile(os.environ['blah_blah_blah']))

        try:
            run_cmd.get_env_executable_cmd('blah_blah_blah')
        except Exception as err:  # pylint: disable=W0703
            self.assertEqual(
                "Exception('No such executable: "
                "/this/is/not-an-executable-file.txt (from environment variable blah_blah_blah)')",
                repr(err),
            )

    def test_get_env_executable_cmd__parts_parsed(self) -> None:
        """Test get_env_executable_cmd with a list of command arguments."""
        os.environ['blah_blah_blah'] = '/bin/ls -lA /tmp "/tmp/some file.txt"'
        self.assertTrue(os.path.isfile('/bin/ls'))

        result = run_cmd.get_env_executable_cmd('blah_blah_blah')
        self.assertEqual(
            ['/bin/ls', '-lA', '/tmp', '/tmp/some file.txt'],
            list(result),
        )

    def test_run_with_backoff__no_retry(self) -> None:
        """Test run_with_backoff with no retry required."""
        mock = BackoffMock(self, [0], [False])
        result = run_cmd.run_with_backoff(
            mock.runner_callback,
            mock.requires_retry_callback,
            12, 12.0,
            mock.sleep_func,
        )
        self.assertEqual(0, result)
        mock.next_runner_callback()
        mock.next_requires_retry_callback(0)
        mock.at_end()

    def test_run_with_backoff__maximum_time_maximum_retries(self) -> None:
        """Test run_with_backoff with no retry required."""
        mock = BackoffMock(
            self,
            [1, 2, 3],
            [True, True, True],
        )
        result = run_cmd.run_with_backoff(
            mock.runner_callback,
            mock.requires_retry_callback,
            3, 2.04,
            mock.sleep_func,
        )
        self.assertEqual(3, result)
        mock.next_runner_callback()
        mock.next_requires_retry_callback(1)
        mock.next_sleep_func(2.0)
        mock.next_runner_callback()
        mock.next_requires_retry_callback(2)
        mock.next_sleep_func(2.04)
        mock.next_runner_callback()
        mock.next_requires_retry_callback(3)
        mock.at_end()


class BackoffMock:
    """Mock class for recording callbacks."""
    def __init__(
            self, tester: unittest.TestCase, runner_responses: List[int],
            retry_responses: List[bool],
    ) -> None:
        self.calls: List[Tuple[str, Union[float, int]]] = []
        self._runner_responses = runner_responses
        self._retry_responses = retry_responses
        self._tester = tester

    def next_runner_callback(self) -> None:
        """Asserts the next call was to the runner."""
        self._tester.assertTrue(len(self.calls) > 0)
        name, _ = self.calls.pop(0)
        self._tester.assertEqual('runner_callback', name)

    def next_requires_retry_callback(self, expected: int) -> None:
        """Asserts the next call was to the retry check."""
        self._tester.assertTrue(len(self.calls) > 0)
        name, arg = self.calls.pop(0)
        self._tester.assertEqual('requires_retry_callback', name)
        self._tester.assertEqual(expected, arg)

    def next_sleep_func(self, expected: float) -> None:
        """Asserts the next call was to the sleep function."""
        self._tester.assertTrue(len(self.calls) > 0)
        name, arg = self.calls.pop(0)
        self._tester.assertEqual('sleep_func', name)
        self._tester.assertAlmostEqual(expected, arg, 4)

    def at_end(self) -> None:
        """Asserts there are no more calls."""
        self._tester.assertEqual([], self.calls)

    def runner_callback(self) -> int:
        """Callback for runner_callback argument."""
        self.calls.append(('runner_callback', 0,))
        self._tester.assertTrue(len(self._runner_responses) > 0)
        return self._runner_responses.pop(0)

    def requires_retry_callback(self, code: int) -> bool:
        """Callback for requires_retry_callback"""
        self.calls.append(('requires_retry_callback', code,))
        self._tester.assertTrue(len(self._retry_responses) > 0)
        return self._retry_responses.pop(0)

    def sleep_func(self, sleep_time: float) -> None:
        """Callback for sleep_func"""
        self.calls.append(('sleep_func', sleep_time,))
