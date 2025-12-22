"""Pytest configuration and fixtures."""

import sys
import os

# Add mock micropython module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Add parent directory to path for importing pyhuskylens
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
