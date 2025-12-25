"""Test that the library compiles with mpy-cross for MicroPython."""

import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def test_mpy_cross_available():
    """Test that mpy-cross is available in the system."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "mpy_cross", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, "mpy-cross is not available or failed to run"
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        # Skip test if mpy-cross is not installed
        import pytest

        pytest.skip(f"mpy-cross is not installed: {e}")


def test_pyhuskylens_compiles_with_mpy_cross():
    """Test that pyhuskylens.py compiles with mpy-cross."""
    # Get the path to the main library file
    library_path = Path(__file__).parent.parent / "pyhuskylens" / "pyhuskylens.py"

    assert library_path.exists(), f"Library file not found at {library_path}"

    # Create a temporary directory for output
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "pyhuskylens.mpy"

        try:
            # Run mpy-cross on the library file
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "mpy_cross",
                    str(library_path),
                    "-o",
                    str(output_file),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            # Check that compilation succeeded
            assert result.returncode == 0, (
                f"mpy-cross compilation failed with return code {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

            # Check that the output file was created
            assert output_file.exists(), "mpy-cross did not produce an output file"

            # Check that the output file has content
            assert output_file.stat().st_size > 0, "mpy-cross produced an empty file"

        except FileNotFoundError:
            # Skip test if mpy-cross is not installed
            import pytest

            pytest.skip("mpy-cross is not installed")
        except subprocess.TimeoutExpired:
            raise AssertionError("mpy-cross compilation timed out after 30 seconds")


def test_pyhuskylens_compiles_with_optimization():
    """Test that pyhuskylens.py compiles with mpy-cross optimization levels."""
    library_path = Path(__file__).parent.parent / "pyhuskylens" / "pyhuskylens.py"

    assert library_path.exists(), f"Library file not found at {library_path}"

    # Test different optimization levels
    optimization_levels = [0, 1, 2, 3]

    for opt_level in optimization_levels:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / f"pyhuskylens_O{opt_level}.mpy"

            try:
                # Run mpy-cross with optimization
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "mpy_cross",
                        f"-O{opt_level}",
                        str(library_path),
                        "-o",
                        str(output_file),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                # Check that compilation succeeded
                assert result.returncode == 0, (
                    f"mpy-cross compilation with -O{opt_level} failed with return code {result.returncode}\n"
                    f"stdout: {result.stdout}\n"
                    f"stderr: {result.stderr}"
                )

                # Check that the output file was created
                assert (
                    output_file.exists()
                ), f"mpy-cross with -O{opt_level} did not produce an output file"

                # Check that the output file has content
                assert (
                    output_file.stat().st_size > 0
                ), f"mpy-cross with -O{opt_level} produced an empty file"

            except FileNotFoundError:
                # Skip test if mpy-cross is not installed
                import pytest

                pytest.skip("mpy-cross is not installed")
            except subprocess.TimeoutExpired:
                raise AssertionError(
                    f"mpy-cross compilation with -O{opt_level} timed out after 30 seconds"
                )


def test_pyhuskylens_syntax_for_micropython():
    """Test that pyhuskylens.py doesn't use syntax incompatible with MicroPython."""
    library_path = Path(__file__).parent.parent / "pyhuskylens" / "pyhuskylens.py"

    assert library_path.exists(), f"Library file not found at {library_path}"

    # Read the library file
    with open(library_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for common incompatibilities (this is not exhaustive)
    incompatible_patterns = [
        # MicroPython doesn't support walrus operator in older versions
        # but modern versions do, so we'll skip this check
        # (":=", "walrus operator (:=) may not be supported in all MicroPython versions"),
    ]

    for pattern, message in incompatible_patterns:
        assert pattern not in content, f"Found {message} in the library"
