"""Centralized stylesheet system for MedFlow application."""

from typing import Dict


# iOS-style font stack for native look
IOS_FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI", Roboto, Helvetica, Arial, sans-serif'

class ThemeColors:
    """Centralized color scheme for the application."""
    
    # Primary colors (Pink theme)
    PRIMARY = "#FF6B9D"
    PRIMARY_LIGHT = "#FF8FA3"
    PRIMARY_DARK = "#FF5280"
    
    # Secondary colors
    SECONDARY = "#FFD1DC"
    SECONDARY_LIGHT = "#FFE4E8"
    SECONDARY_DARK = "#FFB6C1"
    
    # Background colors
    BG_DARK = "#0A0E14"
    BG_LIGHT = "#FFF5F7"
    BG_WHITE = "#FFFFFF"
    
    # Text colors - improved contrast
    TEXT_PRIMARY = "#2A2A2A"
    TEXT_SECONDARY = "#5A4A5A"
    TEXT_LIGHT = "#FFFFFF"
    
    # Accent colors
    ACCENT_CYAN = "#00D4FF"
    ACCENT_ORANGE = "#E65100"
    ACCENT_GREEN = "#2E7D32"
    
    # Status colors
    SUCCESS = "#4CAF50"
    WARNING = "#FF9800"
    ERROR = "#F44336"
    INFO = "#2196F3"


