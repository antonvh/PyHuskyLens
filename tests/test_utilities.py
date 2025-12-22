"""Test utility functions."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyhuskylens.pyhuskylens import clamp_int


class TestClampInt:
    """Test clamp_int utility function."""

    def test_clamp_within_range(self):
        """Test that values within range are unchanged."""
        assert clamp_int(0) == 0
        assert clamp_int(50) == 50
        assert clamp_int(-50) == -50

    def test_clamp_above_max(self):
        """Test that values above max are clamped."""
        assert clamp_int(150) == 100
        assert clamp_int(1000) == 100

    def test_clamp_below_min(self):
        """Test that values below min are clamped."""
        assert clamp_int(-150) == -100
        assert clamp_int(-1000) == -100

    def test_clamp_at_boundaries(self):
        """Test boundary values."""
        assert clamp_int(100) == 100
        assert clamp_int(-100) == -100

    def test_clamp_custom_range(self):
        """Test custom min/max values."""
        assert clamp_int(50, min_val=0, max_val=100) == 50
        assert clamp_int(-10, min_val=0, max_val=100) == 0
        assert clamp_int(150, min_val=0, max_val=100) == 100

    def test_clamp_float_to_int(self):
        """Test that floats are converted to ints."""
        assert clamp_int(50.7) == 50
        assert clamp_int(-50.3) == -50
        assert isinstance(clamp_int(50.5), int)
