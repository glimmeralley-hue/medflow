"""Active Recall Sidebar widget — high-yield facts and study debt tracking."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QListWidget, QListWidgetItem, QGroupBox, QMessageBox
)
from PySide6.QtCore import Qt
from medflow.database import Database
class ActiveRecallSidebar(QWidget):
    """Active recall sidebar — high-yield facts and study debt tracking"""
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.current_event_id = None
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        # Title
        title = QLabel("Active Recall")
        title.setStyleSheet("font-size: 18px; font-weight: 700; ")
        layout.addWidget(title)
        # High-yield facts section
        facts_group = QGroupBox("High-Yield Facts")
        facts_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                padding-top: 10px;
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
        facts_layout = QVBoxLayout()
        self.facts_list = QListWidget()
        self.facts_list.setMinimumHeight(120)
        self.facts_list.setStyleSheet("""
            QListWidget {
                border: 2px solid;
            border-radius: 8px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                }
        """)
        facts_layout.addWidget(self.facts_list)
        self.fact_input = QTextEdit()
        self.fact_input.setPlaceholderText("Write a high-yield fact here...")
        self.fact_input.setMaximumHeight(60)
        self.fact_input.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 2px solid;
            border-radius: 8px;
                padding: 8px;
                font-size: 12px;
            }
            QTextEdit:focus {
                border: 2px solid;
            }
        """)
        facts_layout.addWidget(self.fact_input)
        add_fact_btn = QPushButton("Add Fact")
        add_fact_btn.setMinimumHeight(36)
        add_fact_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 10px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                }
        """)
        add_fact_btn.clicked.connect(self.add_fact)
        facts_layout.addWidget(add_fact_btn)
        facts_group.setLayout(facts_layout)
        layout.addWidget(facts_group)
        # Study debt section
        debt_group = QGroupBox("Study Debt")
        debt_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 600;
                padding-top: 10px;
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
        debt_layout = QVBoxLayout()
        self.debt_list = QListWidget()
        self.debt_list.setMinimumHeight(100)
        self.debt_list.setStyleSheet("""
            QListWidget {
                border: 2px solid;
            border-radius: 8px;
                padding: 5px;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
                margin: 2px 0px;
            }
            QListWidget::item:hover {
                }
        """)
        debt_layout.addWidget(self.debt_list)
        # Resolve debt button
        resolve_btn = QPushButton("Resolve Selected")
        resolve_btn.setMinimumHeight(36)
        resolve_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                padding: 10px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                }
        """)
        resolve_btn.clicked.connect(self.resolve_debt)
        debt_layout.addWidget(resolve_btn)
        # Mark as missed button
        miss_btn = QPushButton("Mark as Missed")
        miss_btn.setMinimumHeight(36)
        miss_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid;
            padding: 10px;
                font-weight: 600;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover {
                }
        """)
        miss_btn.clicked.connect(self.mark_as_missed)
        debt_layout.addWidget(miss_btn)
        debt_group.setLayout(debt_layout)
        layout.addWidget(debt_group)
        layout.addStretch()
        self.setLayout(layout)
    def set_event(self, event_id: int):
        self.current_event_id = event_id
        self.load_facts()
        self.load_debt()
    def load_facts(self):
        self.facts_list.clear()
        if self.current_event_id is None:
            self.facts_list.addItem("Select an event to view facts")
            return
        facts = self.db.get_study_notes(self.current_event_id)
        for fact in facts:
            item = QListWidgetItem(f"- {fact}")
            self.facts_list.addItem(item)
        if not facts:
            self.facts_list.addItem("No high-yield facts yet")
    def load_debt(self):
        self.debt_list.clear()
        debts = self.db.get_study_debt()
        for debt in debts:
            text = f"{debt['title']} ({debt['date']})\n  {debt['reason']}"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, debt['event_id'])
            self.debt_list.addItem(item)
        if not debts:
            self.debt_list.addItem("No study debt - Great job!")
    def add_fact(self):
        if self.current_event_id is None:
            QMessageBox.warning(self, "No Event Selected", "Please select an event first.")
            return
        fact = self.fact_input.toPlainText().strip()
        if not fact:
            return
        self.db.add_study_note(self.current_event_id, fact)
        self.fact_input.clear()
        self.load_facts()
    def resolve_debt(self):
        current_item = self.debt_list.currentItem()
        if current_item is None:
            QMessageBox.warning(self, "No Selection", "Please select a debt item to resolve.")
            return
        event_id = current_item.data(Qt.UserRole)
        if event_id:
            self.db.resolve_study_debt(event_id)
            self.load_debt()
    def mark_as_missed(self):
        if self.current_event_id is None:
            QMessageBox.warning(self, "No Event Selected", "Please select an event first.")
            return
        reason = "Marked as missed by user"
        self.db.add_study_debt(self.current_event_id, reason)
        self.load_debt()
        QMessageBox.information(self, "Marked as Missed",
                                "Event has been moved to study debt.")