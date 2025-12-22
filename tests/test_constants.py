"""Test constants and enums."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyhuskylens.pyhuskylens import (
    ALGORITHM_FACE_RECOGNITION,
    ALGORITHM_OBJECT_TRACKING,
    ALGORITHM_OBJECT_RECOGNITION,
    ALGORITHM_LINE_TRACKING,
    ALGORITHM_COLOR_RECOGNITION,
    ALGORITHM_TAG_RECOGNITION,
    ALGORITHM_OBJECT_CLASSIFICATION,
    ALGORITHM_OCR,
    ALGORITHM_LICENSE_RECOGNITION,
    ALGORITHM_QR_CODE_RECOGNITION,
    ALGORITHM_BARCODE_RECOGNITION,
    ALGORITHM_FACE_EMOTION_RECOGNITION,
    ALGORITHM_POSE_RECOGNITION,
    ALGORITHM_HAND_RECOGNITION,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_RED,
    COLOR_GREEN,
    COLOR_BLUE,
    COLOR_YELLOW,
    BLOCKS,
    ARROWS,
    FACES,
    HANDS,
    POSES,
    FRAME,
)


def test_algorithm_constants():
    """Test that algorithm constants are defined correctly."""
    assert ALGORITHM_FACE_RECOGNITION == 1
    assert ALGORITHM_OBJECT_TRACKING == 2
    assert ALGORITHM_OBJECT_RECOGNITION == 3
    assert ALGORITHM_LINE_TRACKING == 4
    assert ALGORITHM_COLOR_RECOGNITION == 5
    assert ALGORITHM_TAG_RECOGNITION == 6
    assert ALGORITHM_OBJECT_CLASSIFICATION == 7
    assert ALGORITHM_OCR == 8
    assert ALGORITHM_LICENSE_RECOGNITION == 9
    assert ALGORITHM_QR_CODE_RECOGNITION == 10
    assert ALGORITHM_BARCODE_RECOGNITION == 11
    assert ALGORITHM_FACE_EMOTION_RECOGNITION == 12
    assert ALGORITHM_POSE_RECOGNITION == 13
    assert ALGORITHM_HAND_RECOGNITION == 14


def test_color_constants():
    """Test that color constants are defined correctly."""
    assert COLOR_BLACK == 0
    assert COLOR_WHITE == 1
    assert COLOR_RED == 2
    assert COLOR_GREEN == 3
    assert COLOR_BLUE == 4
    assert COLOR_YELLOW == 5


def test_result_dict_keys():
    """Test that result dictionary keys are defined correctly."""
    assert BLOCKS == "blocks"
    assert ARROWS == "arrows"
    assert FACES == "faces"
    assert HANDS == "hands"
    assert POSES == "poses"
    assert FRAME == "frame"
