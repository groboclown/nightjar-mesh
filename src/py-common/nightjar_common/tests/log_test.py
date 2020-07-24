
"""
Test the log module.
"""

from typing import Callable
import unittest
import io
import sys
from .. import log


class LogTest(unittest.TestCase):
    """Test the log functions."""

    def setUp(self) -> None:
        self._orig_stderr = sys.stderr
        self._orig_model = log.EXECUTE_MODEL
        self._orig_debug = log.DEBUG_ON

    def tearDown(self) -> None:
        sys.stderr = self._orig_stderr
        log.EXECUTE_MODEL = self._orig_model
        log.DEBUG_ON = self._orig_debug

    def test_log(self) -> None:
        """Test the log method."""
        log.EXECUTE_MODEL = 'tuna'
        res = self._with_replace(lambda: log.log("x", "y {z}", z="abc"))
        self.assertEqual("[tuna :: x] y abc\n", res)

    def test_debug__disabled(self) -> None:
        """Test the debug function with debug disabled."""
        log.DEBUG_ON = False
        res = self._with_replace(lambda: log.debug("x"))
        self.assertEqual("", res)

    def test_debug__enabled(self) -> None:
        """Test the debug function with debug enabled."""
        log.EXECUTE_MODEL = 'marlin'
        log.DEBUG_ON = True
        res = self._with_replace(lambda: log.debug("x {y}", y="q"))
        self.assertEqual("[marlin :: DEBUG] x q\n", res)

    def test_warning(self) -> None:
        """Test the warning function."""
        log.EXECUTE_MODEL = 'koi'
        log.DEBUG_ON = False
        res = self._with_replace(lambda: log.warning('a {b}', b="c"))
        self.assertEqual("[koi :: WARN] a c\n", res)

    def _with_replace(self, callback: Callable[[], None]) -> str:
        new_err = io.StringIO()
        sys.stderr = new_err
        try:
            callback()
        finally:
            sys.stderr = self._orig_stderr
        return new_err.getvalue()
