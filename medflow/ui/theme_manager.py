"""Theme Manager for MedFlow - Centralized theme customization system.

This module provides a complete theming system with:
- 6 professionally-designed color themes
- Signal-based listeners for real-time theme propagation
- Global stylesheet generation for all widget types
- Per-theme status bar, combo, and button styling
"""

from typing import Dict, Optional, Callable
from enum import Enum
from PySide6.QtCore import QObject, Signal

# iOS-style font stack for native look
IOS_FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI", Roboto, Helvetica, Arial, sans-serif'


class ThemeType(Enum):
    """Available theme types for MedFlow."""
    LIGHT = "light"
    DARK = "dark"
    MEDICAL_BLUE = "medical_blue"
    HIGH_CONTRAST = "high_contrast"
    WARM_SEPIA = "warm_sepia"
    FOREST_NIGHT = "forest_night"


class ThemeColors:
    """Centralized color schemes for all themes.
    
    Each theme defines a complete palette with the following tokens:
    
    Core Brand:
        PRIMARY / PRIMARY_LIGHT / PRIMARY_DARK
        SECONDARY / SECONDARY_LIGHT / SECONDARY_DARK
    
    Backgrounds:
        BG_DARK - main window background
        BG_LIGHT - input/card alternate background  
        BG_WHITE - pure white card surface
        BG_CARD - card/widget surface color
        
    Text:
        TEXT_PRIMARY - main body text
        TEXT_SECONDARY - secondary/meta text
        TEXT_MUTED - disabled/placeholder text
        TEXT_LIGHT - text on primary buttons
        
    Accents:
        ACCENT_CYAN / ACCENT_ORANGE / ACCENT_GREEN
        
    Semantic:
        SUCCESS / WARNING / ERROR / INFO
        
    Borders & Dividers:
        BORDER - widget borders
        DIVIDER - line/separator
        HOVER - hover highlight
        
    Inputs:
        INPUT_BG - input field background
        INPUT_BORDER - input field border
        
    Status Bar:
        STATUSBAR_BG / STATUSBAR_TEXT / STATUSBAR_BORDER
        
    Tabs:
        TAB_BG / TAB_SELECTED / TAB_TEXT / TAB_TEXT_SELECTED
        
    Misc:
        CARD_BORDER - card/groupbox border
    """
    
    # ─── Light Theme (Pink - Warm, inviting) ────────────────────────────────
    LIGHT = {
        "PRIMARY": "#E91E63",
        "PRIMARY_LIGHT": "#F06292",
        "PRIMARY_DARK": "#C2185B",
        "SECONDARY": "#F8BBD0",
        "SECONDARY_LIGHT": "#FCE4EC",
        "SECONDARY_DARK": "#F48FB1",
        "BG_DARK": "#FDF2F5",
        "BG_LIGHT": "#FFF5F7",
        "BG_WHITE": "#FFFFFF",
        "BG_CARD": "#FFF8FA",
        "TEXT_PRIMARY": "#2D1B24",
        "TEXT_SECONDARY": "#5C3D4E",
        "TEXT_MUTED": "#9E7D8E",
        "TEXT_LIGHT": "#FFFFFF",
        "ACCENT_CYAN": "#00BCD4",
        "ACCENT_ORANGE": "#FF6F00",
        "ACCENT_GREEN": "#388E3C",
        "SUCCESS": "#43A047",
        "WARNING": "#FB8C00",
        "ERROR": "#E53935",
        "INFO": "#1E88E5",
        "BORDER": "#F0DCE3",
        "DIVIDER": "#E8D0D9",
        "HOVER": "#FCE4EC",
        "INPUT_BG": "#FFFBFD",
        "INPUT_BORDER": "#E8C9D4",
        "STATUSBAR_BG": "#E91E63",
        "STATUSBAR_TEXT": "#FFFFFF",
        "STATUSBAR_BORDER": "#C2185B",
        "TAB_BG": "#FCE4EC",
        "TAB_SELECTED": "#E91E63",
        "TAB_TEXT": "#5C3D4E",
        "TAB_TEXT_SELECTED": "#FFFFFF",
        "CARD_BORDER": "#F0DCE3",
    }
    
    # ─── Dark Theme (Modern dark with cyan accent) ──────────────────────────
    DARK = {
        "PRIMARY": "#00D4FF",
        "PRIMARY_LIGHT": "#33DBFF",
        "PRIMARY_DARK": "#00A8CC",
        "SECONDARY": "#1A1F2E",
        "SECONDARY_LIGHT": "#2A3244",
        "SECONDARY_DARK": "#0A0E14",
        "BG_DARK": "#0A0E14",
        "BG_LIGHT": "#1A1F2E",
        "BG_WHITE": "#2A3244",
        "BG_CARD": "#1A1F2E",
        "TEXT_PRIMARY": "#E8E8E8",
        "TEXT_SECONDARY": "#B0B0B0",
        "TEXT_MUTED": "#707070",
        "TEXT_LIGHT": "#0A0E14",
        "ACCENT_CYAN": "#00D4FF",
        "ACCENT_ORANGE": "#FF9800",
        "ACCENT_GREEN": "#81C784",
        "SUCCESS": "#81C784",
        "WARNING": "#FFB74D",
        "ERROR": "#E57373",
        "INFO": "#64B5F6",
        "BORDER": "#2A3244",
        "DIVIDER": "#1A1F2E",
        "HOVER": "#2A3244",
        "INPUT_BG": "#2A3244",
        "INPUT_BORDER": "#00D4FF",
        "STATUSBAR_BG": "#1A1F2E",
        "STATUSBAR_TEXT": "#B0B0B0",
        "STATUSBAR_BORDER": "#00D4FF",
        "TAB_BG": "#1A1F2E",
        "TAB_SELECTED": "#00D4FF",
        "TAB_TEXT": "#B0B0B0",
        "TAB_TEXT_SELECTED": "#0A0E14",
        "CARD_BORDER": "#2A3244",
    }
    
    # ─── Medical Blue Theme (Clean, professional, clinical) ─────────────────
    MEDICAL_BLUE = {
        "PRIMARY": "#1565C0",
        "PRIMARY_LIGHT": "#42A5F5",
        "PRIMARY_DARK": "#0D47A1",
        "SECONDARY": "#BBDEFB",
        "SECONDARY_LIGHT": "#E3F2FD",
        "SECONDARY_DARK": "#90CAF9",
        "BG_DARK": "#E8F0FE",
        "BG_LIGHT": "#F0F8FF",
        "BG_WHITE": "#FFFFFF",
        "BG_CARD": "#F5FBFF",
        "TEXT_PRIMARY": "#0D1B3E",
        "TEXT_SECONDARY": "#2C4A7C",
        "TEXT_MUTED": "#7A9CC6",
        "TEXT_LIGHT": "#FFFFFF",
        "ACCENT_CYAN": "#00ACC1",
        "ACCENT_ORANGE": "#EF6C00",
        "ACCENT_GREEN": "#2E7D32",
        "SUCCESS": "#43A047",
        "WARNING": "#FB8C00",
        "ERROR": "#E53935",
        "INFO": "#1E88E5",
        "BORDER": "#BBDEFB",
        "DIVIDER": "#C8E0F4",
        "HOVER": "#E3F2FD",
        "INPUT_BG": "#FFFFFF",
        "INPUT_BORDER": "#90CAF9",
        "STATUSBAR_BG": "#1565C0",
        "STATUSBAR_TEXT": "#FFFFFF",
        "STATUSBAR_BORDER": "#0D47A1",
        "TAB_BG": "#E3F2FD",
        "TAB_SELECTED": "#1565C0",
        "TAB_TEXT": "#2C4A7C",
        "TAB_TEXT_SELECTED": "#FFFFFF",
        "CARD_BORDER": "#BBDEFB",
    }
    
    # ─── High Contrast Theme (Accessibility-first) ──────────────────────────
    HIGH_CONTRAST = {
        "PRIMARY": "#000000",
        "PRIMARY_LIGHT": "#333333",
        "PRIMARY_DARK": "#000000",
        "SECONDARY": "#FFFF00",
        "SECONDARY_LIGHT": "#FFFF66",
        "SECONDARY_DARK": "#FFCC00",
        "BG_DARK": "#FFFFFF",
        "BG_LIGHT": "#FFFFFF",
        "BG_WHITE": "#FFFFFF",
        "BG_CARD": "#FFFFFF",
        "TEXT_PRIMARY": "#000000",
        "TEXT_SECONDARY": "#000000",
        "TEXT_MUTED": "#444444",
        "TEXT_LIGHT": "#000000",
        "ACCENT_CYAN": "#0000FF",
        "ACCENT_ORANGE": "#FF0000",
        "ACCENT_GREEN": "#008000",
        "SUCCESS": "#008000",
        "WARNING": "#FF0000",
        "ERROR": "#FF0000",
        "INFO": "#0000FF",
        "BORDER": "#000000",
        "DIVIDER": "#000000",
        "HOVER": "#FFFF66",
        "INPUT_BG": "#FFFFFF",
        "INPUT_BORDER": "#000000",
        "STATUSBAR_BG": "#FFFFFF",
        "STATUSBAR_TEXT": "#000000",
        "STATUSBAR_BORDER": "#000000",
        "TAB_BG": "#FFFFFF",
        "TAB_SELECTED": "#000000",
        "TAB_TEXT": "#000000",
        "TAB_TEXT_SELECTED": "#FFFFFF",
        "CARD_BORDER": "#000000",
    }
    
    # ─── Warm Sepia Theme (Easy on eyes, warm tones) ───────────────────────
    WARM_SEPIA = {
        "PRIMARY": "#A67C52",
        "PRIMARY_LIGHT": "#C4A07A",
        "PRIMARY_DARK": "#7A5C3A",
        "SECONDARY": "#E8D5B7",
        "SECONDARY_LIGHT": "#F4E8D0",
        "SECONDARY_DARK": "#D4BFA0",
        "BG_DARK": "#F5EDE0",
        "BG_LIGHT": "#FAF3E8",
        "BG_WHITE": "#FFFBF5",
        "BG_CARD": "#FDF5EA",
        "TEXT_PRIMARY": "#3D2B1F",
        "TEXT_SECONDARY": "#6B5A4A",
        "TEXT_MUTED": "#A09080",
        "TEXT_LIGHT": "#FFFFFF",
        "ACCENT_CYAN": "#5B9BD5",
        "ACCENT_ORANGE": "#BF6F00",
        "ACCENT_GREEN": "#5B8054",
        "SUCCESS": "#5B8054",
        "WARNING": "#BF6F00",
        "ERROR": "#B0413E",
        "INFO": "#4A7BA7",
        "BORDER": "#E0CFB8",
        "DIVIDER": "#D8C4AA",
        "HOVER": "#F4E8D0",
        "INPUT_BG": "#FFFBF5",
        "INPUT_BORDER": "#D4BFA0",
        "STATUSBAR_BG": "#A67C52",
        "STATUSBAR_TEXT": "#FFFFFF",
        "STATUSBAR_BORDER": "#7A5C3A",
        "TAB_BG": "#F4E8D0",
        "TAB_SELECTED": "#A67C52",
        "TAB_TEXT": "#6B5A4A",
        "TAB_TEXT_SELECTED": "#FFFFFF",
        "CARD_BORDER": "#E0CFB8",
    }
    
    # ─── Forest Night Theme (Deep green, calming) ──────────────────────────
    FOREST_NIGHT = {
        "PRIMARY": "#4CAF50",
        "PRIMARY_LIGHT": "#66BB6A",
        "PRIMARY_DARK": "#2E7D32",
        "SECONDARY": "#1B3A2D",
        "SECONDARY_LIGHT": "#2D4F3F",
        "SECONDARY_DARK": "#0D251B",
        "BG_DARK": "#0D1F15",
        "BG_LIGHT": "#132A1D",
        "BG_WHITE": "#1B3A2D",
        "BG_CARD": "#162F21",
        "TEXT_PRIMARY": "#D4E6D0",
        "TEXT_SECONDARY": "#A8C0A0",
        "TEXT_MUTED": "#6A8A60",
        "TEXT_LIGHT": "#0D1F15",
        "ACCENT_CYAN": "#26C6DA",
        "ACCENT_ORANGE": "#FFA726",
        "ACCENT_GREEN": "#81C784",
        "SUCCESS": "#81C784",
        "WARNING": "#FFB74D",
        "ERROR": "#E57373",
        "INFO": "#4FC3F7",
        "BORDER": "#1B3A2D",
        "DIVIDER": "#152F21",
        "HOVER": "#2D4F3F",
        "INPUT_BG": "#1B3A2D",
        "INPUT_BORDER": "#4CAF50",
        "STATUSBAR_BG": "#132A1D",
        "STATUSBAR_TEXT": "#A8C0A0",
        "STATUSBAR_BORDER": "#4CAF50",
        "TAB_BG": "#132A1D",
        "TAB_SELECTED": "#4CAF50",
        "TAB_TEXT": "#A8C0A0",
        "TAB_TEXT_SELECTED": "#0D1F15",
        "CARD_BORDER": "#1B3A2D",
    }
    
    @classmethod
    def get_colors(cls, theme_type: ThemeType = ThemeType.LIGHT) -> Dict[str, str]:
        """Get color dictionary for a theme."""
        mapping = {
            ThemeType.LIGHT: cls.LIGHT,
            ThemeType.DARK: cls.DARK,
            ThemeType.MEDICAL_BLUE: cls.MEDICAL_BLUE,
            ThemeType.HIGH_CONTRAST: cls.HIGH_CONTRAST,
            ThemeType.WARM_SEPIA: cls.WARM_SEPIA,
            ThemeType.FOREST_NIGHT: cls.FOREST_NIGHT,
        }
        return mapping.get(theme_type, cls.LIGHT)


