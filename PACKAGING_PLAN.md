# MedFlow Cross-Platform Packaging Plan

## Overview

This document outlines the strategy for packaging MedFlow for Windows and mobile platforms (Android/iOS).

---

## Windows Version

### Current Status
- Basic build script exists at `build_windows.sh`
- Requires running on Windows or Wine with Windows Python

### Requirements
- **PyInstaller**: For creating standalone executable
- **PySide6-Charts**: Qt Charts support
- **PySide6-Multimedia**: Audio support for study music
- **Windows Python runtime** (3.8+)

### Implementation Steps

#### 1. Update Build Script
- [x] Add sounds directory to PyInstaller data files
- [x] Add hidden imports for Qt modules
- [ ] Create separate `.spec` file for Windows (`MedFlow-Windows.spec`)
- [ ] Add icon embedding for Windows executable

#### 2. Windows-Specific Considerations
- Path handling: Use `os.path` or `pathlib` for cross-platform compatibility
- Audio files: Bundle in `sounds/` directory
- Database location: `%LOCALAPPDATA%\MedFlow\medflow.db`
- Configuration: `%LOCALAPPDATA%\MedFlow\config.json`

#### 3. Testing Strategy
- Test on Windows 10/11 with different Python versions
- Verify all tabs work correctly
- Test database migrations
- Test audio/music player functionality

### Build Commands

```powershell
# On Windows (PowerShell)
pip install pyinstaller PySide6 PySide6-Charts PySide6-Multimedia
bash build_windows.sh
```

---

## Mobile Version (Android)

### Current Status
- Desktop-only application using PySide6
- Requires Qt for Android toolchain

### Architecture Options

#### Option A: Qt for Android (Recommended)
- Use Qt's Android support with PySide6
- Requires:
  - Qt installation with Android support
  - Android NDK and SDK
  - Qt Creator or `python-for-android` (buildozer)

#### Option B: Kivy (Alternative)
- Rewrite UI layer using Kivy framework
- Better mobile support but requires significant changes

### Implementation Plan

#### Phase 1: Research & Setup
1. Install Qt with Android support
2. Set up Android SDK/NDK
3. Test PySide6 Android deployment

#### Phase 2: UI Adaptations
1. Responsive layout changes:
   - Convert tabbed interface to drawer navigation
   - Optimize for touch targets (minimum 48dp)
   - Landscape/portrait orientation handling
2. Mobile-specific features:
   - Notification support
   - Background audio playback
   - File picker integration

#### Phase 3: Build Configuration
Create `buildozer.spec` for Android builds:

```ini
[app]
title = MedFlow
package.name = medflow
package.domain = com.medflow
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,svg,wav
version = 1.0.0
requirements = python3, pyside6, sqlite3

[buildozer]
log_level = 2

[android]
sdk_path = ~/Android/Sdk
ndk_path = ~/Android/Ndk
api_level = 33
```

### Challenges
- PySide6 QtCharts on Android may need special handling
- File access permissions on mobile
- Database backup/sync strategy for mobile

---

## Mobile Version (iOS)

### Requirements
- macOS with Xcode installed
- Qt for iOS
- Apple Developer account ($99/year)

### Build Approach
1. Use Qt Creator to package PySide6 app
2. Replace `QLineEdit` with `QTextEdit` for better mobile keyboards
3. Add iOS-specific entitlements for file access

---

## Release Strategy

### Windows Release
- GitHub Release with `MedFlow.exe`
- Install wizard (NSIS/Inno Setup)
- Auto-update capability

### Android Release
- Google Play Store listing
- APK/AAB distribution via GitHub Releases

### iOS Release
- Apple App Store listing
- TestFlight for beta testing

---

## Timeline

| Task | Estimated Time | Priority |
|------|---------------|----------|
| Windows testing & bug fixes | 1-2 weeks | High |
| Mobile research & PoC | 2-3 weeks | Medium |
| Android build setup | 2-4 weeks | Medium |
| iOS build setup | 1-2 weeks | Low |

---

## Resources

- Qt for Android: https://doc.qt.io/qt-6/android.html
- Python for Android: https://github.com/kivy/python-for-android
- Buildozer: https://buildozer.readthedocs.io/
- PyInstaller docs: https://pyinstaller.org/