"""Centralized StyleGuide for MedFlow UI components.

This module provides a factory for creating consistently-styled Qt widgets
that automatically respond to theme changes.
"""

from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QGroupBox, QLabel, QListWidget, QSpinBox, QDoubleSpinBox,
    QDateEdit, QTimeEdit, QCheckBox, QTableWidget
)
from PySide6.QtCore import Qt

from .theme_manager import get_theme_manager, ThemeType, IOS_FONT_STACK


class StyleGuide:
    """Factory for creating theme-aware styled widgets.
    
    Usage:
        sg = StyleGuide()
        btn = sg.button("primary", text="Save")
        input = sg.input(placeholder="Enter name...")
    """
    
    def __init__(self, theme_type: Optional[ThemeType] = None):
        self._theme_manager = get_theme_manager()
        self._theme_type = theme_type
        self._colors = self._theme_manager.get_colors(theme_type) if theme_type else self._theme_manager.get_colors()
    
    def _update_colors(self, theme_type: ThemeType = None):
        """Update colors when theme changes."""
        self._colors = self._theme_manager.get_colors(theme_type) if theme_type else self._theme_manager.get_colors()
    
    # ── Button Variants ──────────────────────────────────────────────────────
    
    def button_primary(self, parent=None, text: str = "", tooltip: str = "", 
                      minimum_height: int = 40, maximum_width: Optional[int] = None) -> QPushButton:
        """Primary action button - uses PRIMARY color."""
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(minimum_height)
        if maximum_width:
            btn.setMaximumWidth(maximum_width)
        btn.setStyleSheet(self._primary_button_style())
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def button_secondary(self, parent=None, text: str = "", tooltip: str = "",
                        minimum_height: int = 36) -> QPushButton:
        """Secondary/cancel button - uses SECONDARY color."""
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(minimum_height)
        btn.setStyleSheet(self._secondary_button_style())
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def button_success(self, parent=None, text: str = "", tooltip: str = "",
                      minimum_height: int = 36) -> QPushButton:
        """Success/confirm button - uses SUCCESS color."""
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(minimum_height)
        btn.setStyleSheet(self._success_button_style())
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def button_danger(self, parent=None, text: str = "", tooltip: str = "",
                     minimum_height: int = 36) -> QPushButton:
        """Danger/delete button - uses ERROR color."""
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(minimum_height)
        btn.setStyleSheet(self._danger_button_style())
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def button_info(self, parent=None, text: str = "", tooltip: str = "",
                   minimum_height: int = 36) -> QPushButton:
        """Info/action button - uses INFO color."""
        btn = QPushButton(text, parent)
        btn.setMinimumHeight(minimum_height)
        btn.setStyleSheet(self._info_button_style())
        if tooltip:
            btn.setToolTip(tooltip)
        return btn
    
    def button_checkable(self, parent=None, text: str = "") -> QPushButton:
        """Checkable button (for view toggles) - uses TAB styling."""
        btn = QPushButton(text, parent)
        btn.setCheckable(True)
        btn.setStyleSheet(self._checkable_button_style())
        return btn
    
    # ── Input Fields ──────────────────────────────────────────────────────────
    
    def input_text(self, parent=None, placeholder: str = "", 
                   minimum_height: int = 36) -> QLineEdit:
        """Text input field."""
        input_field = QLineEdit(parent)
        if placeholder:
            input_field.setPlaceholderText(placeholder)
        input_field.setMinimumHeight(minimum_height)
        input_field.setStyleSheet(self._input_style())
        return input_field
    
    def input_multiline(self, parent=None, placeholder: str = "") -> QTextEdit:
        """Multiline text input."""
        input_field = QTextEdit(parent)
        if placeholder:
            input_field.setPlaceholderText(placeholder)
        input_field.setStyleSheet(self._textarea_style())
        return input_field
    
    def combo(self, parent=None, items: Optional[list] = None) -> QComboBox:
        """Combo box selector."""
        combo = QComboBox(parent)
        combo.setMinimumHeight(36)
        if items:
            combo.addItems(items)
        combo.setStyleSheet(self._combo_style())
        return combo
    
    def spin_box(self, parent=None, minimum: int = 0, maximum: int = 100,
                value: int = 0) -> QSpinBox:
        """Integer spin box."""
        spin = QSpinBox(parent)
        spin.setMinimumHeight(36)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setStyleSheet(self._input_style())
        return spin
    
    def double_spin_box(self, parent=None, minimum: float = 0, maximum: float = 100,
                       value: float = 0, decimals: int = 1) -> QDoubleSpinBox:
        """Floating-point spin box."""
        spin = QDoubleSpinBox(parent)
        spin.setMinimumHeight(36)
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setDecimals(decimals)
        spin.setStyleSheet(self._input_style())
        return spin
    
    def date_edit(self, parent=None) -> QDateEdit:
        """Date picker."""
        date_edit = QDateEdit(parent)
        date_edit.setMinimumHeight(36)
        date_edit.setCalendarPopup(True)
        date_edit.setStyleSheet(self._input_style())
        return date_edit
    
    # ── Containers ───────────────────────────────────────────────────────────
    
    def group_box(self, parent=None, title: str = "") -> QGroupBox:
        """Group box container."""
        gb = QGroupBox(title, parent)
        gb.setStyleSheet(self._groupbox_style())
        return gb
    
    def list_widget(self, parent=None) -> QListWidget:
        """List widget."""
        lw = QListWidget(parent)
        lw.setStyleSheet(self._list_widget_style())
        return lw
    
    def table_widget(self, parent=None, columns: int = 0, 
                    headers: Optional[list] = None) -> QTableWidget:
        """Table widget."""
        table = QTableWidget(parent)
        if columns > 0:
            table.setColumnCount(columns)
        if headers:
            table.setHorizontalHeaderLabels(headers)
        table.setStyleSheet(self._table_widget_style())
        return table
    
    def label_title(self, parent=None, text: str = "") -> QLabel:
        """Section title label."""
        lbl = QLabel(text, parent)
        lbl.setStyleSheet(self._title_style())
        return lbl
    
    def label_caption(self, parent=None, text: str = "") -> QLabel:
        """Caption/subtitle label."""
        lbl = QLabel(text, parent)
        lbl.setStyleSheet(self._caption_style())
        return lbl
    
    # ── Private Style Generators ──────────────────────────────────────────────
    
    def _primary_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['PRIMARY']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{ background-color: {c['PRIMARY_LIGHT']}; }}
            QPushButton:pressed {{ background-color: {c['PRIMARY_DARK']}; }}
        """
    
    def _secondary_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['SECONDARY_LIGHT']};
                color: {c['TEXT_SECONDARY']};
                border: 2px solid {c['SECONDARY']};
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{ background-color: {c['SECONDARY']}; }}
        """
    
    def _success_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['SUCCESS']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{ background-color: {c['PRIMARY']}; }}
        """
    
    def _danger_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['ERROR']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{ background-color: {c['PRIMARY_DARK']}; }}
        """
    
    def _info_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['INFO']};
                color: {c['TEXT_LIGHT']};
                border: none;
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:hover {{ background-color: {c['PRIMARY']}; }}
        """
    
    def _checkable_button_style(self) -> str:
        c = self._colors
        return f"""
            QPushButton {{
                background-color: {c['TAB_BG']};
                color: {c['TAB_TEXT']};
                border: 2px solid {c['BORDER']};
                padding: 10px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QPushButton:checked {{
                background-color: {c['TAB_SELECTED']};
                color: {c['TAB_TEXT_SELECTED']};
            }}
            QPushButton:hover {{ background-color: {c['HOVER']}; }}
        """
    
    def _input_style(self) -> str:
        c = self._colors
        return f"""
            QLineEdit, QTextEdit, QDoubleSpinBox, QDateEdit {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QLineEdit:focus, QTextEdit:focus {{ border: 2px solid {c['PRIMARY']}; }}
        """
    
    def _textarea_style(self) -> str:
        return self._input_style()
    
    def _combo_style(self) -> str:
        c = self._colors
        return f"""
            QComboBox {{
                background-color: {c['INPUT_BG']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['INPUT_BORDER']};
                padding: 8px 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
            }}
            QComboBox:focus {{ border: 2px solid {c['PRIMARY']}; }}
            QComboBox QAbstractItemView {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                selection-background-color: {c['SECONDARY']};
                selection-color: {c['PRIMARY']};
            }}
        """
    
    def _groupbox_style(self) -> str:
        c = self._colors
        return f"""
            QGroupBox {{
                font-size: 16px;
                font-weight: 600;
                color: {c['PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 12px;
                margin-top: 15px;
                padding-top: 15px;
                font-family: {IOS_FONT_STACK};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }}
        """
    
    def _list_widget_style(self) -> str:
        c = self._colors
        return f"""
            QListWidget {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 12px;
                padding: 8px;
                font-size: 14px;
                font-family: {IOS_FONT_STACK};
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
            }}
            QListWidget::item:hover {{ background-color: {c['HOVER']}; }}
        """
    
    def _table_widget_style(self) -> str:
        c = self._colors
        return f"""
            QTableWidget {{
                background-color: {c['BG_WHITE']};
                color: {c['TEXT_PRIMARY']};
                border: 2px solid {c['BORDER']};
                border-radius: 10px;
                gridline-color: {c['DIVIDER']};
                font-size: 13px;
                font-family: {IOS_FONT_STACK};
            }}
            QHeaderView::section {{
                background-color: {c['BG_LIGHT']};
                color: {c['PRIMARY']};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {c['BORDER']};
                font-weight: 600;
            }}
        """
    
    def _title_style(self) -> str:
        c = self._colors
        return f"""
            font-size: 28px;
            font-weight: 600;
            color: {c['PRIMARY']};
            font-family: {IOS_FONT_STACK};
        """
    
    def _caption_style(self) -> str:
        c = self._colors
        return f"""
            font-size: 14px;
            color: {c['TEXT_SECONDARY']};
            font-family: {IOS_FONT_STACK};
        """
    
    def get_colors(self) -> Dict[str, str]:
        """Get current theme colors."""
        return self._colors
    
    def get_theme_manager(self):
        """Get the theme manager instance."""
        return self._theme_manager