
import unittest
from ..params import ParamDef


class ParamDefTest(unittest.TestCase):
    def test_required_not_given(self) -> None:
        pd = ParamDef('n1', 'N1', ['n1'], '', None, str, True)
        try:
            pd.get_value({})
            self.fail('Did not raise ValueError.')
        except ValueError:
            pass

    def test_required_not_given_with_default(self) -> None:
        pd = ParamDef('n1', 'N1', ['n1'], '', 'xyz', str, True)
        self.assertEqual(pd.get_value({}), 'xyz')

    def test_not_required_not_given(self) -> None:
        pd = ParamDef('n1', 'N1', ['n1'], '', None, str, False)
        self.assertIsNone(pd.get_value({}))
