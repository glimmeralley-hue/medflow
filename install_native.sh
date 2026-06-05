#!/bin/bash
# Native installation script for MedFlow on CachyOS/KDE Plasma

set -e

echo "🏥 Installing MedFlow - Medical School Command Center"
echo "=================================================="

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_NAME="MedFlow"
APP_ID="com.medflow.app"

# Create installation directory
INSTALL_DIR="$HOME/.local/share/$APP_ID"
echo "📁 Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Copy application files
echo "📦 Copying application files..."
cp -r "$SCRIPT_DIR"/*.py "$INSTALL_DIR/"
cp -r "$SCRIPT_DIR"/*.db "$INSTALL_DIR/" 2>/dev/null || true

# Create application icon directory
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"
mkdir -p "$ICON_DIR"

ICON_PATH="appointment-new"
if [ -f "$SCRIPT_DIR/medflow-icon.svg" ]; then
    echo "🎨 Installing application icon..."
    cp "$SCRIPT_DIR/medflow-icon.svg" "$ICON_DIR/$APP_ID.svg"
    cp "$SCRIPT_DIR/medflow-icon.svg" "$INSTALL_DIR/"
    ICON_PATH="$INSTALL_DIR/medflow-icon.svg"
else
    echo "🎨 No SVG icon found; using system default icon."
fi

# Create desktop entry
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

echo "🖥️  Creating desktop entry..."
cat > "$DESKTOP_DIR/$APP_ID.desktop" << EOF
[Desktop Entry]
Name=MedFlow
Comment=Medical School Command Center - Planner, Timer, and Study Assistant
Exec=python3 $INSTALL_DIR/main.py
Icon=$ICON_PATH
Type=Application
Categories=Education;Office;Calendar;
Terminal=false
StartupNotify=true
Keywords=medical;student;planner;calendar;study;anki;
X-GNOME-FullName=MedFlow Medical School Planner
X-KDE-StartupNotify=true

Actions=NewEvent;

[Desktop Action NewEvent]
Name=Add New Event
Exec=python3 $INSTALL_DIR/main.py --add-event
Icon=appointment-new
EOF

# Create launcher script
LAUNCHER_DIR="$HOME/.local/bin"
mkdir -p "$LAUNCHER_DIR"

cat > "$LAUNCHER_DIR/medflow" << EOF
#!/bin/bash
# MedFlow launcher
python3 "$INSTALL_DIR/main.py" "\$@"
EOF

chmod +x "$LAUNCHER_DIR/medflow"

# Update desktop database
echo "🔄 Updating application database..."
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true

# Check dependencies
echo "🔍 Checking dependencies..."
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "⚠️  PySide6 not found! Installing..."
    sudo pacman -S pyside6 --noconfirm || {
        echo "❌ Failed to install PySide6. Please install manually:"
        echo "   sudo pacman -S pyside6 qt6-charts"
        exit 1
    }
fi

if ! python3 -c "import PySide6.QtCharts" 2>/dev/null; then
    echo "⚠️  Qt6 Charts not found! Installing..."
    sudo pacman -S qt6-charts --noconfirm || {
        echo "❌ Failed to install qt6-charts. Please install manually:"
        echo "   sudo pacman -S qt6-charts"
        exit 1
    }
fi

echo ""
echo "✅ Installation complete!"
echo "=================================================="
echo "📍 Installation directory: $INSTALL_DIR"
echo "🚀 Launch MedFlow by:"
echo "   - Searching 'MedFlow' in your application menu"
echo "   - Running: medflow"
echo "   - Running: python3 $INSTALL_DIR/main.py"
echo ""
echo "🗑️  To uninstall, run: rm -rf $INSTALL_DIR"
echo "=================================================="
