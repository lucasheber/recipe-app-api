"""
Sample tests
"""

from django.test import SimpleTestCase

from app import calc

class CalcTests(SimpleTestCase):
    """Test the calc module."""

    def test_add_numbers(self):
        """Test adding number together."""
        res = calc.add(5, 5)

        self.assertEqual(res, 10)

    def test_subtract_numbers(self):
        """Test subtracting number."""
        res = calc.sub(10, 8)

        self.assertEqual(res, 2)