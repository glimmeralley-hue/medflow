#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🔧 Building MedFlow as a standalone Linux executable"

PYTHON=python3
if [[ -f ".venv/bin/python" ]]; then
  PYTHON="$(pwd)/.venv/bin/python"
fi

if ! "$PYTHON" --version >/dev/null 2>&1; then
  echo "Python3 is required."
  exit 1
fi

if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
  echo "PyInstaller is not installed. Install it with: $PYTHON -m pip install pyinstaller"
  exit 1
fi

PYINSTALLER_OPTS=(
  --onefile
  --windowed
  --name MedFlow
  --add-data "medflow-icon.svg:./"
  --add-data "requirements.txt:./"
  main.py
)

"$PYTHON" -m PyInstaller "${PYINSTALLER_OPTS[@]}"

echo "✅ Build complete."
echo "Binary is available in dist/MedFlow"

if command -v appimagetool >/dev/null 2>&1; then
  echo "🚀 appimagetool found; creating AppImage from AppDir..."
  mkdir -p build/MedFlow.AppDir/usr/bin
  cp dist/MedFlow build/MedFlow.AppDir/usr/bin/MedFlow
  mkdir -p build/MedFlow.AppDir/usr/share/icons/hicolor/256x256/apps
  cp medflow-icon.svg build/MedFlow.AppDir/usr/share/icons/hicolor/256x256/apps/MedFlow.svg
  cat > build/MedFlow.AppDir/MedFlow.desktop <<EOF
[Desktop Entry]
Name=MedFlow
Exec=MedFlow
Icon=MedFlow
Type=Application
Categories=Education;Office;Calendar;
Terminal=false
EOF
  appimagetool build/MedFlow.AppDir dist/MedFlow.AppImage
  echo "✅ AppImage created at dist/MedFlow.AppImage"
else
  echo "⚠️ appimagetool not found. Install it to generate an AppImage."
fi
