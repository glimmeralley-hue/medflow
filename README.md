# MedFlow - Native Medical School Command Center

A lightweight, native desktop application designed specifically for medical students, featuring a high-yield planner and scheduler with a professional dark theme aesthetic.

## Features

### 📅 Academic Ledger (Scheduler)
- Hierarchical calendar view with date selection
- Categorization for: Lectures, Practical Labs, Dissection, and Clinical Rotations
- Ability to add "Sub-topics" to any block (e.g., Anatomy -> Lower Limb -> Femoral Triangle)
- Time-based event scheduling with notes

### ⏱️ The "Pulse" Timer (Study Tool)
- Customizable Pomodoro-style timer integrated into the main dashboard
- Presets for "Deep Work" (50/10) and "Flashcard Blitz" (25/5)
- Visual countdown with a glowing neon blue progress ring
- Start, Stop, and Reset controls

### 📝 Active Recall Sidebar
- Quick Note area for each study block to jot down 3 "High-Yield Facts"
- "Study Debt" list that automatically tracks missed or incomplete scheduled blocks
- Event-specific note taking with automatic saving

### 📊 Results Ledger (Performance Tracker)
- Log CAT (Continuous Assessment Test) and End-of-Unit exam scores
- Track Subject Name, Score (%), and Date
- Visual pass/fail indicator showing proximity to 50% pass mark
- **Scientist Feature**: Study Hours vs Exam Score correlation line graph
- Analyze if productivity correlates with exam results

### 📝 Active Recall & Notes Section
- Quick High-Yield facts manager linked to each academic session
- Fully editable notepad with auto-save for comprehensive study sessions
- Search and browse clinical study logs by date and topic

### 📚 Digital Medical Library
- Catalog your textbooks, slides, and journals (PDF, EPUB, TXT)
- Categorize documents by preclinical and clinical subjects (Anatomy, Physiology, Pathology, etc.)
- Star-rating system and customized reading notes for each item

### 🎨 Visual & Technical Requirements
- **Aesthetic**: Dark theme (Background: #0A0E14), Cyan/Neon Blue accents
- **Native Integration**: System Tray icon showing remaining timer and next class
- **Database**: Local medflow.db (SQLite) - no cloud dependency or internet required
- **Layout**: Clean, tabbed interface with 3-pane Dashboard layout

## Installation on CachyOS/KDE Plasma

### Method 1: Using Package Manager (Recommended)
1. Open your Software Manager (Shelly or Octopi)
2. Search and install: `pyside6`
3. Install a code editor like VS Code or PyCharm

### Method 2: Command Line
```bash
# Install PySide6
sudo pacman -S pyside6

# Verify installation
python3 -c "import PySide6; print('PySide6 installed successfully')"
```

## Usage

1. Clone or download this repository
2. Navigate to the project directory
3. Run the application:
   ```bash
   python3 main.py
   ```
4. The application will start with a fully custom, tabbed interface in our Obsidian Dark Theme layout.

## Application Layout

### 📅 Planner Tab
The main **dedicated full-page planner** featuring:
- **Large Calendar** (60% of screen) - Month view with navigation
- **Date Selection** - Click any date to see events
- **⏰ Reminders & Pulse Timer** - Automatic notifications and glowing Pomodoro focus timer
- **Event Management** - Add events with category, time, subtopic, and reminder settings

### 📊 Results Ledger Tab
- Log exam scores with subject, type (CAT/End-of-Unit), score (%), and date
- View exam performance in a table with green/red pass-fail badges (50% threshold)
- Study Hours vs Exam Score correlation graph to track productivity with exam results

### 📝 Notes Tab
- Link clinical study logs and high-yield facts to scheduled blocks
- Searchable library of clinical notes and summaries

### 📚 Library Tab
- Catalog textbook PDFs, slides, and learning materials
- Star and review books to track active reading progress

### 👤 Profile Tab
- Comprehensive profile setup with personal details, goals, and study plans
- Display avatars/profile pictures and comprehensive statistics overview
- **Clear Profile** button to reset all database records with confirmation dialog

## Native Installation

### Install as System Application
```bash
# Make the install script executable
chmod +x install_native.sh

# Run the installer
./install_native.sh
```

This will:
- Install MedFlow to `~/.local/share/com.medflow.app/`
- Create a desktop entry (appears in your app menu)
- Add `medflow` command to your PATH
- Set up auto-start capability

### Manual Installation
```bash
# Copy to a location in your PATH
cp main.py ~/.local/bin/medflow

# Or run directly
python3 /path/to/main.py
```

### Uninstall
```bash
rm -rf ~/.local/share/com.medflow.app/
rm ~/.local/share/applications/com.medflow.app.desktop
rm ~/.local/bin/medflow
```

## Database

The application uses a local SQLite database (`medflow.db`) that stores:
- Academic events (lectures, labs, etc.)
- High-yield facts for each event
- Study debt entries for missed/incomplete tasks
- **Exam scores** (CAT and End-of-Unit results)
- **Study hours** tracked per day/subject

The database is automatically created on first run and requires no setup.

## System Requirements

- **OS**: Linux (optimized for CachyOS/KDE Plasma)
- **Python**: 3.8 or higher
- **Dependencies**: PySide6 (Qt6 bindings for Python)

## Configuration

The application supports KWin background blur for transparent-glass effects on KDE Plasma systems. The dark theme is automatically applied with cyan/neon blue accents.

## Troubleshooting

If you encounter import errors:
1. Ensure PySide6 is installed: `python3 -c "import PySide6"`
2. If using a virtual environment, activate it before running
3. Check that all dependencies are installed with `pip install -r requirements.txt`

## Development

The codebase is modular and can be extended:
- Database operations are handled by the `Database` class
- UI components are separated into logical widgets
- Styling uses Qt stylesheets for easy customization

## License

This project is open source and available for medical students to use and modify.
