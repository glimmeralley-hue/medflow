"""Add Event dialog for creating academic events."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QComboBox, QTimeEdit, QCheckBox, QSpinBox, QPushButton, QWidget,
    QSizePolicy, QMessageBox
)
from PySide6.QtCore import Qt, QTime
from medflow.database import Database
from .constants import EVENT_CATEGORIES
class AddEventDialog(QDialog):
    """Dialog for adding new academic events with reminders"""
    def __init__(self, database: Database, date: str):
        super().__init__()
        self.db = database
        self.date = date
        self.setWindowModality(Qt.ApplicationModal)
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle("Add Academic Event")
        self.setMinimumSize(450, 500)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)
        # Title
        title = QLabel("Add New Event")
        title.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        layout.addWidget(title)
        # Form container
        form_widget = QWidget()
        form_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-radius: 15px;
                border: 2px solid;
            }
            QLabel {
                font-size: 14px;
                font-weight: 600;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit, QComboBox, QTextEdit, QSpinBox, QTimeEdit {
                border: 2px solid;
            padding: 12px;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QLineEdit:focus, QComboBox:focus, QTextEdit:focus, QSpinBox:focus, QTimeEdit:focus {
                border: 2px solid;
            }
        """)
        form_layout = QVBoxLayout()
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(20, 20, 20, 20)
        # Event Title
        form_layout.addWidget(QLabel("Event Title:"))
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("e.g., Anatomy Lecture - Lower Limb")
        form_layout.addWidget(self.title_input)
        # Category
        form_layout.addWidget(QLabel("Category:"))
        self.category_combo = QComboBox()
        self.category_combo.addItems(EVENT_CATEGORIES)
        self.category_combo.setMinimumHeight(40)
        form_layout.addWidget(self.category_combo)
        # Subtopic
        form_layout.addWidget(QLabel("Subtopic (Optional):"))
        self.subtopic_input = QLineEdit()
        self.subtopic_input.setPlaceholderText("e.g., Femoral Triangle, Brachial Plexus")
        form_layout.addWidget(self.subtopic_input)
        # Time selection
        time_layout = QHBoxLayout()
        time_start_layout = QVBoxLayout()
        time_start_layout.addWidget(QLabel("Start Time:"))
        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(9, 0))
        self.time_start.setMinimumHeight(40)
        time_start_layout.addWidget(self.time_start)
        time_end_layout = QVBoxLayout()
        time_end_layout.addWidget(QLabel("End Time:"))
        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(10, 0))
        self.time_end.setMinimumHeight(40)
        time_end_layout.addWidget(self.time_end)
        time_layout.addLayout(time_start_layout)
        time_layout.addLayout(time_end_layout)
        form_layout.addLayout(time_layout)
        # Reminder settings
        reminder_layout = QHBoxLayout()
        self.reminder_checkbox = QCheckBox("Enable Reminder")
        self.reminder_checkbox.setChecked(True)
        self.reminder_checkbox.setStyleSheet("""
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        reminder_layout.addWidget(self.reminder_checkbox)
        reminder_layout.addWidget(QLabel("Minutes before:"))
        self.reminder_spin = QSpinBox()
        self.reminder_spin.setRange(1, 120)
        self.reminder_spin.setValue(15)
        self.reminder_spin.setSuffix(" min")
        self.reminder_spin.setMinimumHeight(35)
        self.reminder_spin.setStyleSheet("""
            QSpinBox {
                border: 2px solid;
            padding: 8px;
                border-radius: 8px;
            }
            QSpinBox:focus {
                border: 2px solid;
            }
        """)
        reminder_layout.addWidget(self.reminder_spin)
        reminder_layout.addStretch()
        form_layout.addLayout(reminder_layout)
        # Notes
        form_layout.addWidget(QLabel("Notes:"))
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional details, room number, preparation needed...")
        self.notes_input.setMinimumHeight(80)
        self.notes_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        form_layout.addWidget(self.notes_input)
        form_widget.setLayout(form_layout)
        layout.addWidget(form_widget)
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        save_btn = QPushButton("Save Event")
        save_btn.setMinimumHeight(48)
        save_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 14px 32px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                }
            QPushButton:pressed {
                }
        """)
        save_btn.clicked.connect(self.save_event)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(48)
        cancel_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 14px 32px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        layout.addStretch()
        self.setLayout(layout)
    def save_event(self):
        title = self.title_input.text().strip()
        if not title:
            QMessageBox.warning(self, "Missing Title", "Please enter an event title.")
            self.title_input.setFocus()
            return
        category = self.category_combo.currentText()
        subtopic = self.subtopic_input.text().strip()
        time_start = self.time_start.time().toString("HH:mm")
        time_end = self.time_end.time().toString("HH:mm")
        # Validate that end time is after start time
        if self.time_end.time() <= self.time_start.time():
            QMessageBox.warning(self, "Invalid Time Range",
                                "End time must be after start time.\n\nPlease adjust the times and try again.")
            self.time_end.setFocus()
            return
        notes = self.notes_input.toPlainText().strip()
        reminder_minutes = self.reminder_spin.value()
        reminder_enabled = self.reminder_checkbox.isChecked()
        self.db.add_event(title, category, subtopic, self.date, time_start, time_end, 
                         notes, reminder_minutes, reminder_enabled)
        self.accept()