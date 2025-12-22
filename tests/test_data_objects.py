"""Test data objects (Block, Arrow, etc.)."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pyhuskylens.pyhuskylens import Arrow, Block


class TestArrow:
    """Test Arrow class."""

    def test_arrow_creation(self):
        """Test creating an Arrow object."""
        arrow = Arrow(10, 20, 30, 40, 1)
        assert arrow.x_tail == 10
        assert arrow.y_tail == 20
        assert arrow.x_head == 30
        assert arrow.y_head == 40
        assert arrow.ID == 1
        assert arrow.type == "ARROW"

    def test_arrow_direction_calculation(self):
        """Test arrow direction calculation."""
        # Horizontal arrow pointing right (atan2 uses y,x so this is -90°)
        arrow = Arrow(0, 0, 100, 0, 1)
        assert abs(arrow.direction - (-90)) < 1

        # Vertical arrow pointing up
        arrow = Arrow(0, 100, 0, 0, 1)
        assert abs(arrow.direction - 0) < 1

        # Diagonal arrow (down-right is -135°)
        arrow = Arrow(0, 0, 100, 100, 1)
        assert abs(arrow.direction - (-135)) < 1

    def test_arrow_learned(self):
        """Test arrow learned property."""
        arrow = Arrow(0, 0, 10, 10, 1)
        assert arrow.learned is True

        arrow = Arrow(0, 0, 10, 10, 0)
        assert arrow.learned is False

    def test_arrow_str(self):
        """Test arrow string representation."""
        arrow = Arrow(10, 20, 30, 40, 5)
        str_repr = str(arrow)
        assert "Arrow" in str_repr
        assert "10" in str_repr
        assert "20" in str_repr
        assert "30" in str_repr
        assert "40" in str_repr
        assert "5" in str_repr


class TestBlock:
    """Test Block class."""

    def test_block_creation(self):
        """Test creating a Block object."""
        block = Block(100, 120, 50, 60, 2)
        assert block.x == 100
        assert block.y == 120
        assert block.width == 50
        assert block.height == 60
        assert block.ID == 2
        assert block.type == "BLOCK"

    def test_block_learned(self):
        """Test block learned property."""
        block = Block(100, 120, 50, 60, 3)
        assert block.learned is True

        block = Block(100, 120, 50, 60, 0)
        assert block.learned is False

    def test_block_str(self):
        """Test block string representation."""
        block = Block(100, 120, 50, 60, 7)
        str_repr = str(block)
        assert "Block" in str_repr
        assert "100" in str_repr
        assert "120" in str_repr
        assert "50" in str_repr
        assert "60" in str_repr
        assert "7" in str_repr

    def test_block_default_attributes(self):
        """Test block default attributes."""
        block = Block(100, 120, 50, 60, 1)
        assert block.confidence == 0
        assert block.name == ""
        assert block.content == ""
