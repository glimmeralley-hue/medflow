#!/bin/bash
# Simple user-local installation for MedFlow (no sudo required)

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
cp "$SCRIPT_DIR/main.py" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/requirements.txt" "$INSTALL_DIR/" 2>/dev/null || true

# Copy icon if it exists
if [ -f "$SCRIPT_DIR/medflow-icon.svg" ]; then
    cp "$SCRIPT_DIR/medflow-icon.svg" "$INSTALL_DIR/"
    echo "🎨 Copied app icon"
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
Icon=$INSTALL_DIR/medflow-icon.svg
Type=Application
Categories=Education;Office;Calendar;
Terminal=false
StartupNotify=true
Keywords=medical;student;planner;calendar;study;
Name[en_US]=MedFlow
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

echo ""
echo "✅ Installation complete!"
echo "=================================================="
echo "📍 Installation directory: $INSTALL_DIR"
echo ""
echo "🚀 Launch MedFlow by:"
echo "   1. Search 'MedFlow' in your application menu (KDE/GNOME)"
echo "   2. Run: medflow"
echo "   3. Run: python3 $INSTALL_DIR/main.py"
echo ""
echo "🗑️  To uninstall: rm -rf $INSTALL_DIR && rm $DESKTOP_DIR/$APP_ID.desktop && rm $LAUNCHER_DIR/medflow"
echo "=================================================="
echo ""
echo "⚠️  NOTE: Make sure you have PySide6 and qt6-charts installed:"
echo "   sudo pacman -S pyside6 qt6-charts"
