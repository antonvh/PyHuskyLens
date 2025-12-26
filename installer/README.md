# PyHuskyLens SPIKE Installer

This directory contains scripts to generate an installer for SPIKE Prime and MINDSTORMS Robot Inventor hubs.

**Note:** Python files are cross-compiled to `.mpy` format for better performance and smaller file size.

## Quick Start

### Generate the Installer

On your computer (Mac/Linux/Windows with Python):

```bash
cd /path/to/PyHuskyLens
source .venv/bin/activate  # Activate virtual environment
cd installer
python3 create_installer.py
```

This will create `install_pyhuskylens.py` (~21KB file, .mpy compiled).

### Install on Hub

1. Open SPIKE 2.0 LEGACY or MINDSTORMS Robot Inventor app
2. **REBOOT your hub first** (important!)
3. Create a new empty Python project
4. Open `install_pyhuskylens.py` in a text editor
5. Copy all the contents
6. Paste into your empty project
7. Open the console (click `[>_]` button at bottom)
8. Click Run/Play button
9. Wait for installation to complete (text will scroll in console)

### Use PyHuskyLens

After installation, use in your projects:

```python
from pyhuskylens import *

# I2C Example (SPIKE/MINDSTORMS)
from hub import port

i2c = port.E  # Use the port your HuskyLens is connected to
hl = HuskyLens(i2c)

if hl.knock():
    print("Connected!")
    hl.set_alg(ALGORITHM_OBJECT_RECOGNITION)
    blocks = hl.get_blocks()
    print(f"Found {len(blocks)} objects")
```

## Files

- `create_installer.py` - Generator script (run on computer, requires venv)
- `base_installer.py` - Template for the installer
- `install_pyhuskylens.py` - Generated installer (paste into hub, ~21KB .mpy compiled)
- `mpy/` - Temporary directory (auto-deleted after generation)

## How It Works

1. **Generator** (`create_installer.py`):
   - Reads all Python files from `../pyhuskylens/` directory
   - Skips Raspberry Pi specific files (`rpi.py`)
   - **Cross-compiles** files to `.mpy` using mpy-cross (ARM Cortex-M0+ architecture)
   - Encodes .mpy files as base64 chunks (256 bytes each)
   - Generates SHA256 hashes for verification
   - Creates installer script with embedded data

2. **Installer** (`install_pyhuskylens.py`):
   - Runs on the SPIKE/MINDSTORMS hub
   - Creates `/projects/pyhuskylens/` directory
   - Decodes and writes each `.mpy` file
   - Verifies file integrity with hash checks
   - Reports success or errors

## Notes

- **Requires venv activation** to access mpy-cross compiler
- The installer excludes `rpi.py` (Raspberry Pi specific)
- `.mpy` files are ~60% smaller than `.py` files
- Generated installer is self-contained (no dependencies)
- Works with SPIKE Prime and MINDSTORMS Robot Inventor
- Compatible with SPIKE 2.0 LEGACY and MINDSTORMS apps

## Troubleshooting

**Installation fails or stops:**

- Make sure you rebooted the hub first
- Check that you opened the console before running
- Ensure you copied the ENTIRE installer file

**Import errors after installation:**

- Installation may have failed - check console for errors
- Try reinstalling after rebooting the hub

**"No space" errors:**

- Delete old projects from hub to free up space
- The library needs ~50KB of storage
