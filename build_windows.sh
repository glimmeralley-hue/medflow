#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Building MedFlow for Windows using PyInstaller"

if [[ "$OSTYPE" != mstsc* && "$OSTYPE" != cygwin* && "$OSTYPE" != msys* && "$OSTYPE" != win32 ]]; then
  echo "⚠️  Windows exe builds should be performed on Windows or via Wine with a Windows Python interpreter."
  echo "   Building on Linux with the Linux .venv will produce a non-Windows ELF binary even if it ends with .exe."
  exit 1
fi

PYTHON=python3
if [[ -f ".venv/bin/python" ]]; then
  PYTHON="$(pwd)/.venv/bin/python"
fi

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller is not installed. Install it with: $PYTHON -m pip install pyinstaller"
  exit 1
fi

DATA_SEP=":"
if [[ "$OSTYPE" == cygwin* || "$OSTYPE" == msys* || "$OSTYPE" == win32 ]]; then
  DATA_SEP=";"
fi

"$PYTHON" -m PyInstaller --onefile --windowed --name MedFlow.exe --add-data "medflow-icon.svg${DATA_SEP}." --add-data "requirements.txt${DATA_SEP}." main.py

echo "✅ Build complete."
echo "Executable is available in dist/MedFlow.exe"
