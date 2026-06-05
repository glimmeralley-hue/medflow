# MedFlow Build Guide

## Linux Standalone

1. Install build dependencies:
   ```bash
   python3 -m pip install pyinstaller
   ```

2. Run the Linux build script:
   ```bash
   bash build_linux.sh
   ```

3. Output:
   - `dist/MedFlow` — standalone Linux binary
   - `dist/MedFlow.AppImage` — AppImage if `appimagetool` is installed

## Windows Executable

1. Install PyInstaller on Windows:
   ```powershell
   python -m pip install pyinstaller
   ```

2. Run the build script on Windows or in a Wine-enabled environment with a Windows Python interpreter:
   ```bash
   bash build_windows.sh
   ```

3. Output:
   - `dist/MedFlow.exe`

> Note: building from Linux with the Linux `.venv` Python will not produce a valid Windows executable. Use Windows or Wine with a native Windows Python runtime to make a proper `.exe`.

## Publish a Download Page

A polished static landing page is included at `index.html`. Deploy it to GitHub Pages or any static host, then link it in your social bio for a professional download gateway.

Recommended release links:

- Linux AppImage: https://github.com/glimmeralley-hue/medflow/releases/download/latest/MedFlow.AppImage
- Windows EXE: https://github.com/glimmeralley-hue/medflow/releases/download/latest/MedFlow.exe

> Use the PayPal checkout button to charge $5 and send buyers the download asset after purchase. This repo includes a GitHub Pages workflow so your page can publish automatically.

### GitHub Pages Setup

1. Push this repo to GitHub.
2. Enable GitHub Pages from `Settings > Pages`.
3. Select the `main` branch and `/ (root)` directory.
4. Wait a few minutes for the site to deploy.

Your landing page link will be:

- `https://glimmeralley-hue.github.io/medflow/`

## Mobile Packaging

MedFlow is currently a PySide6 desktop app, so mobile packaging requires Qt for Android/iOS or a cross-platform mobile runtime.

### Android

The most direct route is to use Qt for Android and deploy the PySide6 app through the Qt Android toolchain. That process typically includes:

- Installing Qt with Android support
- Installing the Android NDK and SDK
- Using `pyside6-setup` or Qt Creator to package the application
- Creating an Android package (`.apk` / `.aab`)

### iOS

iOS packaging requires Qt for iOS and an Apple developer toolchain. This is generally done in a macOS environment.

### Notes

- Full mobile packaging is not currently automated in this repository.
- The desktop code can be adapted for mobile, but it may require UI adjustments and build toolchain setup.