class ThemeChangeNotifier(QObject):
    """QObject-based signal emitter for theme changes.
    
    This allows any widget to connect to theme changes without
    inheriting from ThemeManager.
    """
    theme_changed = Signal(ThemeType)


class ThemeManager:
    """Central manager for theme application across the application.
    
    Features:
    - Singleton pattern via get_theme_manager()
    - Signal-based notification when theme changes
    - Global stylesheet generation covering all widget types
    - Convenience methods for status bar, combo, button styling
    """
    
    def __init__(self):
        self._current_theme = ThemeType.LIGHT
        self._notifier = ThemeChangeNotifier()
    
    def set_theme(self, theme_type: ThemeType) -> None:
        """Set the current theme and notify listeners."""
        if theme_type != self._current_theme:
            self._current_theme = theme_type
            self._notifier.theme_changed.emit(theme_type)
    
    def get_theme(self) -> ThemeType:
        """Get the current theme."""
        return self._current_theme
    
    def get_color(self, color_name: str) -> str:
        """Get a specific color for the current theme."""
        colors = ThemeColors.get_colors(self._current_theme)
        return colors.get(color_name, "#000000")
    
    def get_colors(self, theme_type: ThemeType = None) -> Dict[str, str]:
        """Get all colors dictionary for current or specified theme."""
        if theme_type is None:
            theme_type = self._current_theme
        return ThemeColors.get_colors(theme_type)
    
    def theme_changed_connect(self, callback: Callable[[ThemeType], None]) -> None:
        """Connect a callback to be called when theme changes.
        
        The callback receives the new ThemeType as its argument.
        """
        self._notifier.theme_changed.connect(callback)
    
    def theme_changed_disconnect(self, callback: Callable[[ThemeType], None]) -> None:
        """Disconnect a previously connected callback."""
        self._notifier.theme_changed.disconnect(callback)
    
    def get_global_stylesheet(self, theme_type: ThemeType = None) -> str:
        """Get a complete global stylesheet for the entire application.
        
        This covers ALL widget types so individual widgets don't need
        their own stylesheets. Widgets that need special styling can
        override specific properties after this is applied.
        
        The key improvement: Instead of 'QWidget { background-color: ... }'
        which overrides everything, we use specific selectors so that
        targeted inline styles (e.g. status bar) still work.
        """
        c = ThemeColors.get_colors(theme_type or self._current_theme)
        return f"""
            /* Main Window */
            QMainWindow {{
                background-color: {c['BG_DARK']};
                color: {c['TEXT_PRIMARY']};
                font-family: {IOS_FONT_STACK};
            }}
            
            /* Generic Widget - only set for direct QWidget, not subclasses */
            QWidget {{
                font-family: {IOS_FONT_STACK};
            }}
            
            /* Frame / Card style widgets */
            QFrame {{
                background-color: {c['BG_CARD']};
                color: {c['TEXT_PRIMARY']};
                border-radius: 8px;
            }}
            
            /* Group Box */
            QGroupBox {{
                font-weight: 600;
                font-size: 14px;
                color: {c['PRIMARY']};
                background-color: {c['BG_CARD']};
                border: 2px solid {c['CARD_BORDER']};
                border-radius: 12px;
                margin-top: 10px;
                padding-top: 15px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                color: {c['PRIMARY']};
            }}
            
            /* Labels */
            QLabel {{
                color: {c['TEXT_PRIMARY']};
                background: transparent;
                border: none;
            }}
            
            /* Buttons */
            QPushButton {{
                background-color: {c['PRIMARY']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: 600;
                font-size: 13px;
                font-family: {IOS_FONT_STACK};
                min-height: 24px;
            }}
            QPushButton:hover {{
                background-color: {c['PRIMARY_LIGHT']};
            }}
            QPushButton:pressed {{
                background-color: {c['PRIMARY_DARK']};
            }}
            QPushButton:disabled {{
                background-color: {c['SECONDARY_LIGHT']};
                color: {c['TEXT_MUTED']};
            }}
            
            /* Secondary button style - for cancel/destructive actions */
            QPushButton[danger="true"] {{
                background-color: {c['ERROR']};
            }}
            QPushButton[danger="true"]:hover {{
                background-color: {c['ERROR']}aa;
            }}
            
            /* Input Fields */
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 10px;
                border-radius: 10px;
                font-size: 13px;
                font-family: {IOS_FONT_STACK};
                selection-background-color: {c['PRIMARY']};
                selection-color: {c['TEXT_LIGHT']};
            }}
            QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
            QLineEdit:disabled, QTextEdit:disabled {{
                background-color: {c['BG_LIGHT']};
                color: {c['TEXT_MUTED']};
            }}
            
            /* Combo Box */
            QComboBox {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px 10px;
                border-radius: 10px;
                font-size: 13px;
                font-family: {IOS_FONT_STACK};
                min-height: 24px;
            }}
            QComboBox:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 8px;
            }}
            QComboBox::down-arrow {{
                image: none;
                width: 0;
            }}
            QComboBox QAbstractItemView {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 8px;
                selection-background-color: {c['SECONDARY']};
                selection-color: {c['PRIMARY']};
                outline: none;
            }}
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px;
                border-radius: 10px;
                font-size: 13px;
                min-height: 24px;
            }}
            QSpinBox:focus, QDoubleSpinBox:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
            
            /* Time / Date Edit */
            QTimeEdit, QDateEdit {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px;
                border-radius: 10px;
                font-size: 13px;
                min-height: 24px;
            }}
            QTimeEdit:focus, QDateEdit:focus {{
                border: 2px solid {c['PRIMARY']};
            }}
            
            /* Check Box */
            QCheckBox {{
                color: {c['TEXT_PRIMARY']};
                spacing: 8px;
                font-size: 13px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 2px solid {c['INPUT_BORDER']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {c['PRIMARY']};
                border: 2px solid {c['PRIMARY']};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {c['PRIMARY']};
            }}
            
            /* List Widget */
            QListWidget {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 12px;
                padding: 8px;
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 12px;
                border-radius: 8px;
                margin: 2px 0px;
                color: {c['TEXT_PRIMARY']};
            }}
            QListWidget::item:selected {{
                background-color: {c['SECONDARY']};
                color: {c['PRIMARY']};
                border: 1px solid {c['PRIMARY']};
            }}
            QListWidget::item:hover {{
                background-color: {c['HOVER']};
            }}
            
            /* Table Widget */
            QTableWidget {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 10px;
                gridline-color: {c['DIVIDER']};
                font-size: 13px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {c['TEXT_PRIMARY']};
            }}
            QTableWidget::item:selected {{
                background-color: {c['SECONDARY']};
                color: {c['PRIMARY']};
            }}
            QTableWidget::item:hover {{
                background-color: {c['HOVER']};
            }}
            QHeaderView::section {{
                background-color: {c['BG_LIGHT']};
                color: {c['PRIMARY']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {c['BORDER']};
                font-weight: 600;
                font-size: 12px;
            }}
            
            /* Scroll Bars */
            QScrollBar:vertical {{
                background-color: {c['BG_LIGHT']};
                width: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {c['SECONDARY']};
                border-radius: 5px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {c['PRIMARY']};
            }}
            QScrollBar:horizontal {{
                background-color: {c['BG_LIGHT']};
                height: 10px;
                border-radius: 5px;
                margin: 0;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {c['SECONDARY']};
                border-radius: 5px;
                min-width: 30px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background-color: {c['PRIMARY']};
            }}
            QScrollBar::add-line, QScrollBar::sub-line {{
                height: 0;
                width: 0;
            }}
            
            /* Slider */
            QSlider::groove:horizontal {{
                height: 4px;
                background: {c['BORDER']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {c['PRIMARY']};
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {c['PRIMARY']};
                border-radius: 2px;
            }}
            
            /* Progress Bar */
            QProgressBar {{
                background-color: {c['BG_LIGHT']};
                border: 2px solid {c['BORDER']};
                border-radius: 8px;
                text-align: center;
                color: {c['TEXT_PRIMARY']};
                font-weight: 600;
                font-size: 11px;
            }}
            QProgressBar::chunk {{
                background-color: {c['PRIMARY']};
                border-radius: 6px;
            }}
            
            /* Tab Widget */
            QTabWidget::pane {{
                border: none;
                background-color: {c['BG_DARK']};
            }}
            QTabBar::tab {{
                background-color: {c['TAB_BG']};
                color: {c['TAB_TEXT']};
                padding: 10px 24px;
                border: none;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                font-family: {IOS_FONT_STACK};
                font-size: 13px;
                font-weight: 500;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {c['TAB_SELECTED']};
                color: {c['TAB_TEXT_SELECTED']};
                font-weight: 600;
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {c['SECONDARY']};
            }}
            
            /* Splitter */
            QSplitter::handle {{
                background-color: {c['DIVIDER']};
                width: 2px;
                margin: 2px;
            }}
            QSplitter::handle:hover {{
                background-color: {c['PRIMARY']};
            }}
            
            /* Menu */
            QMenu {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 10px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 32px 8px 20px;
                border-radius: 6px;
            }}
            QMenu::item:selected {{
                background-color: {c['SECONDARY']};
                color: {c['PRIMARY']};
            }}
            QMenu::separator {{
                height: 1px;
                background: {c['DIVIDER']};
                margin: 4px 8px;
            }}
            
            /* Calendar Widget */
            QCalendarWidget {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border-radius: 12px;
            }}
            QCalendarWidget QToolButton {{
                color: {c['PRIMARY']};
                background-color: transparent;
                padding: 8px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {c['HOVER']};
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                selection-color: {c['TEXT_LIGHT']};
                selection-background-color: {c['PRIMARY']};
                font-size: 13px;
                outline: none;
            }}
            
            /* Status Bar */
            QStatusBar {{
                font-size: 13px;
                padding: 4px 12px;
            }}
            
            /* Tooltips */
            QToolTip {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 8px;
                padding: 6px 10px;
                font-size: 12px;
            }}
        """
    
    def get_status_bar_colors(self, theme_type: ThemeType = None) -> Dict[str, str]:
        """Get status bar specific colors for the given theme."""
        c = ThemeColors.get_colors(theme_type or self._current_theme)
        return {
            "bg": c["STATUSBAR_BG"],
            "text": c["STATUSBAR_TEXT"],
            "border": c["STATUSBAR_BORDER"],
        }
    
    def get_combo_colors(self, theme_type: ThemeType = None) -> Dict[str, str]:
        """Get combo box specific colors for the given theme."""
        c = ThemeColors.get_colors(theme_type or self._current_theme)
        return {
            "bg": c["INPUT_BG"],
            "text": c["TEXT_PRIMARY"],
            "border": c["INPUT_BORDER"],
        }
    
    def get_status_bar_style(self, theme_type: ThemeType = None) -> str:
        """Get stylesheet for the status bar."""
        sc = self.get_status_bar_colors(theme_type)
        return f"""
            QStatusBar {{
                background-color: {sc['bg']};
                color: {sc['text']};
                font-size: 13px;
                padding: 4px 12px;
                border-top: 1px solid {sc['border']};
            }}
        """
    
    def get_combo_style(self, theme_type: ThemeType = None) -> str:
        """Get stylesheet for the theme combo box."""
        cc = self.get_combo_colors(theme_type)
        sc = self.get_status_bar_colors(theme_type)
        return f"""
            QComboBox {{
                background-color: {cc['bg']};
                color: {cc['text']};
                border: 1px solid {cc['border']};
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 12px;
            }}
            QComboBox:hover {{
                border: 1px solid {sc['border']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 16px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {cc['bg']};
                color: {cc['text']};
                border: 1px solid {cc['border']};
                border-radius: 4px;
                selection-background-color: {c['SECONDARY'] if (c := ThemeColors.get_colors(theme_type or self._current_theme)) else '#eee'};
                selection-color: {c['PRIMARY'] if (c := ThemeColors.get_colors(theme_type or self._current_theme)) else '#000'};
                outline: none;
            }}
        """
    
    def get_theme_button_style(self, theme_type: ThemeType = None) -> str:
        """Get stylesheet for the theme toggle button."""
        sc = self.get_status_bar_colors(theme_type)
        return f"""
            QPushButton {{
                background: transparent; border: none;
                font-size: 16px; padding: 2px;
                color: {sc['text']};
            }}
            QPushButton:hover {{ 
                background: {sc['bg']}88; 
                border-radius: 6px; 
            }}
        """


# Global theme manager instance
_theme_manager: Optional[ThemeManager] = None


def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager


def set_theme(theme_type: str) -> None:
    """Set theme by string name."""
    theme_map = {
        "light": ThemeType.LIGHT,
        "dark": ThemeType.DARK,
        "medical_blue": ThemeType.MEDICAL_BLUE,
        "high_contrast": ThemeType.HIGH_CONTRAST,
        "warm_sepia": ThemeType.WARM_SEPIA,
        "forest_night": ThemeType.FOREST_NIGHT,
    }
    theme = theme_map.get(theme_type.lower(), ThemeType.LIGHT)
    get_theme_manager().set_theme(theme)


# Theme name mappings for combo boxes
THEME_NAMES = {
    ThemeType.LIGHT: "Light Pink",
    ThemeType.DARK: "Dark Mode",
    ThemeType.MEDICAL_BLUE: "Medical Blue",
    ThemeType.HIGH_CONTRAST: "High Contrast",
    ThemeType.WARM_SEPIA: "Warm Sepia",
    ThemeType.FOREST_NIGHT: "Forest Night",
}

THEME_NAME_TO_TYPE = {v: k for k, v in THEME_NAMES.items()}

THEME_LIST = [THEME_NAMES[t] for t in ThemeType]