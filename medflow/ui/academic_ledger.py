"""Academic Ledger widget — calendar and event management."""
from datetime import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem
)
from PySide6.QtCore import Qt, Signal
from medflow.database import Database
from .add_event_dialog import AddEventDialog
class AcademicLedger(QWidget):
    """Calendar and event management widget"""
    event_selected = Signal(int)
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.init_ui()
        self.load_events()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        # Title
        title = QLabel("Schedule & Events")
        title.setStyleSheet("font-size: 18px; font-weight: 700; ")
        layout.addWidget(title)
        # Calendar — light pink theme
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumHeight(280)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: white;
                font-size: 13px;
                border: 2px solid;
            border-radius: 12px;
            }
            QCalendarWidget QToolButton {
                padding: 8px;
                font-size: 13px;
                font-weight: 600;
                border: none;
                border-radius: 6px;
            }
            QCalendarWidget QToolButton:hover {
                }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-color: white;
                selection-font-size: 13px;
                outline: none;
            }
            QCalendarWidget QAbstractItemView:enabled {
                padding: 4px;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                border-bottom: 1px solid #FFD1DC;
                border-radius: 10px;
            }
        """)
        self.calendar.clicked.connect(self.on_date_selected)
        layout.addWidget(self.calendar)
        # Events section
        events_label = QLabel("Events for Selected Date")
        events_label.setStyleSheet("font-size: 14px; font-weight: 600; margin-top: 6px;")
        layout.addWidget(events_label)
        # Event list
        self.event_list = QListWidget()
        self.event_list.setMinimumHeight(180)
        self.event_list.setStyleSheet("""
            QListWidget {
                border: 2px solid;
            border-radius: 10px;
                padding: 8px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 6px;
                margin: 2px 0px;
            }
            QListWidget::item:selected {
                }
            QListWidget::item:hover {
                }
        """)
        self.event_list.itemClicked.connect(self.on_event_selected)
        layout.addWidget(self.event_list)
        # Add event button
        self.add_event_btn = QPushButton("Add New Event")
        self.add_event_btn.setMinimumHeight(45)
        self.add_event_btn.setToolTip("Add a new academic event for the selected date (Ctrl+N)")
        self.add_event_btn.clicked.connect(self.show_add_event_dialog)
        self.add_event_btn.setStyleSheet("""
            QPushButton {
                border: none;
                padding: 12px 20px;
                font-weight: bold;
                border-radius: 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                }
        """)
        layout.addWidget(self.add_event_btn)
        layout.addStretch()
        self.setLayout(layout)
    def on_date_selected(self, date):
        self.selected_date = date.toString("yyyy-MM-dd")
        self.load_events()
    def on_event_selected(self, item):
        event_id = item.data(Qt.UserRole)
        self.event_selected.emit(event_id)
    def load_events(self):
        self.event_list.clear()
        events = self.db.get_events(self.selected_date)
        for event in events:
            item = QListWidgetItem(f"{event['time_start']} - {event['title']} ({event['category']})")
            item.setData(Qt.UserRole, event['id'])
            self.event_list.addItem(item)
    def show_add_event_dialog(self):
        dialog = AddEventDialog(self.db, self.selected_date)
        if dialog.exec():
            self.load_events()