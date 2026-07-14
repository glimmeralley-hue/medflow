"""Full-page schedule planner with large calendar and reminders."""
from datetime import datetime, timedelta
from collections import defaultdict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QListWidget, QListWidgetItem, QGroupBox,
    QSplitter, QStackedWidget, QMessageBox, QSystemTrayIcon, QMenu
)
from PySide6.QtCore import Qt, QTimer, Signal
from medflow.database import Database
from .constants import CATEGORY_COLORS
from .add_event_dialog import AddEventDialog
class FullPageSchedulePlanner(QWidget):
    """Full-page dedicated schedule planner with large calendar and reminders"""
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.current_view = "month"  # month, week, day
        self.init_ui()
        self.load_schedule()
        self.start_reminder_timer()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(30, 30, 30, 30)
        # Header with title and view controls
        header = QHBoxLayout()
        title = QLabel("Medical School Planner")
        title.setStyleSheet("""
            font-size: 32px; 
            font-weight: 700; 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(title)
        header.addStretch()
        # View toggle buttons
        self.month_btn = QPushButton("Month")
        self.week_btn = QPushButton("Week")
        self.day_btn = QPushButton("Day")
        for btn in [self.month_btn, self.week_btn, self.day_btn]:
            btn.setMinimumHeight(42)
            btn.setMinimumWidth(90)
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid;
            padding: 10px 20px;
                    font-weight: 600;
                    border-radius: 10px;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                }
                QPushButton:checked {
                    color: white;
                    border: 2px solid;
            }
                QPushButton:hover:!checked {
                    }
            """)
            btn.setCheckable(True)
            header.addWidget(btn)
        self.month_btn.setChecked(True)
        self.month_btn.clicked.connect(lambda: self.set_view("month"))
        self.week_btn.clicked.connect(lambda: self.set_view("week"))
        self.day_btn.clicked.connect(lambda: self.set_view("day"))
        # Add Event button
        add_btn = QPushButton("Add Event")
        add_btn.setMinimumHeight(48)
        add_btn.setMinimumWidth(150)
        add_btn.setToolTip("Add a new event for the selected date  (Ctrl+N)")
        add_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 14px 28px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                }
            QPushButton:pressed {
                }
        """)
        add_btn.clicked.connect(self.show_add_event_dialog)
        header.addWidget(add_btn)
        layout.addLayout(header)
        # Main content area - splitter for calendar and details
        splitter = QSplitter(Qt.Horizontal)
        # Left side - Large Calendar
        calendar_container = QWidget()
        calendar_layout = QVBoxLayout()
        calendar_layout.setSpacing(15)
        # Navigation
        nav_layout = QHBoxLayout()
        self.prev_btn = QPushButton("Previous")
        self.next_btn = QPushButton("Next")
        self.today_btn = QPushButton("Today")
        for btn in [self.prev_btn, self.today_btn, self.next_btn]:
            btn.setMinimumHeight(45)
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid;
            padding: 12px 24px;
                    font-weight: 600;
                    border-radius: 12px;
                    font-size: 14px;
                    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                }
                QPushButton:hover {
                    }
                QPushButton:pressed {
                    color: white;
                }
            """)
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.today_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        calendar_layout.addLayout(nav_layout)
        # Large Calendar Widget
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumHeight(600)
        self.calendar.setGridVisible(True)
        self.calendar.setFirstDayOfWeek(Qt.Monday)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.LongDayNames)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.ISOWeekNumbers)
        self.calendar.setStyleSheet("""
            QCalendarWidget {
                font-size: 16px;
                border: 2px solid;
            border-radius: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                padding: 10px;
            }
            QCalendarWidget QToolButton {
                color: white;
                padding: 12px 20px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 10px;
                border: none;
                margin: 5px;
            }
            QCalendarWidget QToolButton:hover {
                }
            QCalendarWidget QToolButton:pressed {
                }
            QCalendarWidget QMenu {
                background-color: white;
                border: 2px solid;
            border-radius: 10px;
                padding: 10px;
            }
            QCalendarWidget QMenu::item {
                padding: 10px;
                border-radius: 8px;
            }
            QCalendarWidget QMenu::item:selected {
                }
            QCalendarWidget QAbstractItemView {
                background-color: white;
                selection-color: white;
                selection-font-size: 15px;
                padding: 15px;
                border-radius: 10px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                padding: 12px;
                border-radius: 10px;
            }
            QCalendarWidget QAbstractItemView:disabled {
                }
            QCalendarWidget #qt_calendar_navigationbar {
                background: padding: 15px;
                border-radius: 15px 15px 0 0;
            }
            QCalendarWidget #qt_calendar_monthbutton {
                color: white;
                font-size: 18px;
                font-weight: 700;
                padding: 8px 15px;
            }
            QCalendarWidget #qt_calendar_yearbutton {
                color: white;
                font-size: 18px;
                font-weight: 700;
                padding: 8px 15px;
            }
            QCalendarWidget QWidget {
                alternate-}
        """)
        self.prev_btn.clicked.connect(self.calendar.showPreviousMonth)
        self.next_btn.clicked.connect(self.calendar.showNextMonth)
        self.today_btn.clicked.connect(self.calendar.showSelectedDate)
        self.calendar.clicked.connect(self.on_date_selected)
        calendar_layout.addWidget(self.calendar)
        calendar_container.setLayout(calendar_layout)
        splitter.addWidget(calendar_container)
        # Right side - Events list and details
        details_container = QWidget()
        details_layout = QVBoxLayout()
        details_layout.setSpacing(20)
        # Selected date display
        self.date_label = QLabel("Selected Date: " + self.selected_date)
        self.date_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: 600; 
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        details_layout.addWidget(self.date_label)
        # Timer section - COMPACT VERSION
        timer_group = QGroupBox("Timer")
        timer_group.setStyleSheet("""
            QGroupBox { 
                font-size: 14px; 
                font-weight: 600; 
                padding-top: 8px;
                border: 2px solid;
            border-radius: 10px;
                margin-top: 5px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        timer_layout = QVBoxLayout()
        timer_layout.setSpacing(5)
        timer_layout.setContentsMargins(8, 8, 8, 8)
        # Current event display - compact
        self.current_event_label = QLabel("No event selected")
        self.current_event_label.setStyleSheet("""
            font-size: 11px;
            padding: 2px;
            font-style: italic;
        """)
        self.current_event_label.setWordWrap(True)
        timer_layout.addWidget(self.current_event_label)
        # Timer display - smaller
        self.session_timer_label = QLabel("25:00")
        self.session_timer_label.setAlignment(Qt.AlignCenter)
        self.session_timer_label.setStyleSheet("""
            font-size: 32px;
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            padding: 5px;
        """)
        timer_layout.addWidget(self.session_timer_label)
        # Timer controls - compact horizontal
        timer_controls = QHBoxLayout()
        timer_controls.setSpacing(5)
        self.start_timer_btn = QPushButton("Start")
        self.start_timer_btn.setMinimumHeight(32)
        self.start_timer_btn.setMaximumWidth(50)
        self.start_timer_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                }
        """)
        self.start_timer_btn.setToolTip("Start")
        self.start_timer_btn.clicked.connect(self.start_event_timer)
        self.stop_timer_btn = QPushButton("Pause")
        self.stop_timer_btn.setMinimumHeight(32)
        self.stop_timer_btn.setMaximumWidth(50)
        self.stop_timer_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                }
        """)
        self.stop_timer_btn.setToolTip("Pause")
        self.stop_timer_btn.clicked.connect(self.stop_event_timer)
        self.reset_timer_btn = QPushButton("Reset")
        self.reset_timer_btn.setMinimumHeight(32)
        self.reset_timer_btn.setMaximumWidth(50)
        self.reset_timer_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 5px;
                font-weight: 700;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover {
                }
        """)
        self.reset_timer_btn.setToolTip("Reset")
        self.reset_timer_btn.clicked.connect(self.reset_event_timer)
        timer_controls.addWidget(self.start_timer_btn)
        timer_controls.addWidget(self.stop_timer_btn)
        timer_controls.addWidget(self.reset_timer_btn)
        timer_layout.addLayout(timer_controls)
        # Timer presets - compact
        presets_layout = QHBoxLayout()
        presets_layout.setSpacing(5)
        self.preset_25 = QPushButton("25 min")
        self.preset_50 = QPushButton("50 min")
        for btn in [self.preset_25, self.preset_50]:
            btn.setMinimumHeight(28)
            btn.setMaximumWidth(60)
            btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid;
            padding: 3px;
                    font-weight: 500;
                    border-radius: 5px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    }
            """)
        self.preset_25.clicked.connect(lambda: self.set_timer_preset(25))
        self.preset_50.clicked.connect(lambda: self.set_timer_preset(50))
        presets_layout.addWidget(self.preset_25)
        presets_layout.addWidget(self.preset_50)
        presets_layout.addStretch()
        timer_layout.addLayout(presets_layout)
        timer_group.setLayout(timer_layout)
        details_layout.addWidget(timer_group)
        # Initialize timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_event_timer)
        self.timer_remaining = 25 * 60
        self.timer_duration_minutes = 25  # Track original duration for study hours
        self.current_timer_event = None
        # Upcoming reminders section with pulsing header
        reminders_group = QGroupBox("")
        reminders_header = QWidget()
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        reminders_icon = QLabel("Reminders")
        reminders_icon.setStyleSheet("font-size: 20px; font-weight: 700; ")
        header_layout.addWidget(reminders_icon)
        reminders_title = QLabel("Upcoming Reminders")
        reminders_title.setStyleSheet("""
            font-size: 16px; 
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header_layout.addWidget(reminders_title)
        header_layout.addStretch()
        # Pulsing indicator
        self.pulse_label = QLabel("●")
        self.pulse_label.setStyleSheet("""
            font-size: 14px;
            """)
        header_layout.addWidget(self.pulse_label)
        reminders_header.setLayout(header_layout)
        reminders_group.setStyleSheet("""
            QGroupBox { 
                padding-top: 15px;
                border: 2px solid;
            border-radius: 15px;
                }
        """)
        reminders_layout = QVBoxLayout()
        reminders_layout.addWidget(reminders_header)
        self.reminders_list = QListWidget()
        self.reminders_list.setMinimumHeight(140)
        self.reminders_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 2px solid;
            border-radius: 12px;
                padding: 12px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 12px;
                margin: 4px 0px;
                border-radius: 8px;
                border-left: 4px solid #FF6B9D;
            }
            QListWidget::item:hover {
                }
        """)
        reminders_layout.addWidget(self.reminders_list)
        # Check reminders button
        snooze_btn = QPushButton("Check Reminders")
        snooze_btn.setMinimumHeight(45)
        snooze_btn.setStyleSheet("""
            QPushButton {
                background: color: white;
                border: none;
                padding: 12px 24px;
                font-weight: 700;
                border-radius: 10px;
                font-size: 14px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }
            QPushButton:hover {
                background: }
            QPushButton:pressed {
                background: }
        """)
        snooze_btn.clicked.connect(self.check_reminders)
        reminders_layout.addWidget(snooze_btn)
        reminders_group.setLayout(reminders_layout)
        details_layout.addWidget(reminders_group)
        # Events for selected date
        events_group = QGroupBox("Events for Selected Date")
        events_group.setStyleSheet("""
            QGroupBox { 
                font-size: 16px; 
                font-weight: 600; 
                padding-top: 15px;
                border: 2px solid;
            border-radius: 12px;
            }
        """)
        events_layout = QVBoxLayout()
        self.events_list = QListWidget()
        self.events_list.setMinimumHeight(250)
        self.events_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 2px solid;
            border-radius: 12px;
                padding: 12px;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 15px;
                margin: 5px 0px;
                border-radius: 10px;
                border: 2px solid;
            }
            QListWidget::item:selected {
                border: 2px solid;
            }
            QListWidget::item:hover {
                }
        """)
        self.events_list.itemClicked.connect(self.on_event_selected)
        self.events_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self._events_context_menu)
        events_layout.addWidget(self.events_list)
        events_group.setLayout(events_layout)
        details_layout.addWidget(events_group)
        # Quick stats
        stats_label = QLabel("Click any event to start a focus timer for that session. You'll get reminders before events start.")
        stats_label.setStyleSheet("""
            font-size: 13px; 
            padding: 15px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        stats_label.setWordWrap(True)
        details_layout.addWidget(stats_label)
        details_layout.addStretch()
        details_container.setLayout(details_layout)
        splitter.addWidget(details_container)
        # Set splitter ratio (60% calendar, 40% details)
        splitter.setSizes([900, 600])
        layout.addWidget(splitter)
        self.setLayout(layout)
    def set_view(self, view: str):
        """Switch between month/week/day views"""
        self.current_view = view
        self.month_btn.setChecked(view == "month")
        self.week_btn.setChecked(view == "week")
        self.day_btn.setChecked(view == "day")
        if view == "month":
            self.calendar.showSelectedDate()
    def on_date_selected(self, date):
        """Handle date selection from calendar"""
        self.selected_date = date.toString("yyyy-MM-dd")
        self.date_label.setText("Selected Date: " + self.selected_date)
        self.load_schedule()
    def on_event_selected(self, item):
        """Handle event selection - update timer with event info"""
        event_id = item.data(Qt.UserRole)
        events = self.db.get_events(self.selected_date)
        for event in events:
            if event['id'] == event_id:
                self.current_timer_event = event
                self.current_event_label.setText(
                    f"Timing: {event['title']}\n{event['time_start']} - {event['time_end']}"
                )
                self.timer_remaining = 25 * 60
                self.update_timer_display()
                break
    def load_schedule(self):
        """Load events for selected date and upcoming reminders"""
        # Load events for selected date
        self.events_list.clear()
        events = self.db.get_events(self.selected_date)
        for event in events:
            reminder_text = " [Reminder]" if event.get('reminder_enabled') else ""
            time_str = f"{event['time_start']} - {event['time_end']}"
            completed = bool(event.get('completed'))
            done_mark = "[Done]" if completed else ""
            # Calculate duration for display
            try:
                h1, m1 = map(int, event['time_start'].split(":"))
                h2, m2 = map(int, event['time_end'].split(":"))
                dur = (h2 * 60 + m2) - (h1 * 60 + m1)
                dur_str = f" · {dur}min" if dur > 0 else ""
            except Exception:
                dur_str = ""
            text = f"{done_mark}{reminder_text}{time_str}{dur_str}\n{event['title']}  [{event['category']}]"
            if event.get('subtopic'):
                text += f"\n  └ {event['subtopic']}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, event['id'])
            # Color-code by category
            colors = CATEGORY_COLORS.get(event['category'], CATEGORY_COLORS["Other"])
            if completed:
                item.setForeground(QColor("#8A8A8A"))
                item.setBackground(QColor("#F5F5F5"))
                font = item.font()
                font.setStrikeOut(True)
                item.setFont(font)
            else:
                item.setForeground(QColor(colors["fg"]))
                item.setBackground(QColor(colors["bg"]))
            self.events_list.addItem(item)
        # Load upcoming reminders
        self.reminders_list.clear()
        upcoming = self.db.get_upcoming_events(minutes_ahead=60)
        for event in upcoming:
            text = f"{event['time_start']} - {event['title']}"
            self.reminders_list.addItem(text)
        if not upcoming:
            self.reminders_list.addItem("No upcoming reminders")
    def show_add_event_dialog(self):
        """Show dialog to add new event"""
        dialog = AddEventDialog(self.db, self.selected_date)
        if dialog.exec():
            self.load_schedule()
    def _events_context_menu(self, pos):
        """Right-click context menu on the events list"""
        item = self.events_list.itemAt(pos)
        if not item:
            return
        event_id = item.data(Qt.UserRole)
        events = self.db.get_events(self.selected_date)
        target = next((e for e in events if e['id'] == event_id), None)
        if not target:
            return
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: white;
                border: 2px solid;
            border-radius: 10px;
                padding: 6px;
                font-size: 14px;
                }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                }
        """)
        if target.get('completed'):
            action_toggle = menu.addAction("Mark as Incomplete")
        else:
            action_toggle = menu.addAction("Mark as Complete")
        action = menu.exec(self.events_list.mapToGlobal(pos))
        if action == action_toggle:
            new_state = not bool(target.get('completed'))
            self.db.mark_event_completed(event_id, new_state)
            self.load_schedule()
    def start_reminder_timer(self):
        """Start timer to check for reminders every minute"""
        self.reminder_timer = QTimer()
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)
        # Start pulse animation for visual alert
        self.pulse_timer = QTimer()
        self.pulse_timer.timeout.connect(self.animate_pulse)
        self.pulse_timer.start(1000)
        self.pulse_state = 0
    def animate_pulse(self):
        """Animate the reminder pulse indicator"""
        self.pulse_state = (self.pulse_state + 1) % 2
        if self.pulse_state == 0:
            self.pulse_label.setStyleSheet("""
                font-size: 20px;
                font-weight: bold;
            """)
        else:
            self.pulse_label.setStyleSheet("""
                font-size: 16px;
                font-weight: normal;
            """)
    def start_event_timer(self):
        """Start the Pomodoro timer for the selected event"""
        if not self.timer.isActive():
            self.timer_duration_minutes = self.timer_remaining // 60
            self.timer.start(1000)
    def stop_event_timer(self):
        """Stop the timer"""
        self.timer.stop()
    def reset_event_timer(self):
        """Reset timer to 25 minutes"""
        self.timer.stop()
        self.timer_remaining = 25 * 60
        self.update_timer_display()
    def set_timer_preset(self, minutes: int):
        """Set timer to specific preset"""
        self.timer.stop()
        self.timer_remaining = minutes * 60
        self.timer_duration_minutes = minutes
        self.update_timer_display()
    def update_event_timer(self):
        """Update the timer countdown"""
        if self.timer_remaining > 0:
            self.timer_remaining -= 1
            self.update_timer_display()
        else:
            self.timer.stop()
            total_minutes = self.timer_duration_minutes
            hours = total_minutes / 60.0
            if self.current_timer_event and hours > 0:
                today = datetime.now().strftime("%Y-%m-%d")
                subject = self.current_timer_event.get('title', 'Study Session')
                self.db.add_study_hours(
                    date=today,
                    hours=hours,
                    subject=subject,
                    notes=f"Pomodoro timer session ({total_minutes} minutes)"
                )
                title = self.current_timer_event['title']
                QMessageBox.information(
                    self,
                    "Session Complete",
                    f"Great work! You've completed a {total_minutes}-minute study session for:\n\n"
                    f"{title}\n\n"
                    f"{hours:.1f} hours have been added to your study log!"
                )
            else:
                QMessageBox.information(
                    self,
                    "Timer Finished",
                    f"Your {total_minutes}-minute timer has finished!"
                )
    def update_timer_display(self):
        """Update the timer label"""
        minutes = self.timer_remaining // 60
        seconds = self.timer_remaining % 60
        self.session_timer_label.setText(f"{minutes:02d}:{seconds:02d}")
    def check_reminders(self):
        """Check for upcoming events and show notifications"""
        upcoming = self.db.get_upcoming_events(minutes_ahead=15)
        for event in upcoming:
            if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
                self.tray_icon.showMessage(
                    "Upcoming Event",
                    f"{event['title']} at {event['time_start']}",
                    QSystemTrayIcon.Information,
                    5000
                )
        self.load_schedule()