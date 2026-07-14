"""Study Streak Heatmap widget - GitHub-style visualization of daily study hours."""
from datetime import date, timedelta
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from medflow.database import Database
from .theme_manager import get_theme_manager, IOS_FONT_STACK


class StreakHeatmap(QWidget):
    """GitHub-style heatmap showing study hours for the past 90 days."""
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.theme_manager = get_theme_manager()
        self._colors = self.theme_manager.get_colors(self.theme_manager.get_theme())
        self._streak = 0
        self.init_ui()
        
        # Connect to theme changes
        self.theme_manager.theme_changed_connect(self._on_theme_changed)
    
    def _on_theme_changed(self, theme_type):
        """Update styles when theme changes."""
        self._colors = self.theme_manager.get_colors(theme_type)
        self._update_styles()
    
    def _update_styles(self):
        """Apply theme-aware styles."""
        c = self._colors
        self.streak_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {c['PRIMARY']};
            font-family: {IOS_FONT_STACK};
        """)
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {c['TEXT_PRIMARY']};
            font-family: {IOS_FONT_STACK};
        """)
    
    def init_ui(self):
        c = self._colors
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header with title and streak count
        header = QHBoxLayout()
        self.title_label = QLabel("Study Streak")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {c['TEXT_PRIMARY']};
            font-family: {IOS_FONT_STACK};
        """)
        header.addWidget(self.title_label)
        
        header.addStretch()
        
        self.streak_label = QLabel("🔥 0 days")
        self.streak_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {c['PRIMARY']};
            font-family: {IOS_FONT_STACK};
        """)
        header.addWidget(self.streak_label)
        
        layout.addLayout(header)
        
        # Heatmap days label
        self.days_label = QLabel("Last 90 days")
        self.days_label.setStyleSheet(f"""
            font-size: 11px;
            color: {c['TEXT_SECONDARY']};
            font-family: {IOS_FONT_STACK};
        """)
        layout.addWidget(self.days_label)
        
        # Heatmap widget (custom painted)
        self.heatmap_widget = HeatmapWidget(self.db)
        layout.addWidget(self.heatmap_widget)
        
        self.setLayout(layout)
        
        # Load streak data
        self._load_streak()
    
    def _load_streak(self):
        """Load and display current streak."""
        self._streak = self.db.get_current_study_streak()
        self.streak_label.setText(f"🔥 {self._streak}-day streak")
    
    def refresh(self):
        """Refresh the heatmap data."""
        self.heatmap_widget.update()
        self._load_streak()


class HeatmapWidget(QWidget):
    """Custom widget that paints the heatmap grid."""
    
    COLS = 14  # Show 14 weeks
    CELL_SIZE = 16
    CELL_SPACING = 4
    BORDER_RADIUS = 3
    
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.study_data = {}
        self._load_data()
        self.setMinimumHeight(self.COLS * (self.CELL_SIZE + self.CELL_SPACING))
    
    def _load_data(self):
        """Load study hours data for the past 90 days."""
        self.study_data = self.db.get_study_hours_last_n_days(90)
    
    def paintEvent(self, event):
        """Paint the heatmap grid."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get colors from theme
        theme_manager = get_theme_manager()
        c = theme_manager.get_colors(theme_manager.get_theme())
        
        today = date.today()
        
        # Calculate date range: 14 weeks = 98 days
        start_date = today - timedelta(days=97)
        
        # Day labels
        day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
        # Calculate max hours for color scaling
        max_hours = max(self.study_data.values()) if self.study_data else 4.0
        
        margin_left = 45
        margin_top = 0
        
        for week in range(self.COLS):
            for day in range(7):
                current_date = start_date + timedelta(days=week * 7 + day)
                x = margin_left + week * (self.CELL_SIZE + self.CELL_SPACING)
                y = margin_top + day * (self.CELL_SIZE + self.CELL_SPACING)
                
                date_str = current_date.isoformat()
                hours = self.study_data.get(date_str, 0)
                
                # Determine color based on hours
                if hours > 4:
                    color = QColor(c['PRIMARY'])
                elif hours > 2:
                    color = QColor("#FF8FB2")  # Light pink for 2-4 hours
                elif hours > 0:
                    color = QColor(c['SECONDARY'])
                else:
                    # Light grey for no study
                    r = int(c['BG_LIGHT'][1:3], 16) if c['BG_LIGHT'].startswith('#') else 245
                    g = int(c['BG_LIGHT'][3:5], 16) if c['BG_LIGHT'].startswith('#') else 245
                    b = int(c['BG_LIGHT'][5:7], 16) if c['BG_LIGHT'].startswith('#') else 245
                    color = QColor(r, g, b)
                
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(
                    x, y, self.CELL_SIZE, self.CELL_SIZE,
                    self.BORDER_RADIUS, self.BORDER_RADIUS
                )
        
        # Draw day labels on the left
        painter.setPen(QColor(c['TEXT_SECONDARY']))
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        
        for day in range(7):
            y = margin_top + day * (self.CELL_SIZE + self.CELL_SPACING) + self.CELL_SIZE // 2
            painter.drawText(0, y, margin_left - 5, self.CELL_SIZE, Qt.AlignRight, day_labels[day])