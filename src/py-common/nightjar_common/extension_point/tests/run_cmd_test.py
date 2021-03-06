
"""
Test the run_cmd module.
"""

from typing import Dict, List, Tuple, Union
import unittest
import os
import platform
from .. import run_cmd
from ..errors import ConfigurationError


class RunCmdTest(unittest.TestCase):
    """Test the run_cmd functions."""

    def test_get_env_executable_cmd__no_value(self) -> None:
        """Test get_env_executable_cmd with no env value set."""
        env: Dict[str, str] = {}

        try:
            run_cmd.get_env_executable_cmd(env, 'blah_blah_blah')
            self.fail("Did not raise exception")  # pragma no cover
        except ConfigurationError as err:
            self.assertEqual('blah_blah_blah', err.source)
            self.assertEqual('environment variable not defined', err.problem)

    def test_get_env_executable_cmd__not_found(self) -> None:
        """Test get_env_executable_cmd with a non-executable file."""
        env = {'blah_blah_blah': '/this/is/not-an-executable-file.txt'}
        self.assertFalse(os.path.isfile(env['blah_blah_blah']))

        try:
            run_cmd.get_env_executable_cmd(env, 'blah_blah_blah')
        except ConfigurationError as err:
            self.assertEqual('blah_blah_blah', err.source)
            self.assertEqual(
                "No such executable: `/this/is/not-an-executable-file.txt`",
                err.problem,
            )

    @unittest.skipIf(
        platform.system() == 'Windows',
        "The code is written for Linux, and can't be correctly run from windows."
    )
    def test_get_env_executable_cmd__parts_parsed(self) -> None:
        """Test get_env_executable_cmd with a list of command arguments."""

        print(platform.system())

        cmd = '/bin/ls'
        env = {'blah_blah_blah': cmd + ' -lA /tmp "/tmp/some file.txt"'}
        self.assertTrue(os.path.isfile(cmd))

        result = run_cmd.get_env_executable_cmd(env, 'blah_blah_blah')
        self.assertEqual(
            [cmd, '-lA', '/tmp', '/tmp/some file.txt'],
            list(result),
        )

    def test_run_with_backoff__no_retry(self) -> None:
        """Test run_with_backoff with no retry required."""
        mock = BackoffMock(self, [0], [False])
        result = run_cmd.run_with_backoff(
            mock.runner_callback,
            12, 12.0,
            mock.sleep_func,
        )
        self.assertEqual(0, result)
        mock.next_runner_callback()
        mock.at_end()

    def test_run_with_backoff__maximum_time_maximum_retries(self) -> None:
        """Test run_with_backoff with no retry required."""
        mock = BackoffMock(
            self,
            [31, 31, 3],
            [True, True, True],
        )
        result = run_cmd.run_with_backoff(
            mock.runner_callback,
            3, 2.04,
            mock.sleep_func,
        )
        self.assertEqual(3, result)
        mock.next_runner_callback()
        mock.next_sleep_func(2.0)
        mock.next_runner_callback()
        mock.next_sleep_func(2.04)
        mock.next_runner_callback()
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

    def sleep_func(self, sleep_time: float) -> None:
        """Callback for sleep_func"""
        self.calls.append(('sleep_func', sleep_time,))
