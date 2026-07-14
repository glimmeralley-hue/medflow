"""Full-screen dialog for viewing exam details."""
from typing import List, Dict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QGroupBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
class ExamDetailDialog(QDialog):
    """Full-screen dialog for viewing exam details"""
    def __init__(self, exam_data: dict, parent=None):
        super().__init__(parent)
        self.exam = exam_data
        self.notes: List[Dict] = []  # in-memory notes for this session
        self.setWindowTitle(f"{exam_data['subject_name']} - Exam Details")
        self.setMinimumSize(500, 400)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(40, 30, 40, 30)
        # Header with score badge
        header = QHBoxLayout()
        # Title section
        title_layout = QVBoxLayout()
        subject_label = QLabel(self.exam['subject_name'])
        subject_label.setStyleSheet("""
            font-size: 28px;
            font-weight: 700;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(subject_label)
        type_label = QLabel(self.exam['exam_type'])
        type_label.setStyleSheet("""
            font-size: 16px;
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        """)
        title_layout.addWidget(type_label)
        header.addLayout(title_layout, stretch=1)
        # Score badge
        score = self.exam['score']
        passed = score >= 50
        score_widget = QWidget()
        score_widget.setStyleSheet(f"""
            QWidget {{
                background-color: {'#E8F5E9' if passed else '#FFEBEE'};
                border-radius: 15px;
                padding: 15px;
            }}
        """)
        score_layout = QVBoxLayout()
        score_layout.setContentsMargins(20, 15, 20, 15)
        score_num = QLabel(f"{score:.1f}%")
        score_num.setStyleSheet(f"""
            font-size: 36px;
            font-weight: 700;
            color: {'#1B5E20' if passed else '#B71C1C'};
        """)
        score_num.setAlignment(Qt.AlignCenter)
        score_text = QLabel("PASS" if passed else "FAIL")
        score_text.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {'#1B5E20' if passed else '#B71C1C'};
        """)
        score_text.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(score_num)
        score_layout.addWidget(score_text)
        score_widget.setLayout(score_layout)
        header.addWidget(score_widget)
        layout.addLayout(header)
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("")
        line.setMaximumHeight(2)
        layout.addWidget(line)
        # Details grid
        details_group = QGroupBox("Exam Details")
        details_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 15px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        detail_grid = QGridLayout()
        detail_grid.setSpacing(12)
        detail_grid.setContentsMargins(20, 25, 20, 20)
        fields = [
            ("Subject:", self.exam['subject_name']),
            ("Exam Type:", self.exam['exam_type']),
            ("Score:", f"{self.exam['score']:.1f}%"),
            ("Date:", self.exam['date']),
        ]
        for i, (label_text, value_text) in enumerate(fields):
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size: 14px; font-weight: 600;")
            val = QLabel(str(value_text))
            val.setStyleSheet("font-size: 14px; ")
            detail_grid.addWidget(lbl, i, 0)
            detail_grid.addWidget(val, i, 1)
        details_group.setLayout(detail_grid)
        layout.addWidget(details_group)
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(48)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 14px 32px;
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
        layout.addStretch()
        self.setLayout(layout)