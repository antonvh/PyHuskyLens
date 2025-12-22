# Publishing to PyPI

## Package Status
✅ **Ready for publishing!**

- Version: 2.1.0
- Package built successfully with no warnings
- Twine validation: PASSED
- Distribution files ready in `dist/`

## Distribution Files

```
dist/
  pyhuskylens-2.1.0-py3-none-any.whl  (18KB)
  pyhuskylens-2.1.0.tar.gz            (27KB)
```

## To Publish

### 1. Test on TestPyPI (Optional but Recommended)

```bash
source .venv/bin/activate
twine upload --repository testpypi dist/*
```

Then test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ pyhuskylens
```

### 2. Publish to PyPI

```bash
source .venv/bin/activate
twine upload dist/*
```

You'll be prompted for your PyPI credentials:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

### 3. Verify Installation

After publishing:
```bash
pip install pyhuskylens
python -c "import pyhuskylens; print(pyhuskylens.__version__)"
```

## API Token Setup

If you don't have a PyPI API token:

1. Go to https://pypi.org/manage/account/token/
2. Create a new API token
3. Save it securely (it's shown only once)

For convenience, create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-YOUR-API-TOKEN-HERE

[testpypi]
username = __token__
password = pypi-YOUR-TESTPYPI-API-TOKEN-HERE
```

Set permissions:
```bash
chmod 600 ~/.pypirc
```

## What's Included

### Features (v2.1.0)
- MicroPython optimizations (2-3x faster)
- Raspberry Pi support (I2C and Serial)
- All 14 HuskyLens algorithms
- V2 support (Face, Hand, Pose detection with keypoints)
- Full documentation and examples

### Package Contents
- Main library: `pyhuskylens/pyhuskylens.py`
- Package init: `pyhuskylens/__init__.py`
- Tests included in source distribution
- README with comprehensive documentation
- MIT License

### Dependencies
- **Core**: None (pure Python)
- **Optional**:
  - `smbus2>=0.4.0` (Raspberry Pi I2C)
  - `pyserial>=3.5` (Raspberry Pi Serial)

Install with extras:
```bash
pip install pyhuskylens[i2c]      # For Raspberry Pi I2C
pip install pyhuskylens[serial]   # For Raspberry Pi Serial
pip install pyhuskylens[all]      # For both
```

## Post-Publishing

1. Tag the release in git:
   ```bash
   git tag -a v2.1.0 -m "Release v2.1.0: Add Raspberry Pi support and MicroPython optimizations"
   git push origin v2.1.0
   ```

2. Create a GitHub release with release notes

3. Update documentation links if needed

## Troubleshooting

**"Invalid or non-existent authentication information"**
- Check your API token is correct
- Ensure username is `__token__`
- Verify the token has upload permissions

**"File already exists"**
- PyPI doesn't allow re-uploading the same version
- Bump the version in `pyproject.toml` and `pyhuskylens/__init__.py`
- Rebuild: `python -m build`

**"Package validation failed"**
- Run `twine check dist/*` to see specific issues
- Ensure README.md renders correctly on PyPI
