# Environment Setup Guide

This guide explains how to set up a Python environment that works with all OCR and layout detection libraries used in this project.

## Python Version Compatibility

| Library | Python 3.10 | Python 3.11 | Python 3.12 | Python 3.13 |
|---------|-------------|-------------|-------------|-------------|
| EasyOCR | ✅ | ✅ | ✅ | ✅ |
| Surya OCR | ✅ | ✅ | ✅ | ✅ |
| PaddleOCR | ✅ | ✅ | ✅ | ✅* |
| Tesseract | ✅ | ✅ | ✅ | ✅ |
| DocLayout-YOLO | ✅ | ✅ | ✅ | ✅ |
| DocTR | ✅ | ✅ | ✅ | ✅ |

*PaddleOCR 3.x on Python 3.13 requires a workaround (setting `HUB_DATASET_ENDPOINT` environment variable before import).

**Recommended: Python 3.11** - Best compatibility with all libraries.

## Option 1: Using venv (Built-in)

### Windows (PowerShell)

```powershell
# Navigate to project directory
cd c:\Users\leolw\OneDrive\Documents\MSAIB\Capstone\eCourtDateOCR

# Create virtual environment with Python 3.11 (if available)
# If you have multiple Python versions, specify the path:
# py -3.11 -m venv venv
python -m venv venv

# Activate the environment
.\venv\Scripts\Activate

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

### Windows (Command Prompt)

```cmd
cd c:\Users\leolw\OneDrive\Documents\MSAIB\Capstone\eCourtDateOCR
python -m venv venv
venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Linux/macOS

```bash
cd /path/to/eCourtDateOCR
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Option 2: Using Conda

```bash
# Create conda environment with Python 3.11
conda create -n court-ocr python=3.11

# Activate environment
conda activate court-ocr

# Install dependencies
pip install -r requirements.txt
```

## Option 3: Using pyenv (for managing Python versions)

### Install pyenv (Windows - use pyenv-win)

```powershell
# Install pyenv-win via PowerShell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"

# Install Python 3.11
pyenv install 3.11.9
pyenv local 3.11.9

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate
pip install -r requirements.txt
```

## Verifying Installation

After setting up the environment, run this script to verify all libraries work:

```python
import sys
print(f"Python version: {sys.version}")

# Test EasyOCR
try:
    import easyocr
    print("✅ EasyOCR installed")
except ImportError as e:
    print(f"❌ EasyOCR: {e}")

# Test Surya
try:
    from surya.ocr import run_ocr
    print("✅ Surya OCR installed")
except ImportError as e:
    print(f"❌ Surya OCR: {e}")

# Test PaddleOCR (with Python 3.13 workaround)
try:
    import os
    os.environ.setdefault('HUB_DATASET_ENDPOINT', 'https://modelscope.cn/api/v1/datasets')
    from paddleocr import PaddleOCR
    print("✅ PaddleOCR installed")
except ImportError as e:
    print(f"❌ PaddleOCR: {e}")

# Test DocLayout-YOLO
try:
    from doclayout_yolo import YOLOv10
    print("✅ DocLayout-YOLO installed")
except ImportError as e:
    print(f"❌ DocLayout-YOLO: {e}")

# Test DocTR
try:
    from doctr.models import detection_predictor
    print("✅ DocTR installed")
except ImportError as e:
    print(f"❌ DocTR: {e}")

print("\nVerification complete!")
```

## Tesseract Installation (System Binary Required)

Tesseract OCR requires a system-level installation in addition to the Python package.

### Windows
1. Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer (default path: `C:\Program Files\Tesseract-OCR`)
3. Add to PATH or set in Python:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install tesseract-ocr
```

### macOS
```bash
brew install tesseract
```

## Troubleshooting

### PaddleOCR on Python 3.13

If you get errors like `OSError: [WinError 127]` or `NoneType has no attribute 'replace'`:

1. **Use the workaround** - Set environment variable before importing:
   ```python
   import os
   os.environ.setdefault('HUB_DATASET_ENDPOINT', 'https://modelscope.cn/api/v1/datasets')
   from paddleocr import PaddleOCR
   ```

2. **Use older version** (if workaround doesn't work):
   ```bash
   pip uninstall paddleocr paddlex modelscope
   pip install paddleocr==2.7.3
   ```

3. **Use Python 3.11** - Create a separate environment with Python 3.11.

### CUDA/GPU Support

For GPU acceleration (optional):
- Install CUDA 11.8 or 12.x
- Install GPU versions of PyTorch and PaddlePaddle:
  ```bash
  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
  pip install paddlepaddle-gpu
  ```

### Memory Issues

Some models are large. If you run out of memory:
- Use CPU mode (default)
- Process smaller images
- Close other applications
