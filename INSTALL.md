# MedFlow Installation Guide

## Quick Install (Recommended)

Run the installer script for automatic setup:

```bash
bash install.sh
```

This installs MedFlow to `~/.local/share/com.medflow.app` with a launcher in `~/.local/bin`.

---

## Manual Installation

### Prerequisites

- **Python 3.8+** (Python 3.10+ recommended)
- **PySide6** (Qt6 bindings for Python)
- **Qt6 Charts** (for graphs)

### Install Dependencies

#### Arch Linux / Manjaro:
```bash
sudo pacman -S python-pyside6 qt6-charts
```

#### Ubuntu / Debian:
```bash
sudo apt install python3-pyside6.qt6 qt6-base
pip install PySide6
pip install PyQt6-Charts  # Alternative: use matplotlib
```

#### Fedora:
```bash
sudo dnf install python3-pyside6 qt6-qtcharts
```

#### Windows:
```powershell
pip install PySide6 PyQt6-Charts
```

#### macOS:
```bash
pip install PySide6 PyQt6-Charts
```

### Manual Setup Steps

1. **Clone or download MedFlow:**
   ```bash
   git clone https://github.com/glimmeralley-hue/medflow.git
   cd medflow
   ```

2. **Create installation directory:**
   ```bash
   mkdir -p ~/.local/share/com.medflow.app
   ```

3. **Copy files:**
   ```bash
   cp main.py requirements.txt medflow-icon.svg ~/.local/share/com.medflow.app/
   cp -r medflow/ ~/.local/share/com.medflow.app/
   ```

4. **Create launcher script:**
   ```bash
   mkdir -p ~/.local/bin
   cat > ~/.local/bin/medflow << 'EOF'
   #!/bin/bash
   python3 ~/.local/share/com.medflow.app/main.py "$@"
   EOF
   chmod +x ~/.local/bin/medflow
   ```

5. **Create desktop entry:**
   ```bash
   mkdir -p ~/.local/share/applications
   cat > ~/.local/share/applications/com.medflow.app.desktop << 'EOF'
   [Desktop Entry]
   Name=MedFlow
   Comment=Medical School Command Center - Planner, Timer, and Study Assistant
   Exec=python3 ~/.local/share/com.medflow.app/main.py
   Icon=~/.local/share/com.medflow.app/medflow-icon.svg
   Type=Application
   Categories=Education;Office;Calendar;
   Terminal=false
   StartupNotify=true
   Keywords=medical;student;planner;calendar;study;
   EOF
   ```

6. **Update desktop database:**
   ```bash
   update-desktop-database ~/.local/share/applications 2>/dev/null || true
   ```

---

## Database Initialization

On first launch, MedFlow automatically creates its database at `~/medflow.db` with the following schema:

- **academic_events** - Schedule and events
- **study_notes** - High-yield facts per event
- **study_debt** - Missed study targets
- **exam_scores** - Exam results with correlation
- **study_hours** - Time tracking
- **user_profile** - Personal profile data
- **flashcard_decks** - SM-2 spaced repetition decks
- **flashcards** - Individual flashcard cards
- **pomodoro_sessions** - Pomodoro timer logs

---

## Configuration

Configuration is stored at `~/.medflow/config.json`. Default settings:

```json
{
    "ui": {
        "theme": "light",
        "window_width": 1400,
        "window_height": 900
    },
    "timer": {
        "default_work_minutes": 25,
        "default_break_minutes": 5
    },
    "database": {
        "backup_enabled": true,
        "backup_retention": 5
    }
}
```

### Available Themes

- `light` - Light pink/beige theme (default)
- `dark` - Dark mode with cyan accents
- `medical_blue` - Professional blue medical theme
- `high_contrast` - Accessibility-focused contrast theme

Change theme via:
- Status bar theme selector dropdown
- Or edit `config.json` and restart

---

## Launch Options

After installation, you can launch MedFlow via:

1. **Application Menu:** Search "MedFlow" in KDE/GNOME
2. **Command Line:** Run `medflow`
3. **Direct:** `python3 ~/.local/share/com.medflow.app/main.py`

---

## Uninstall

To remove MedFlow:

```bash
rm -rf ~/.local/share/com.medflow.app
rm ~/.local/share/applications/com.medflow.app.desktop
rm ~/.local/bin/medflow
```

---

## Troubleshooting

### Import errors (QPen, etc.)
Run from the project directory:
```bash
python3 main.py
```

### Database errors
Delete the database to reset (WARNING: deletes all data):
```bash
rm ~/medflow.db
```

### Theme not applying
Ensure you're using the refactored entry point:
```bash
python3 main_refactored.py
```

### Missing sounds
Audio files for study timer are in `sounds/` directory. Copy to installation if needed.

---

## Features Overview

### 1. Planner Tab
- Full-page calendar with event management
- Categories: Lectures, Clinical, Study, Review, Research
- Reminders and notifications

### 2. Results Tab
- Exam score tracking (CAT & End-of-Unit)
- Study hours correlation graphs
- Performance analytics

### 3. Notes Tab
- Clinical study journal
- Category tagging
- Search and export

### 4. Flashcards Tab
- SM-2 spaced repetition algorithm
- Import study notes as flashcards
- Rating: Again (0), Hard (2), Good (4), Easy (5)

### 5. Library Tab
- PDF/EPUB/TXT book management
- Reading progress tracking
- Bookmarks

### 6. Profile Tab
- Personal information
- Career goals & ambitions
- Music player for study sessions
- Quick stats dashboard

---

## Keyboard Shortcuts

- `Ctrl+N` - New event (Planner tab)
- `Ctrl+D` - Toggle theme
- `Ctrl+S` - Save note (Notes tab)
- `Space` - Start/pause timer (Timer view)