"""Pulse Timer and Progress Ring widgets for MedFlow."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSizePolicy
)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QPainter, QColor, QPen
from .constants import TIMER_PRESETS
class ProgressRing(QWidget):
    """Custom progress ring widget — pink-themed with optional pulse alpha."""
    def __init__(self):
        super().__init__()
        self.progress    = 0.0
        self._pulse_alpha = 255  # 255 = fully visible, lower = dimmed for pulse
    def set_progress(self, value: float):
        self.progress = value
        self.update()
    def set_pulse_alpha(self, alpha: int):
        self._pulse_alpha = alpha
        self.update()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        margin = 12
        rect_size = min(w, h) - margin * 2
        # Background track
        painter.setPen(QPen(QColor("#FFE4E8"), 9))
        painter.drawEllipse(margin, margin, rect_size, rect_size)
        if self.progress <= 0:
            return
        start_angle = 90 * 16
        span_angle  = -int(self.progress * 360 * 16)
        a           = self._pulse_alpha
        # Glow bloom
        painter.setPen(QPen(QColor(255, 107, 157, max(0, min(50, int(a * 0.2)))), 18))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)
        # Soft halo
        painter.setPen(QPen(QColor(255, 107, 157, max(0, min(130, int(a * 0.5)))), 11))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)
        # Core arc
        painter.setPen(QPen(QColor(255, 107, 157, a), 7))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)
        # Highlight
        painter.setPen(QPen(QColor(255, 255, 255, max(0, min(220, int(a * 0.86)))), 2))
        painter.drawArc(margin, margin, rect_size, rect_size, start_angle, span_angle)
class PulseTimer(QWidget):
    """Pomodoro-style timer — pink-themed, with session counter and break mode."""
    timer_finished = Signal()
    # Modes
    MODE_WORK  = "work"
    MODE_BREAK = "break"
    PRESETS = TIMER_PRESETS
    def __init__(self):
        super().__init__()
        self.total_time     = 25 * 60
        self.time_remaining = 25 * 60
        self.break_time     = 5  * 60
        self.is_running     = False
        self.mode           = self.MODE_WORK
        self.sessions_done  = 0
        self._pulse_tick = 0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._pulse_ring)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.init_ui()
    # ── UI ──────────────────────────────────────────────────────────────────
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)
        # ── Header row ────────────────────────────────────────────────────
        header = QHBoxLayout()
        self._title_lbl = QLabel("Focus Timer")
        self._title_lbl.setStyleSheet(
            "font-size: 18px; font-weight: 700; "
        )
        header.addWidget(self._title_lbl)
        header.addStretch()
        self._session_lbl = QLabel("Sessions: 0")
        self._session_lbl.setStyleSheet(
            "font-size: 12px; "
            "padding:4px 10px; border-radius:10px;"
        )
        header.addWidget(self._session_lbl)
        layout.addLayout(header)
        # ── Mode badge ────────────────────────────────────────────────────
        self._mode_lbl = QLabel("FOCUS")
        self._mode_lbl.setAlignment(Qt.AlignCenter)
        self._mode_lbl.setStyleSheet(
            "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
            "color: white; "
            "padding: 4px 16px; border-radius: 10px;"
        )
        layout.addWidget(self._mode_lbl, 0, Qt.AlignCenter)
        # ── Progress ring ─────────────────────────────────────────────────
        self.progress_ring = ProgressRing()
        self.progress_ring.setFixedSize(210, 210)
        layout.addWidget(self.progress_ring, 0, Qt.AlignCenter)
        # ── Time label (drawn inside ring via overlay trick) ──────────────
        self.timer_label = QLabel("25:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet(
            "font-size: 48px; font-weight: 700; "
            "background: transparent; letter-spacing: 2px;"
        )
        layout.addWidget(self.timer_label)
        # ── Preset selector ───────────────────────────────────────────────
        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(self.PRESETS.keys()))
        self._preset_combo.setMinimumHeight(36)
        self._preset_combo.setStyleSheet("""
            QComboBox {
                border: 2px solid;
            padding: 6px 12px;
                border-radius: 10px;
                font-size: 13px;
            }
            QComboBox:focus { border: 2px solid;
            }
        """)
        self._preset_combo.currentTextChanged.connect(self._on_preset_changed)
        layout.addWidget(self._preset_combo)
        # ── Control buttons ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self.start_btn = QPushButton("Start")
        self.start_btn.setMinimumHeight(44)
        self.start_btn.setStyleSheet(self._btn_css("#FF6B9D", "white", "#FF8FA3"))
        self.start_btn.clicked.connect(self.start_timer)
        self.start_btn.setToolTip("Start / resume the timer  (Space)")
        btn_row.addWidget(self.start_btn)
        self.stop_btn = QPushButton("Pause")
        self.stop_btn.setMinimumHeight(44)
        self.stop_btn.setStyleSheet(self._btn_css("#FFE4E8", "#5A4A5A", "#FFD1DC", border="#FFD1DC"))
        self.stop_btn.clicked.connect(self.stop_timer)
        btn_row.addWidget(self.stop_btn)
        self.reset_btn = QPushButton("Reset")
        self.reset_btn.setMinimumHeight(44)
        self.reset_btn.setStyleSheet(self._btn_css("#FFE4E8", "#5A4A5A", "#FFD1DC", border="#FFD1DC"))
        self.reset_btn.clicked.connect(self.reset_timer)
        btn_row.addWidget(self.reset_btn)
        layout.addLayout(btn_row)
        # ── Break button ──────────────────────────────────────────────────
        self._break_btn = QPushButton("Take a Break")
        self._break_btn.setMinimumHeight(38)
        self._break_btn.setStyleSheet(self._btn_css("#FFF3E0", "#E65100", "#FFE0B2", border="#FFE0B2"))
        self._break_btn.clicked.connect(self._start_break)
        self._break_btn.setToolTip("Switch to a short break countdown")
        layout.addWidget(self._break_btn)
        layout.addStretch()
    # ── helpers ─────────────────────────────────────────────────────────────
    @staticmethod
    def _btn_css(bg, fg, hover_bg, border="none"):
        border_decl = f"border: 2px solid {border};" if border != "none" else "border: none;"
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                {border_decl}
                padding: 10px 18px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
            }}
            QPushButton:hover {{ background-color: {hover_bg}; }}
            QPushButton:pressed {{ opacity: 0.85; }}
        """
    def _on_preset_changed(self, text: str):
        work_min, break_min = self.PRESETS[text]
        self.break_time = break_min * 60
        self.stop_timer()
        self.total_time     = work_min * 60
        self.time_remaining = work_min * 60
        self.mode = self.MODE_WORK
        self._update_mode_ui()
        self.update_display()
    def _update_mode_ui(self):
        if self.mode == self.MODE_WORK:
            self._mode_lbl.setText("FOCUS")
            self._mode_lbl.setStyleSheet(
                "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
                "color: white; "
                "padding: 4px 16px; border-radius: 10px;"
            )
            self.timer_label.setStyleSheet(
                "font-size: 48px; font-weight: 700; "
                "background: transparent; letter-spacing: 2px;"
            )
        else:
            self._mode_lbl.setText("BREAK")
            self._mode_lbl.setStyleSheet(
                "font-size: 11px; font-weight: 700; letter-spacing: 2px;"
                "color: white; "
                "padding: 4px 16px; border-radius: 10px;"
            )
            self.timer_label.setStyleSheet(
                "font-size: 48px; font-weight: 700; "
                "background: transparent; letter-spacing: 2px;"
            )
    def _pulse_ring(self):
        """Animate ring color while running"""
        self._pulse_tick = (self._pulse_tick + 1) % 2
        alpha = 180 if self._pulse_tick == 0 else 255
        self.progress_ring.set_pulse_alpha(alpha)
    # ── Timer control ────────────────────────────────────────────────────────
    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            self.start_btn.setText("Running...")
            self.start_btn.setStyleSheet(self._btn_css("#FFD1DC", "#FF6B9D", "#FFB6C1"))
            self.timer.start(1000)
            self._pulse_timer.start(600)
    def stop_timer(self):
        self.is_running = False
        self.start_btn.setText("Start")
        self.start_btn.setStyleSheet(self._btn_css("#FF6B9D", "white", "#FF8FA3"))
        self.timer.stop()
        self._pulse_timer.stop()
        self.progress_ring.set_pulse_alpha(255)
    def reset_timer(self):
        self.stop_timer()
        self.mode = self.MODE_WORK
        self.time_remaining = self.total_time
        self._update_mode_ui()
        self.update_display()
    def _start_break(self):
        self.stop_timer()
        self.mode = self.MODE_BREAK
        self.time_remaining = self.break_time
        self.total_time = self.break_time
        self._update_mode_ui()
        self.update_display()
        self.start_timer()
    def set_preset(self, work_minutes: int, break_minutes: int):
        self.break_time = break_minutes * 60
        self.stop_timer()
        self.total_time     = work_minutes * 60
        self.time_remaining = work_minutes * 60
        self.mode = self.MODE_WORK
        self._update_mode_ui()
        self.update_display()
    def update_timer(self):
        if self.time_remaining > 0:
            self.time_remaining -= 1
            self.update_display()
        else:
            self.stop_timer()
            if self.mode == self.MODE_WORK:
                self.sessions_done += 1
                self._session_lbl.setText(f"Sessions: {self.sessions_done}")
            self.timer_finished.emit()
    def update_display(self):
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")
        progress = 1.0 - (self.time_remaining / self.total_time) if self.total_time > 0 else 0.0
        self.progress_ring.set_progress(max(0.0, min(1.0, progress)))