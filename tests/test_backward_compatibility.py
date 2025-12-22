"""Test backward compatibility features."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyhuskylens.pyhuskylens import (
    BLOCKS,
    ARROWS,
    FACES,
    HANDS,
    POSES,
    FRAME,
    clamp_int,
)


def test_constant_exports():
    """Test that backward compatibility constants are exported."""
    # These should be available for import
    assert BLOCKS == "blocks"
    assert ARROWS == "arrows"
    assert FACES == "faces"
    assert HANDS == "hands"
    assert POSES == "poses"
    assert FRAME == "frame"


def test_clamp_int_export():
    """Test that clamp_int utility is exported."""
    assert callable(clamp_int)
    assert clamp_int(50) == 50


def test_dict_keys_are_strings():
    """Test that dict keys are strings for compatibility."""
    assert isinstance(BLOCKS, str)
    assert isinstance(ARROWS, str)
    assert isinstance(FACES, str)
    assert isinstance(HANDS, str)
    assert isinstance(POSES, str)
    assert isinstance(FRAME, str)
