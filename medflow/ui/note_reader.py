"""Full-screen dialog for reading notes comfortably."""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame
)
from PySide6.QtCore import Qt
class NoteReaderDialog(QDialog):
    """Full-screen dialog for reading notes comfortably"""
    def __init__(self, note: dict, parent=None):
        super().__init__(parent)
        self.note = note
        self.setWindowTitle(self.note['title'])
        self.setMinimumSize(800, 600)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        # Header
        header = QHBoxLayout()
        title = QLabel(self.note['title'])
        title.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(title)
        header.addStretch()
        # Meta info
        meta = QLabel(f"{self.note['category']} | {self.note['date']}")
        meta.setStyleSheet("""
            font-size: 14px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        header.addWidget(meta)
        layout.addLayout(header)
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("")
        line.setMaximumHeight(2)
        layout.addWidget(line)
        # Content display
        content_display = QTextEdit()
        content_display.setPlainText(self.note['content'])
        content_display.setReadOnly(True)
        content_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid;
            border-radius: 15px;
                padding: 30px;
                font-size: 16px;
                font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.8;
            }
        """)
        layout.addWidget(content_display)
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(50)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 15px 40px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 16px;
            }
            QPushButton:hover {
                }
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        self.setLayout(layout)