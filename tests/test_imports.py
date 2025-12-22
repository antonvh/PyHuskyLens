"""Test that all expected imports work."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_main_module_import():
    """Test that main module can be imported."""
    from pyhuskylens import pyhuskylens

    assert pyhuskylens is not None


def test_class_imports():
    """Test that main classes can be imported."""
    from pyhuskylens.pyhuskylens import (
        HuskyLensBase,
        HuskyLensI2C,
        HuskyLensSerial,
        HuskyLens,
    )

    assert HuskyLensBase is not None
    assert HuskyLensI2C is not None
    assert HuskyLensSerial is not None
    assert HuskyLens is not None


def test_data_class_imports():
    """Test that data classes can be imported."""
    from pyhuskylens.pyhuskylens import Arrow, Block

    assert Arrow is not None
    assert Block is not None


def test_algorithm_imports():
    """Test that algorithm constants can be imported."""
    from pyhuskylens.pyhuskylens import (
        ALGORITHM_FACE_RECOGNITION,
        ALGORITHM_OBJECT_TRACKING,
        ALGORITHM_OBJECT_RECOGNITION,
        ALGORITHM_LINE_TRACKING,
        ALGORITHM_COLOR_RECOGNITION,
        ALGORITHM_TAG_RECOGNITION,
        ALGORITHM_OBJECT_CLASSIFICATION,
    )

    assert all(
        [
            ALGORITHM_FACE_RECOGNITION,
            ALGORITHM_OBJECT_TRACKING,
            ALGORITHM_OBJECT_RECOGNITION,
            ALGORITHM_LINE_TRACKING,
            ALGORITHM_COLOR_RECOGNITION,
            ALGORITHM_TAG_RECOGNITION,
            ALGORITHM_OBJECT_CLASSIFICATION,
        ]
    )


def test_color_imports():
    """Test that color constants can be imported."""
    from pyhuskylens.pyhuskylens import (
        COLOR_BLACK,
        COLOR_WHITE,
        COLOR_RED,
        COLOR_GREEN,
        COLOR_BLUE,
        COLOR_YELLOW,
    )

    assert all(
        [
            COLOR_BLACK is not None,
            COLOR_WHITE is not None,
            COLOR_RED is not None,
            COLOR_GREEN is not None,
            COLOR_BLUE is not None,
            COLOR_YELLOW is not None,
        ]
    )


def test_dict_key_imports():
    """Test that dict key constants can be imported."""
    from pyhuskylens.pyhuskylens import (
        BLOCKS,
        ARROWS,
        FACES,
        HANDS,
        POSES,
        FRAME,
    )

    assert all([BLOCKS, ARROWS, FACES, HANDS, POSES, FRAME])


def test_utility_imports():
    """Test that utility functions can be imported."""
    from pyhuskylens.pyhuskylens import clamp_int

    assert clamp_int is not None
    assert callable(clamp_int)
