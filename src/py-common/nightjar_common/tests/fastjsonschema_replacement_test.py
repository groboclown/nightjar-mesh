
"""Test the fastjsonschema_replacement module"""

import unittest
from .. import fastjsonschema_replacement


class JsonSchemaExceptionTest(unittest.TestCase):
    """Test the JsonSchemaException class"""

    def test_init_raise(self) -> None:
        """Test initialization and raising the exception."""
        try:
            raise fastjsonschema_replacement.JsonSchemaException('my message')
        except ValueError as err:
            self.assertEqual("JsonSchemaException('my message')", repr(err))
        else:
            self.fail("Did not raise the right error.")  # pragma no cover
