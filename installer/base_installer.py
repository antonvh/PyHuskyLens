#### PyHuskyLens Installer for SPIKE Prime / MINDSTORMS ####
#
# HOW TO USE:
# 1. REBOOT your hub first!
# 2. Paste this script into an empty Python project in the SPIKE/MINDSTORMS app
# 3. Open the console: [>_] button at the bottom of the screen
# 4. Click the 'run/play' button
# 5. WAIT! The play button will stop spinning, but the script is still running
# 6. When text stops scrolling in the console, installation is complete
# 7. Use PyHuskyLens in your projects with: from pyhuskylens import *
#
# Works with SPIKE 2.0 LEGACY app and LEGO MINDSTORMS Robot Inventor app

from ubinascii import hexlify, a2b_base64
from uhashlib import sha256
from os import mkdir
import gc

encoded = {}

print("=" * 50)
print("PyHuskyLens Installer")
print("=" * 50)

# Create main directory
try:
    mkdir("/projects/pyhuskylens")
    print("Created /projects/pyhuskylens/")
except:
    print("/projects/pyhuskylens/ already exists")

error = False

for file_name, code, expected_hash in encoded:
    target_path = "/projects/pyhuskylens/" + file_name

    # Handle directories
    if code == "dir":
        try:
            mkdir(target_path)
            print("Created directory:", target_path)
        except:
            pass  # Directory likely exists
        continue

    # Write file from base64 chunks
    try:
        with open(target_path, "wb") as f:
            for chunk in code:
                f.write(a2b_base64(chunk))
        del code
        gc.collect()
        print("Installed:", file_name)
    except Exception as e:
        print("ERROR writing", file_name, ":", str(e))
        error = True
        continue

    # Verify file integrity with hash
    try:
        with open(target_path, "rb") as f:
            m = sha256()
            while True:
                chunk = f.read(256)
                if not chunk:
                    break
                m.update(chunk)

        actual_hash = hexlify(m.digest()).decode()
        gc.collect()

        if actual_hash != expected_hash:
            print("ERROR: Hash mismatch for", file_name)
            error = True
        else:
            print("  Verified:", file_name)
    except Exception as e:
        print("ERROR verifying", file_name, ":", str(e))
        error = True

del encoded
gc.collect()

print("=" * 50)
if not error:
    print("SUCCESS! PyHuskyLens installed!")
    print("Use: from projects.pyhuskylens import PyHuskyLens")
else:
    print("FAILED! Some files had errors")
print("=" * 50)
