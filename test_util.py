import unittest
import un_util
import math

"""
assert:
Equal      | NotEqual
True       | False
Is         | IsNot
IsNone     | IsNotNone
In         | NotIn
IsInstance | NotIsInstance

"""

class TestUtil(unittest.TestCase):

    def test_remove_month(self):
        result = un_util.strip_date('December')
        self.assertEqual(result, '')

        result = un_util.strip_date('aug')
        self.assertEqual(result, '')
        return

    def test_example_dates(self):
        result = un_util.strip_date('2021 - 8') # UNFI
        self.assertEqual(result, '-')

        result = un_util.strip_date('Cases   2021/8') # Momentum
        self.assertEqual(result, 'Cases')

        result = un_util.strip_date('Units Aug') # Eagle Rock
        self.assertEqual(result, 'Units')

        result = un_util.strip_date('Case Equiv 2021 08') # Craft Collective
        self.assertEqual(result, 'Case Equiv')
        return

    def test_unnamed_cols(self):
        columns = ['col0', 'col1', 'Unnamed: 1', 'col2', 'Unnamed: 2', 'Unnamed: 3']
        result = un_util.remove_unnamed_columns(columns)
        self.assertEqual(result, ['col0', 'col1', '', 'col2'])

        columns = ['col0', 'col1', 'Unnamed: 1', 'col2', math.nan, 'Unnamed: 3']
        result = un_util.remove_unnamed_columns(columns)
        self.assertEqual(result, ['col0', 'col1', '', 'col2'])

        columns = ['col0', 'col1', 'Unnamed: 1', 'col2']
        result = un_util.remove_unnamed_columns(columns)
        self.assertEqual(result, ['col0', 'col1', '', 'col2'])

        columns = ['col0', 'col1', 'col2']
        result = un_util.remove_unnamed_columns(columns)
        self.assertEqual(result, ['col0', 'col1', 'col2'])
        return

    def test_phone(self):
        result = un_util.standardize_phone('1-763_242/9365')
        self.assertEqual(result, '763-242-9365')
        return


if __name__ == '__main__':
    unittest.main()
