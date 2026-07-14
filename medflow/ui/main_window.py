"""Main application window for MedFlow - tabbed interface with system tray."""

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QPushButton, QLabel,
    QVBoxLayout, QHBoxLayout, QSplitter, QSystemTrayIcon, QMenu,
    QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QAction

from medflow.database import Database
from medflow.utils.config import get_config
from .planner import FullPageSchedulePlanner
from .results import ResultsLedger
from .notes import NotesSection
from .flashcard_widget import FlashcardWidget
from .library import LibrarySection
from .profile import ProfilePage
from .timer import PulseTimer
from .academic_ledger import AcademicLedger
from .active_recall import ActiveRecallSidebar
from .theme_manager import (
    get_theme_manager, ThemeType, THEME_NAMES, THEME_NAME_TO_TYPE, THEME_LIST
)


class MedFlowMainWindow(QMainWindow):
    """Main application window with tabbed interface"""

    def __init__(self, database=None):
        super().__init__()
        self.db = database if database is not None else Database()
        self._cfg = get_config()
        self._theme_manager = get_theme_manager()
        self._suppress_combo_signal = False
        
        # Read saved theme
        saved_theme = self._cfg.get('ui.theme', 'light')
        theme_map = {
            "light": ThemeType.LIGHT,
            "dark": ThemeType.DARK,
            "medical_blue": ThemeType.MEDICAL_BLUE,
            "high_contrast": ThemeType.HIGH_CONTRAST,
            "warm_sepia": ThemeType.WARM_SEPIA,
            "forest_night": ThemeType.FOREST_NIGHT,
        }
        initial_theme = theme_map.get(saved_theme, ThemeType.LIGHT)
        self._theme_manager.set_theme(initial_theme)
        
        self.init_ui()
        self.setup_system_tray()
        
        # Apply initial theme
        self._apply_theme()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("MedFlow")
        w = self._cfg.get('ui.window_width', 1400)
        h = self._cfg.get('ui.window_height', 900)
        self.setGeometry(100, 100, w, h)

        # Load and set window icon
        icon_path = Path(__file__).parent.parent.parent / "medflow-icon.svg"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("main_tabs")

        # Tab 1: Full Page Schedule Planner
        self.schedule_planner = FullPageSchedulePlanner(self.db)
        self.tab_widget.addTab(self.schedule_planner, "Planner")

        # Tab 2: Results Ledger
        self.results_ledger = ResultsLedger(self.db)
        self.tab_widget.addTab(self.results_ledger, "Results")

        # Tab 3: Notes Section
        self.notes_section = NotesSection(self.db)
        self.tab_widget.addTab(self.notes_section, "Notes")

        # Tab 4: Flashcards
        self.flashcard_widget = FlashcardWidget(self.db)
        self.tab_widget.addTab(self.flashcard_widget, "Flashcards")

        # Tab 5: Library Section
        self.library_section = LibrarySection(self.db)
        self.tab_widget.addTab(self.library_section, "Library")

        # Tab 6: Profile Page
        self.profile_page = ProfilePage(self.db)
        self.tab_widget.addTab(self.profile_page, "Profile")

        self.setCentralWidget(self.tab_widget)

        # Status bar with clock + theme selector
        self._status_bar = self.statusBar()
        self._clock_label = QLabel()
        self._status_bar.addPermanentWidget(self._clock_label)
        self._update_clock()
        self._clock_timer = QTimer(self)
        self._clock_timer.timeout.connect(self._update_clock)
        self._clock_timer.start(30000)

        # Theme selector in status bar
        self._theme_label = QLabel("Theme:")
        self._status_bar.addWidget(self._theme_label)
        
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(THEME_LIST)
        self._theme_combo.setFixedHeight(26)
        theme_name = THEME_NAMES.get(self._theme_manager.get_theme(), "Light Pink")
        self._theme_combo.setCurrentText(theme_name)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        self._status_bar.addWidget(self._theme_combo)

        # Theme toggle button in status bar
        self._theme_btn = QPushButton("☀")
        self._theme_btn.setFixedSize(28, 28)
        self._theme_btn.setToolTip("Toggle theme")
        self._theme_btn.clicked.connect(self._toggle_theme)
        self._status_bar.addWidget(self._theme_btn)

        # Keyboard shortcut: Ctrl+N → add event on Planner tab
        add_event_shortcut = QAction("Add Event", self)
        add_event_shortcut.setShortcut("Ctrl+N")
        add_event_shortcut.triggered.connect(self._shortcut_add_event)
        self.addAction(add_event_shortcut)

        # Keyboard shortcut: Ctrl+D → toggle dark mode
        theme_shortcut = QAction("Toggle Theme", self)
        theme_shortcut.setShortcut("Ctrl+D")
        theme_shortcut.triggered.connect(self._toggle_theme)
        self.addAction(theme_shortcut)

        # Keyboard shortcut: F11 → toggle fullscreen
        fullscreen_shortcut = QAction("Toggle Fullscreen", self)
        fullscreen_shortcut.setShortcut("F11")
        fullscreen_shortcut.triggered.connect(self.toggle_fullscreen)
        self.addAction(fullscreen_shortcut)

    def _update_clock(self):
        now = datetime.now()
        day_str = now.strftime("%A, %B %d %Y")
        time_str = now.strftime("%I:%M %p")
        self._clock_label.setText(f"{day_str}   {time_str}")

    def _shortcut_add_event(self):
        """Ctrl+N: switch to the Planner tab and open Add Event dialog"""
        self.tab_widget.setCurrentIndex(0)
        if hasattr(self.schedule_planner, 'show_add_event_dialog'):
            self.schedule_planner.show_add_event_dialog()

    def create_dashboard_tab(self):
        """Create the main schedule tab with clean 3-pane layout"""
        dashboard_widget = QWidget()
        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)

        # Left pane - Academic Ledger
        self.academic_ledger = AcademicLedger(self.db)
        self.academic_ledger.event_selected.connect(self.on_event_selected)
        splitter.addWidget(self.academic_ledger)

        # Middle pane - Timer and Active Task
        middle_pane = QWidget()
        middle_layout = QVBoxLayout()
        middle_layout.setSpacing(20)
        middle_layout.setContentsMargins(20, 20, 20, 20)

        self.pulse_timer = PulseTimer()
        middle_layout.addWidget(self.pulse_timer)

        # Current task display
        self.current_task_label = QLabel("No event selected")
        self.current_task_label.setAlignment(Qt.AlignCenter)
        middle_layout.addWidget(self.current_task_label)

        middle_pane.setLayout(middle_layout)
        splitter.addWidget(middle_pane)

        # Right pane - Active Recall Sidebar
        self.active_recall = ActiveRecallSidebar(self.db)
        splitter.addWidget(self.active_recall)

        # Set splitter sizes (1:2:1 ratio)
        splitter.setSizes([400, 800, 400])

        main_layout.addWidget(splitter)
        dashboard_widget.setLayout(main_layout)

        return dashboard_widget

    def on_event_selected(self, event_id: int):
        """Handle event selection"""
        self.active_recall.set_event(event_id)

        # Update current task display
        events = self.db.get_events()
        for event in events:
            if event['id'] == event_id:
                self.current_task_label.setText(
                    f"Current: {event['title']} ({event['category']})"
                )
                break

    def setup_system_tray(self):
        """Setup system tray icon"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)

        # Set icon
        icon_path = Path(__file__).parent.parent.parent / "medflow-icon.svg"
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(QIcon.fromTheme("application-x-executable"))

        # Create tray menu
        tray_menu = QMenu()

        show_action = QAction("Show", self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)

        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.close)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _on_theme_changed(self, theme_name: str):
        """Handle theme selection from combo box."""
        if self._suppress_combo_signal:
            return
        theme = THEME_NAME_TO_TYPE.get(theme_name, ThemeType.LIGHT)
        self._theme_manager.set_theme(theme)
        
        # Update config
        config_key = theme.name.lower()
        self._cfg.set('ui.theme', config_key)
        # For backward compatibility, still set 'dark' key for DARK theme
        if theme == ThemeType.DARK:
            self._cfg.set('ui.theme', 'dark')
        else:
            self._cfg.set('ui.theme', theme.name.lower())
        
        self._apply_theme()

    def _apply_theme(self):
        """Apply current theme to the entire window."""
        theme = self._theme_manager.get_theme()
        c = self._theme_manager.get_colors(theme)
        
        # 1. Apply global stylesheet (covers all major widget types)
        global_style = self._theme_manager.get_global_stylesheet(theme)
        self.setStyleSheet(global_style)
        
        # 2. Re-apply status bar styling (it gets overridden by QStatusBar rule)
        self._status_bar.setStyleSheet(self._theme_manager.get_status_bar_style(theme))
        
        # 3. Style the theme label and clock
        sc = self._theme_manager.get_status_bar_colors(theme)
        self._theme_label.setStyleSheet(f"QLabel {{ color: {sc['text']}; font-size: 12px; }}")
        self._clock_label.setStyleSheet(f"QLabel {{ color: {sc['text']}; font-size: 13px; }}")
        
        # 4. Style the theme combo
        self._theme_combo.setStyleSheet(self._theme_manager.get_combo_style(theme))
        
        # 5. Style the theme toggle button
        self._theme_btn.setStyleSheet(self._theme_manager.get_theme_button_style(theme))
        
        # 6. Update toggle button icon
        dark_themes = {ThemeType.DARK, ThemeType.FOREST_NIGHT}
        self._theme_btn.setText("☾" if theme in dark_themes else "☀")
        
        # 7. Emit theme changed signal so other widgets can react
        # (theme_manager already emits via set_theme, but we handle
        #  the combo -> set_theme -> signal -> _apply_theme cycle properly)

    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _toggle_theme(self):
        """Cycle through themes"""
        themes = list(ThemeType)
        current_idx = themes.index(self._theme_manager.get_theme())
        next_theme = themes[(current_idx + 1) % len(themes)]
        self._theme_manager.set_theme(next_theme)
        
        # Update combo box (suppress signal to avoid double-apply)
        self._suppress_combo_signal = True
        self._theme_combo.setCurrentText(THEME_NAMES.get(next_theme, "Light Pink"))
        self._suppress_combo_signal = False
        
        # Update config
        self._cfg.set('ui.theme', next_theme.name.lower())
        
        self._apply_theme()

    def closeEvent(self, event):
        """Handle window close event - minimize to tray if available"""
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()