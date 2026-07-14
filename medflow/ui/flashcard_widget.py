"""Flashcard widget for spaced repetition review."""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QDialog, QLineEdit,
    QMessageBox, QTextEdit, QInputDialog
)
from PySide6.QtCore import Qt
from datetime import date
from medflow.database import Database
from medflow.models.flashcard import Flashcard, FlashcardDeck
from .theme_manager import get_theme_manager, ThemeType
from .flashcard_importer import FlashcardImporter
class FlashcardWidget(QWidget):
    """Flashcard review widget with SM-2 spaced repetition."""
    IOS_FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.current_deck_id = None
        self.current_card_index = 0
        self.due_cards = []
        self.showing_answer = False
        self.theme_manager = get_theme_manager()
        self._colors = self.theme_manager.get_colors(self.theme_manager.get_theme())
        self.init_ui()
        self.load_decks()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        # Header
        header = QHBoxLayout()
        title = QLabel("Flashcard Review")
        title.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {self._colors['PRIMARY']};")
        header.addWidget(title)
        header.addStretch()
        # Add deck button
        add_deck_btn = QPushButton("New Deck")
        add_deck_btn.setStyleSheet(f"""
            background-color: {self._colors['PRIMARY']}; 
            color: {self._colors['TEXT_LIGHT']}; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 10px; 
            font-weight: 600;
            font-family: {self.IOS_FONT_STACK};
        """)
        add_deck_btn.clicked.connect(self.add_deck)
        header.addWidget(add_deck_btn)
        layout.addLayout(header)
        # Main split area
        main_layout = QHBoxLayout()
        # Left: Deck list
        deck_group = QGroupBox("Decks")
        deck_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px; 
                color: {self._colors['PRIMARY']}; 
                font-weight: 600;
                border: 2px solid {self._colors['SECONDARY']}; 
                border-radius: 12px; 
                padding-top: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
        """)
        deck_layout = QVBoxLayout()
        self.deck_list = QListWidget()
        self.deck_list.setMinimumWidth(200)
        self.deck_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {self._colors['BG_LIGHT']}; 
                border: 2px solid {self._colors['SECONDARY']};
                border-radius: 10px; 
                padding: 8px; 
                font-size: 13px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QListWidget::item {{ 
                padding: 12px; 
                border-radius: 6px; 
                margin: 2px 0px; 
            }}
            QListWidget::item:selected {{ 
                background-color: {self._colors['SECONDARY']}; 
                color: {self._colors['PRIMARY_DARK']}; 
            }}
            QListWidget::item:hover {{ 
                background-color: {self._colors['SECONDARY_LIGHT']}; 
            }}
        """)
        self.deck_list.itemClicked.connect(self.on_deck_selected)
        deck_layout.addWidget(self.deck_list)
        delete_deck_btn = QPushButton("Delete Deck")
        delete_deck_btn.clicked.connect(self.delete_deck)
        delete_deck_btn.setStyleSheet(f"""
            background-color: {self._colors['SECONDARY_DARK']}; 
            color: {self._colors['TEXT_LIGHT']}; 
            border: none; 
            padding: 8px; 
            border-radius: 8px;
            font-family: {self.IOS_FONT_STACK};
        """)
        deck_layout.addWidget(delete_deck_btn)
        deck_group.setLayout(deck_layout)
        main_layout.addWidget(deck_group)
        # Right: Card review area
        review_group = QGroupBox("Review")
        review_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 16px; 
                color: {self._colors['PRIMARY']}; 
                font-weight: 600;
                border: 2px solid {self._colors['SECONDARY']}; 
                border-radius: 12px; 
                padding-top: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
        """)
        review_layout = QVBoxLayout()
        self.stats_label = QLabel("Select a deck to begin")
        self.stats_label.setStyleSheet(f"font-size: 14px; color: {self._colors['TEXT_SECONDARY']}; padding: 10px; font-family: {self.IOS_FONT_STACK};")
        review_layout.addWidget(self.stats_label)
        self.card_front = QLabel("")
        self.card_front.setAlignment(Qt.AlignCenter)
        self.card_front.setMinimumHeight(200)
        self.card_front.setStyleSheet(f"""
            font-size: 22px; 
            font-weight: 600; 
            color: {self._colors['TEXT_PRIMARY']};
            background-color: {self._colors['BG_WHITE']}; 
            border: 2px solid {self._colors['SECONDARY']};
            border-radius: 15px; 
            padding: 30px;
        """)
        self.card_front.setWordWrap(True)
        review_layout.addWidget(self.card_front)
        self.card_back = QLabel("")
        self.card_back.setAlignment(Qt.AlignCenter)
        self.card_back.setMinimumHeight(150)
        self.card_back.setStyleSheet(f"""
            font-size: 18px; 
            color: {self._colors['TEXT_SECONDARY']};
            background-color: {self._colors['BG_LIGHT']}; 
            border: 2px solid {self._colors['SECONDARY']};
            border-radius: 15px; 
            padding: 20px;
        """)
        self.card_back.setWordWrap(True)
        self.card_back.setVisible(False)
        review_layout.addWidget(self.card_back)
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        self.show_btn = QPushButton("Show Answer (Space)")
        self.show_btn.setMinimumHeight(45)
        self.show_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['PRIMARY']}; 
                color: {self._colors['TEXT_LIGHT']}; 
                border: none;
                padding: 12px 20px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['PRIMARY_LIGHT']}; 
            }}
        """)
        self.show_btn.clicked.connect(self.show_answer)
        self.show_btn.setShortcut("Space")
        btn_layout.addWidget(self.show_btn)
        self.again_btn = QPushButton("Again (0)")
        self.again_btn.setMinimumHeight(45)
        self.again_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SECONDARY_DARK']}; 
                color: {self._colors['TEXT_LIGHT']}; 
                border: none;
                padding: 12px 20px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['PRIMARY']}; 
            }}
        """)
        self.again_btn.clicked.connect(lambda: self.rate_card(0))
        self.again_btn.setShortcut("1")
        self.again_btn.setVisible(False)
        btn_layout.addWidget(self.again_btn)
        self.hard_btn = QPushButton("Hard (2)")
        self.hard_btn.setMinimumHeight(45)
        self.hard_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SECONDARY_LIGHT']}; 
                color: {self._colors['TEXT_SECONDARY']}; 
                border: 2px solid {self._colors['SECONDARY']};
                padding: 12px 20px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['SECONDARY']}; 
            }}
        """)
        self.hard_btn.clicked.connect(lambda: self.rate_card(2))
        self.hard_btn.setShortcut("2")
        self.hard_btn.setVisible(False)
        btn_layout.addWidget(self.hard_btn)
        self.good_btn = QPushButton("Good (4)")
        self.good_btn.setMinimumHeight(45)
        self.good_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SUCCESS']}; 
                color: white; 
                border: none;
                padding: 12px 20px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                }}
        """)
        self.good_btn.clicked.connect(lambda: self.rate_card(4))
        self.good_btn.setShortcut("3")
        self.good_btn.setVisible(False)
        btn_layout.addWidget(self.good_btn)
        self.easy_btn = QPushButton("Easy (5)")
        self.easy_btn.setMinimumHeight(45)
        self.easy_btn.setStyleSheet(f"""
            QPushButton {{
                color: white; 
                border: none;
                padding: 12px 20px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 14px;
            }}
            QPushButton:hover {{ 
                }}
        """)
        self.easy_btn.clicked.connect(lambda: self.rate_card(5))
        self.easy_btn.setShortcut("4")
        self.easy_btn.setVisible(False)
        btn_layout.addWidget(self.easy_btn)
        review_layout.addLayout(btn_layout)
        # Navigation buttons
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(10)
        self.prev_btn = QPushButton("← Previous")
        self.prev_btn.setMinimumHeight(36)
        self.prev_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SECONDARY_LIGHT']}; 
                color: {self._colors['TEXT_SECONDARY']}; 
                border: 2px solid {self._colors['SECONDARY']};
                padding: 8px 16px; 
                font-weight: 600; 
                border-radius: 8px; 
                font-size: 13px;
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['SECONDARY']}; 
            }}
        """)
        self.prev_btn.clicked.connect(self.prev_card)
        self.prev_btn.setShortcut("Left")
        nav_layout.addWidget(self.prev_btn)
        self.next_btn = QPushButton("Skip →")
        self.next_btn.setMinimumHeight(36)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SECONDARY_LIGHT']}; 
                color: {self._colors['TEXT_SECONDARY']}; 
                border: 2px solid {self._colors['SECONDARY']};
                padding: 8px 16px; 
                font-weight: 600; 
                border-radius: 8px; 
                font-size: 13px;
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['SECONDARY']}; 
            }}
        """)
        self.next_btn.clicked.connect(self.next_card)
        self.next_btn.setShortcut("Right")
        nav_layout.addWidget(self.next_btn)
        nav_layout.addStretch()
        review_layout.addLayout(nav_layout)
        # Add card button
        add_card_btn = QPushButton("Add Card")
        add_card_btn.setMinimumHeight(40)
        add_card_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['SECONDARY_LIGHT']}; 
                color: {self._colors['TEXT_SECONDARY']}; 
                border: 2px solid {self._colors['SECONDARY']};
                padding: 10px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 13px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['SECONDARY']}; 
            }}
        """)
        add_card_btn.clicked.connect(self.add_card)
        review_layout.addWidget(add_card_btn)
        # Import from study notes
        import_btn = QPushButton("Import from Study Notes")
        import_btn.setMinimumHeight(40)
        import_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['BG_LIGHT']}; 
                color: {self._colors['TEXT_SECONDARY']}; 
                border: 2px solid {self._colors['SECONDARY']};
                padding: 10px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 13px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['SECONDARY_LIGHT']}; 
            }}
        """)
        import_btn.clicked.connect(self.import_from_notes)
        review_layout.addWidget(import_btn)
        # Import from file (CSV, APKG, TXT)
        import_file_btn = QPushButton("Import from File (CSV/APKG/TXT)")
        import_file_btn.setMinimumHeight(40)
        import_file_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._colors['PRIMARY']}; 
                color: {self._colors['TEXT_LIGHT']}; 
                border: none;
                padding: 10px; 
                font-weight: 600; 
                border-radius: 10px; 
                font-size: 13px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{ 
                background-color: {self._colors['PRIMARY_LIGHT']}; 
            }}
        """)
        import_file_btn.clicked.connect(self.import_from_file)
        review_layout.addWidget(import_file_btn)
        review_group.setLayout(review_layout)
        main_layout.addWidget(review_group, stretch=2)
        layout.addLayout(main_layout)
        self.setLayout(layout)
    def load_decks(self):
        self.deck_list.clear()
        decks = self.db.get_flashcard_decks()
        for deck in decks:
            text = f"{deck['name']}  ({deck.get('due_cards', 0)} due / {deck.get('total_cards', 0)} total)"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, deck['id'])
            self.deck_list.addItem(item)
    def on_deck_selected(self, item):
        self.current_deck_id = item.data(Qt.UserRole)
        self.load_due_cards()
    def load_due_cards(self):
        if not self.current_deck_id:
            return
        self.due_cards = self.db.get_due_flashcards(self.current_deck_id)
        self.current_card_index = 0
        self.showing_answer = False
        self.show_btn.setVisible(True)
        self.again_btn.setVisible(False)
        self.hard_btn.setVisible(False)
        self.good_btn.setVisible(False)
        self.easy_btn.setVisible(False)
        self.prev_btn.setVisible(False)
        self.next_btn.setVisible(False)
        self.card_back.setVisible(False)
        if not self.due_cards:
            self.stats_label.setText("All caught up! No cards due for review.")
            self.card_front.setText("")
            self.show_btn.setVisible(False)
        else:
            self.stats_label.setText(f"{len(self.due_cards)} cards due")
            self.show_current_card()
    def show_current_card(self):
        if 0 <= self.current_card_index < len(self.due_cards):
            card = self.due_cards[self.current_card_index]
            self.card_front.setText(card['front'])
            self.card_back.setText(card['back'])
            self.card_back.setVisible(False)
            self.showing_answer = False
            self.show_btn.setVisible(True)
            self.again_btn.setVisible(False)
            self.hard_btn.setVisible(False)
            self.good_btn.setVisible(False)
            self.easy_btn.setVisible(False)
            self.prev_btn.setVisible(self.current_card_index > 0)
            self.next_btn.setVisible(True)
    def show_answer(self):
        self.card_back.setVisible(True)
        self.showing_answer = True
        self.show_btn.setVisible(False)
        self.again_btn.setVisible(True)
        self.hard_btn.setVisible(True)
        self.good_btn.setVisible(True)
        self.easy_btn.setVisible(True)
        self.prev_btn.setVisible(self.current_card_index > 0)
        self.next_btn.setVisible(True)
    def prev_card(self):
        """Go to previous card without rating."""
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.show_current_card()
    def next_card(self):
        """Skip current card."""
        if self.current_card_index < len(self.due_cards) - 1:
            self.current_card_index += 1
            self.show_current_card()
    def rate_card(self, quality: int):
        if self.current_card_index >= len(self.due_cards):
            return
        card_data = self.due_cards[self.current_card_index]
        card = Flashcard.from_dict(card_data)
        card.review(quality)
        # Save SM-2 state
        self.db.update_flashcard_review(
            card_id=card_data['id'],
            interval_days=card.interval_days,
            next_review=card.next_review,
            ease_factor=card.ease_factor,
            reps=card.reps,
        )
        self.current_card_index += 1
        if self.current_card_index >= len(self.due_cards):
            self.stats_label.setText("Deck complete for today!")
            self.card_front.setText("")
            self.card_back.setVisible(False)
            self.show_btn.setVisible(False)
            self.again_btn.setVisible(False)
            self.hard_btn.setVisible(False)
            self.good_btn.setVisible(False)
            self.easy_btn.setVisible(False)
            self.prev_btn.setVisible(False)
            self.next_btn.setVisible(False)
            self.load_decks()
        else:
            remaining = len(self.due_cards) - self.current_card_index
            self.stats_label.setText(f"{remaining} cards remaining")
            self.show_current_card()
    def add_deck(self):
        name, ok = QInputDialog.getText(self, "New Deck", "Deck name:")
        if ok and name.strip():
            self.db.add_flashcard_deck(name.strip())
            self.load_decks()
    def delete_deck(self):
        item = self.deck_list.currentItem()
        if not item:
            return
        deck_id = item.data(Qt.UserRole)
        reply = QMessageBox.question(self, "Delete Deck", "Delete this deck and all its cards?")
        if reply == QMessageBox.Yes:
            self.db.delete_flashcard_deck(deck_id)
            self.load_decks()
            self.card_front.setText("")
            self.card_back.setText("")
    def add_card(self):
        if not self.current_deck_id:
            QMessageBox.warning(self, "No Deck", "Please select a deck first.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Card")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        front = QTextEdit()
        front.setPlaceholderText("Front (question)...")
        front.setMaximumHeight(120)
        layout.addWidget(QLabel("Front:"))
        layout.addWidget(front)
        back = QTextEdit()
        back.setPlaceholderText("Back (answer)...")
        back.setMaximumHeight(120)
        layout.addWidget(QLabel("Back:"))
        layout.addWidget(back)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self._save_card(dialog, front.toPlainText(), back.toPlainText()))
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec()
    def _save_card(self, dialog, front, back):
        if not front.strip() or not back.strip():
            QMessageBox.warning(dialog, "Missing Fields", "Both front and back are required.")
            return
        self.db.add_flashcard(self.current_deck_id, front.strip(), back.strip())
        dialog.accept()
        self.load_due_cards()
    def import_from_notes(self):
        if not self.current_deck_id:
            QMessageBox.warning(self, "No Deck", "Please select a deck first.")
            return
        count = self.db.import_study_notes_as_flashcards(self.current_deck_id)
        QMessageBox.information(self, "Import Complete", f"Imported {count} study notes as flashcards!")
        self.load_decks()
        self.load_due_cards()
    def import_from_file(self):
        """Import flashcards from a CSV, APKG, or TXT file."""
        if not self.current_deck_id:
            QMessageBox.warning(self, "No Deck", "Please select a deck first.")
            return
        count = FlashcardImporter.import_file(self.current_deck_id, self.db, self)
        if count > 0:
            QMessageBox.information(self, "Import Complete", f"Imported {count} cards from file!")
            self.load_decks()
            self.load_due_cards()
