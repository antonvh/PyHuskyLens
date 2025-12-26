#!/usr/bin/env python3
"""
PyHuskyLens SPIKE Installer Generator
Generates install_pyhuskylens.py for SPIKE Prime / MINDSTORMS Robot Inventor
Cross-compiles Python files to .mpy format for better performance

Usage:
    source .venv/bin/activate  # Activate venv first
    python3 create_installer.py
"""

import binascii
from datetime import datetime
import hashlib
import os
import sys
import tempfile
from pathlib import Path

# Configuration
SCRIPT_DIR = Path(__file__).parent
LIB_DIR = SCRIPT_DIR.parent / "pyhuskylens"
MPY_DIR = SCRIPT_DIR / "mpy"  # Temporary directory for .mpy files
BASE_INSTALLER = SCRIPT_DIR / "base_installer.py"
OUTPUT_INSTALLER = SCRIPT_DIR / "install_pyhuskylens.py"
CHUNK_SIZE = 256  # Base64 chunk size for hub memory efficiency

# Files to skip (RPi-specific, tests, cache, etc.)
SKIP_FILES = {
    "__pycache__",
    "rpi.py",  # Skip Raspberry Pi module
    ".DS_Store",
    ".pyc",
}

# mpy-cross compilation settings
COMPILE_TO_MPY = True
MPY_ARCH = "armv6m"  # SPIKE Prime / Robot Inventor use ARM Cortex-M0+
MPY_OPTIMIZATION = 0  # 0=none, 1=basic, 2=aggressive (0 for better compatibility)


def should_skip(filename):
    """Check if file should be skipped."""
    return any(skip in filename for skip in SKIP_FILES)


def compile_to_mpy(py_file_path):
    """Compile Python file to .mpy using mpy-cross."""
    
    from mpy_cross_v5 import mpy_cross_compile, Arch

    # Ensure mpy directory exists
    MPY_DIR.mkdir(exist_ok=True)

    # Create output .mpy file in temp directory
    mpy_filename = py_file_path.stem + ".mpy"
    mpy_file_path = MPY_DIR / mpy_filename

    # Run mpy-cross compilation
    with open(py_file_path, "r") as f:
        in_content = f.read()
    proc, mpy = mpy_cross_compile(mpy_file_path, in_content, optimization_level=0, arch=Arch.ARMV6)
    # proc = run(*args)
    # Wait for compilation to complete
    # proc.wait()

    if proc.returncode != 0:
        raise Exception(f"mpy-cross failed with code {proc.returncode}")
    
    return mpy, mpy_filename


def read_and_encode_file(file_path, compile_mpy=True):
    """Read file, optionally compile to .mpy, and encode as base64 chunks with hash."""
    # Compile Python files to .mpy if enabled
    if compile_mpy and file_path.suffix == ".py" and COMPILE_TO_MPY:
        print(f"Compiling: {file_path.name} → .mpy")
        content, output_name = compile_to_mpy(file_path)
    else:
        # Read file as-is
        with open(file_path, "rb") as f:
            content = f.read()
        output_name = file_path.name

    # Calculate hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Split into chunks and encode
    chunks = []
    for i in range(0, len(content), CHUNK_SIZE):
        chunk = content[i : i + CHUNK_SIZE]
        encoded_chunk = binascii.b2a_base64(chunk).decode("utf-8")
        chunks.append(encoded_chunk)

    print(f"  → {len(chunks)} chunks ({len(content)} bytes), hash: {file_hash[:16]}...")
    return output_name, tuple(chunks), file_hash


def scan_files(directory):
    """Recursively scan directory for Python files."""
    encoded_files = []

    for item in sorted(directory.iterdir()):
        if should_skip(item.name):
            continue

        rel_path = item.relative_to(LIB_DIR)

        if item.is_dir():
            # Add directory marker
            encoded_files.append((str(rel_path), "dir", ""))
            # Recursively scan subdirectory
            encoded_files.extend(scan_files(item))

        elif item.suffix == ".py":
            # Compile and encode Python file
            output_name, chunks, file_hash = read_and_encode_file(item)
            # Use .mpy extension in the target path if compiled
            target_name = (
                str(rel_path.with_suffix(".mpy")) if COMPILE_TO_MPY else str(rel_path)
            )
            encoded_files.append((target_name, chunks, file_hash))

    return encoded_files


def generate_installer():
    """Generate the installer script."""
    print("=" * 60)
    print("PyHuskyLens SPIKE Installer Generator")
    print("Compiling to .mpy format" if COMPILE_TO_MPY else "Using .py format")
    print("=" * 60)

    # Ensure temp mpy directory exists
    if COMPILE_TO_MPY:
        MPY_DIR.mkdir(exist_ok=True)

    # Check if source directory exists
    if not LIB_DIR.exists():
        print(f"ERROR: Library directory not found: {LIB_DIR}")
        sys.exit(1)

    # Check if base installer template exists
    if not BASE_INSTALLER.exists():
        print(f"ERROR: Base installer not found: {BASE_INSTALLER}")
        sys.exit(1)

    # Scan and encode files
    print(f"\nScanning: {LIB_DIR}")
    print(f"Architecture: {MPY_ARCH}, Optimization: O{MPY_OPTIMIZATION}\n")
    encoded_files = scan_files(LIB_DIR)

    if not encoded_files:
        print("ERROR: No files found to include!")
        sys.exit(1)

    print(f"\nTotal files: {len(encoded_files)}")

    # Read base installer template
    with open(BASE_INSTALLER, "r") as f:
        template = f.read()

    # Replace placeholder with encoded data
    installer_code = template.replace(
        "encoded = {}", f"# Compiled date: {datetime.now()}\nencoded = {repr(tuple(encoded_files))}"
    )
    
    # Write output installer
    with open(OUTPUT_INSTALLER, "w") as f:
        f.write(installer_code)

    file_size_kb = OUTPUT_INSTALLER.stat().st_size / 1024

    print("\n" + "=" * 60)
    print(f"SUCCESS! Installer created: {OUTPUT_INSTALLER.name}")
    print(f"Format: .mpy (compiled)" if COMPILE_TO_MPY else "Format: .py (source)")
    print(f"Size: {file_size_kb:.1f} KB")
    print("\nInstructions:")
    print("1. Open the SPIKE/MINDSTORMS app")
    print("2. Create a new empty project")
    print("3. Copy the contents of install_pyhuskylens.py")
    print("4. Paste into the project")
    print("5. Run to install PyHuskyLens on your hub")
    print("=" * 60)

    # Clean up temporary mpy directory
    if COMPILE_TO_MPY and MPY_DIR.exists():
        import shutil

        shutil.rmtree(MPY_DIR)
        print(f"\nCleaned up temporary directory: {MPY_DIR}")


if __name__ == "__main__":
    generate_installer()