class Styles:
    """Centralized stylesheet management."""
    
    @staticmethod
    def get_button_style(
        bg_color: str = ThemeColors.PRIMARY,
        text_color: str = ThemeColors.TEXT_LIGHT,
        hover_color: str = ThemeColors.PRIMARY_LIGHT,
        border_color: str = "none",
        border_radius: int = 10
    ) -> str:
        """Get button stylesheet."""
        border_decl = f"border: 2px solid {border_color};" if border_color != "none" else "border: none;"
        return f"""
            QPushButton {{
                background-color: {bg_color};
                color: {text_color};
                {border_decl}
                padding: 10px 18px;
                font-weight: 600;
                border-radius: {border_radius}px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {hover_color}; }}
            QPushButton:pressed {{ opacity: 0.85; }}
            QPushButton:disabled {{ 
                background-color: {ThemeColors.TEXT_SECONDARY};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def get_input_style(
        bg_color: str = ThemeColors.BG_LIGHT,
        border_color: str = ThemeColors.SECONDARY,
        focus_color: str = ThemeColors.PRIMARY,
        border_radius: int = 10
    ) -> str:
        """Get input field stylesheet."""
        return f"""
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QTimeEdit, QDateEdit {{
                background-color: {bg_color};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 2px solid {border_color};
                padding: 12px;
                border-radius: {border_radius}px;
                font-size: 14px;
            }}
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, 
            QSpinBox:focus, QTimeEdit:focus, QDateEdit:focus {{
                border: 2px solid {focus_color};
            }}
        """
    
    @staticmethod
    def get_group_box_style(
        title_color: str = ThemeColors.PRIMARY,
        border_color: str = ThemeColors.SECONDARY,
        border_radius: int = 12
    ) -> str:
        """Get group box stylesheet."""
        return f"""
            QGroupBox {{ 
                font-size: 16px; 
                color: {title_color}; 
                font-weight: 600;
                border: 2px solid {border_color};
                border-radius: {border_radius}px;
                padding-top: 15px;
                margin-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """
    
    @staticmethod
    def get_calendar_style() -> str:
        """Get calendar widget stylesheet."""
        return f"""
            QCalendarWidget {{
                background-color: {ThemeColors.BG_WHITE};
                color: {ThemeColors.TEXT_PRIMARY};
                font-size: 13px;
                border: 2px solid {ThemeColors.SECONDARY};
                border-radius: 12px;
            }}
            QCalendarWidget QToolButton {{
                color: {ThemeColors.PRIMARY};
                background-color: {ThemeColors.BG_LIGHT};
                padding: 8px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }}
            QCalendarWidget QToolButton:hover {{
                background-color: {ThemeColors.SECONDARY};
            }}
            QCalendarWidget QAbstractItemView {{
                background-color: {ThemeColors.BG_WHITE};
                color: {ThemeColors.TEXT_PRIMARY};
                selection-color: {ThemeColors.TEXT_LIGHT};
                selection-background-color: {ThemeColors.PRIMARY};
                font-size: 13px;
                outline: none;
            }}
            QCalendarWidget QAbstractItemView:enabled {{
                padding: 4px;
            }}
            QCalendarWidget QWidget#qt_calendar_navigationbar {{
                background-color: {ThemeColors.BG_LIGHT};
                border-bottom: 1px solid {ThemeColors.SECONDARY};
                border-radius: 10px;
            }}
        """
    
    @staticmethod
    def get_table_style() -> str:
        """Get table widget stylesheet."""
        return f"""
            QTableWidget {{
                background-color: {ThemeColors.BG_WHITE};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 2px solid {ThemeColors.SECONDARY};
                border-radius: 10px;
                gridline-color: {ThemeColors.SECONDARY};
                font-size: 13px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QTableWidget::item:selected {{
                background-color: {ThemeColors.SECONDARY};
                color: {ThemeColors.PRIMARY};
            }}
            QTableWidget::item:hover {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
            }}
            QHeaderView::section {{
                background-color: {ThemeColors.BG_LIGHT};
                color: {ThemeColors.PRIMARY};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {ThemeColors.SECONDARY};
                font-weight: 600;
            }}
        """
    
    @staticmethod
    def get_list_style() -> str:
        """Get list widget stylesheet."""
        return f"""
            QListWidget {{
                background-color: {ThemeColors.BG_WHITE};
                color: {ThemeColors.TEXT_PRIMARY};
                border: 2px solid {ThemeColors.SECONDARY};
                border-radius: 10px;
                padding: 5px;
                font-size: 13px;
            }}
            QListWidget::item {{
                padding: 8px;
                border-radius: 5px;
            }}
            QListWidget::item:selected {{
                background-color: {ThemeColors.SECONDARY};
                color: {ThemeColors.PRIMARY};
                border: 2px solid {ThemeColors.PRIMARY};
            }}
            QListWidget::item:hover {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
            }}
        """
    
    @staticmethod
    def get_scroll_area_style() -> str:
        """Get scroll area stylesheet."""
        return f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
                width: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:vertical {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {ThemeColors.PRIMARY};
            }}
            QScrollBar:horizontal {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
                height: 10px;
                border-radius: 5px;
            }}
            QScrollBar::handle:horizontal {{
                background-color: {ThemeColors.SECONDARY};
                border-radius: 5px;
                min-width: 20px;
            }}
        """
    
    @staticmethod
    def get_label_style(
        color: str = ThemeColors.TEXT_PRIMARY,
        font_size: int = 14,
        font_weight: str = "normal"
    ) -> str:
        """Get label stylesheet."""
        return f"""
            QLabel {{
                color: {color};
                font-size: {font_size}px;
                font-weight: {font_weight};
            }}
        """
    
    @staticmethod
    def get_slider_style() -> str:
        """Get slider stylesheet."""
        return f"""
            QSlider::groove:horizontal {{
                height: 4px;
                background: {ThemeColors.SECONDARY};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {ThemeColors.PRIMARY};
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }}
            QSlider::sub-page:horizontal {{
                background: {ThemeColors.PRIMARY};
                border-radius: 2px;
            }}
        """
    
    @staticmethod
    def get_progress_bar_style() -> str:
        """Get progress bar stylesheet."""
        return f"""
            QProgressBar {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
                border: 2px solid {ThemeColors.SECONDARY};
                border-radius: 8px;
                text-align: center;
                color: {ThemeColors.TEXT_PRIMARY};
                font-weight: 600;
            }}
            QProgressBar::chunk {{
                background-color: {ThemeColors.PRIMARY};
                border-radius: 6px;
            }}
        """
    
    @staticmethod
    def get_main_window_style() -> str:
        """Get main window stylesheet."""
        return f"""
            QMainWindow {{
                background-color: {ThemeColors.BG_DARK};
            }}
            QWidget {{
                background-color: {ThemeColors.BG_DARK};
                color: {ThemeColors.TEXT_PRIMARY};
            }}
        """
    
    @staticmethod
    def get_tab_widget_style() -> str:
        """Get tab widget stylesheet."""
        return f"""
            QTabWidget::pane {{
                border: 2px solid {ThemeColors.SECONDARY};
                border-radius: 8px;
                background-color: {ThemeColors.BG_WHITE};
            }}
            QTabBar::tab {{
                background-color: {ThemeColors.SECONDARY_LIGHT};
                color: {ThemeColors.TEXT_SECONDARY};
                padding: 10px 20px;
                border: 2px solid {ThemeColors.SECONDARY};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: {ThemeColors.BG_WHITE};
                color: {ThemeColors.PRIMARY};
                border-bottom: 2px solid {ThemeColors.BG_WHITE};
            }}
            QTabBar::tab:hover {{
                background-color: {ThemeColors.SECONDARY};
            }}
        """
