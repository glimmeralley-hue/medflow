"""Notes Section widget — clinical study journal with search and export."""
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QTextEdit, QComboBox, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from medflow.database import Database
from .constants import NOTE_CATEGORIES
from .note_reader import NoteReaderDialog
from .theme_manager import get_theme_manager, ThemeType
class NotesSection(QWidget):
    """Notes workspace with clinical study journal."""
    # iOS-style font stack for native look
    IOS_FONT_STACK = '-apple-system, BlinkMacSystemFont, "SF Pro", "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self._editing_note_id: Optional[int] = None  # None = creating new note
        self.theme_manager = get_theme_manager()
        self.init_ui()
        self.load_notes()
    def init_ui(self):
        # Main layout is QHBoxLayout directly in NotesSection
        layout = QHBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(15, 15, 15, 15)
        # Get colors from theme manager
        from .theme_manager import ThemeColors
        c = ThemeColors.get_colors(self.theme_manager.get_theme())
        create_group = QGroupBox("Create / Edit Note")
        create_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 18px;
            }}
        """)
        create_layout = QVBoxLayout()
        create_layout.setSpacing(15)
        self.note_title = QLineEdit()
        self.note_title.setPlaceholderText("Note title...")
        self.note_title.setMinimumHeight(45)
        self.note_title.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid;
            padding: 12px;
                border-radius: 10px;
                font-size: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QLineEdit:focus {{
                border: 2px solid;
            }}
        """)
        create_layout.addWidget(self.note_title)
        category_layout = QHBoxLayout()
        category_label = QLabel("Category:")
        category_label.setStyleSheet(f"font-weight: 500; font-family: {self.IOS_FONT_STACK};")
        self.note_category = QComboBox()
        self.note_category.addItems(NOTE_CATEGORIES)
        self.note_category.setMinimumHeight(40)
        self.note_category.setStyleSheet(f"""
            QComboBox {{
                border: 2px solid;
            padding: 8px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QComboBox:focus {{
                border: 2px solid;
            }}
        """)
        category_layout.addWidget(category_label)
        category_layout.addWidget(self.note_category)
        category_layout.addStretch()
        create_layout.addLayout(category_layout)
        self.note_content = QTextEdit()
        self.note_content.setPlaceholderText("Write your notes here...")
        self.note_content.setMinimumHeight(180)
        self.note_content.setStyleSheet(f"""
            QTextEdit {{
                border: 2px solid;
            padding: 15px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QTextEdit:focus {{
                border: 2px solid;
            }}
        """)
        self.note_content.textChanged.connect(self.update_word_count)
        create_layout.addWidget(self.note_content)
        self.word_count_label = QLabel("0 words | 0 characters")
        self.word_count_label.setStyleSheet(f"font-size: 12px; font-style: italic; font-family: {self.IOS_FONT_STACK};")
        self.word_count_label.setAlignment(Qt.AlignRight)
        create_layout.addWidget(self.word_count_label)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        self.save_note_btn = QPushButton("Save Note")
        self.save_note_btn.setMinimumHeight(50)
        self.save_note_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                }}
        """)
        self.save_note_btn.setToolTip("Save the current note (Ctrl+S)")
        self.save_note_btn.setShortcut("Ctrl+S")
        self.save_note_btn.clicked.connect(self.add_note)
        buttons_layout.addWidget(self.save_note_btn)
        new_note_btn = QPushButton("New Note")
        new_note_btn.setMinimumHeight(50)
        new_note_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid;
            padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                }}
        """)
        new_note_btn.setToolTip("Clear the editor and start a brand new note")
        new_note_btn.clicked.connect(self.clear_editor)
        buttons_layout.addWidget(new_note_btn)
        export_btn = QPushButton("Export")
        export_btn.setMinimumHeight(50)
        export_btn.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid;
            padding: 14px 24px;
                font-weight: 600;
                border-radius: 12px;
                font-size: 15px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                }}
        """)
        export_btn.setToolTip("Export all notes to a text file")
        export_btn.clicked.connect(self.export_notes)
        buttons_layout.addWidget(export_btn)
        create_layout.addLayout(buttons_layout)
        create_group.setLayout(create_layout)
        layout.addWidget(create_group, 2)
        notes_group = QGroupBox("My Notes")
        notes_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 18px;
                font-weight: 600;
                border: 2px solid;
            border-radius: 12px;
                padding-top: 18px;
                font-family: {self.IOS_FONT_STACK};
            }}
        """)
        notes_layout = QVBoxLayout()
        notes_layout.setSpacing(15)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search notes...")
        self.search_input.setMinimumHeight(40)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid;
            padding: 10px;
                border-radius: 10px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
        """)
        self.search_input.textChanged.connect(self.filter_notes)
        notes_layout.addWidget(self.search_input)
        self.notes_list = QListWidget()
        self.notes_list.setMinimumHeight(420)
        self.update_notes_list_style()
        self.notes_list.itemClicked.connect(self.load_note)
        self.notes_list.itemDoubleClicked.connect(self.open_note_reader)
        notes_layout.addWidget(self.notes_list)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)
        read_btn = QPushButton("Read Note")
        read_btn.setMinimumHeight(45)
        read_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                }}
        """)
        read_btn.clicked.connect(self.open_note_reader)
        action_layout.addWidget(read_btn)
        delete_btn = QPushButton("Delete")
        delete_btn.setMinimumHeight(45)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                padding: 12px 20px;
                font-weight: 600;
                border-radius: 10px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QPushButton:hover {{
                }}
        """)
        delete_btn.clicked.connect(self.delete_note)
        action_layout.addWidget(delete_btn)
        action_layout.addStretch()
        notes_layout.addLayout(action_layout)
        notes_group.setLayout(notes_layout)
        layout.addWidget(notes_group, 1)
    def update_notes_list_style(self):
        """Update the notes list stylesheet based on current theme."""
        c = self.theme_manager.get_colors(self.theme_manager.get_theme())
        self.notes_list.setStyleSheet(f"""
            QListWidget {{
                border: 2px solid;
            border-radius: 12px;
                padding: 12px;
                font-size: 14px;
                font-family: {self.IOS_FONT_STACK};
            }}
            QListWidget::item {{
                padding: 14px;
                margin: 8px 0px;
                border-radius: 10px;
                border: 2px solid;
            }}
            QListWidget::item:selected {{
                border: 2px solid;
            }}
            QListWidget::item:hover {{
                }}
        """)
    def add_note(self):
        title = self.note_title.text().strip()
        content = self.note_content.toPlainText().strip()
        category = self.note_category.currentText()
        if not title or not content:
            QMessageBox.warning(self, "Missing Note", "Please enter both a title and note content.")
            return
        if self._editing_note_id is not None:
            # Update existing note in DB
            self.db.update_app_note(self._editing_note_id, title, content, category)
        else:
            # Create new note in DB
            self.db.add_app_note(title, content, category)
        self.clear_editor()
        self.load_notes()
    def clear_editor(self):
        """Reset the editor to create a new note"""
        self._editing_note_id = None
        self.note_title.clear()
        self.note_content.clear()
        self.note_category.setCurrentIndex(0)
        self.save_note_btn.setText("Save Note")
        self.notes_list.clearSelection()
    def refresh_notes_list(self):
        notes = self.db.get_app_notes()
        self.notes_list.clear()
        for note in notes:
            ts = note.get('updated_at') or note.get('created_at', '')
            item_text = f"{note['title']}\n   {note['category']} · {ts[:16]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)
        count = len(notes)
        # Update group box title dynamically if it exists
        parent = self.notes_list.parent()
        if isinstance(parent, QWidget):
            gb = parent.parent()
            if hasattr(gb, 'setTitle'):
                gb.setTitle(f"My Notes  ({count})")
    def load_notes(self):
        self.refresh_notes_list()
    def load_note(self, item: QListWidgetItem):
        note_id = item.data(Qt.UserRole)
        note = self.db.get_app_note_by_id(note_id)
        if note:
            self._editing_note_id = note_id
            self.note_title.setText(note['title'])
            self.note_category.setCurrentText(note['category'])
            self.note_content.setText(note['content'])
            self.save_note_btn.setText("Update Note")
    def delete_note(self):
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a note to delete.")
            return
        note_id = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to permanently delete this note?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_app_note(note_id)
            if self._editing_note_id == note_id:
                self.clear_editor()
            self.load_notes()
    def filter_notes(self, text: str):
        notes = self.db.get_app_notes(search=text if text else None)
        self.notes_list.clear()
        for note in notes:
            ts = note.get('updated_at') or note.get('created_at', '')
            item_text = f"{note['title']}\n   {note['category']} · {ts[:16]}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, note['id'])
            self.notes_list.addItem(item)
    def update_word_count(self):
        text = self.note_content.toPlainText()
        words = len(text.split()) if text.strip() else 0
        chars = len(text)
        self.word_count_label.setText(f"{words} words | {chars} characters")
    def export_notes(self):
        notes = self.db.get_app_notes()
        if not notes:
            QMessageBox.information(self, "No Notes", "No notes to export.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Notes",
            f"medflow_notes_{datetime.now().strftime('%Y%m%d')}.txt",
            "Text Files (*.txt);All Files (*)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write("MEDFLOW STUDY NOTES EXPORT\n")
                f.write(f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write("=" * 60 + "\n\n")
                for i, note in enumerate(notes, 1):
                    f.write(f"{'-' * 60}\n")
                    f.write(f"NOTE #{i}\n")
                    f.write(f"{'-' * 60}\n")
                    f.write(f"Title: {note['title']}\n")
                    f.write(f"Category: {note['category']}\n")
                    f.write(f"Date: {note.get('updated_at', '')[:16]}\n\n")
                    f.write(f"Content:\n{note['content']}\n\n")
                f.write("=" * 60 + "\n")
                f.write(f"Total Notes: {len(notes)}\n")
            QMessageBox.information(self, "Export Successful", f"Notes exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"Error: {str(e)}")
    def open_note_reader(self):
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a note to read.")
            return
        note_id = current_item.data(Qt.UserRole)
        note = self.db.get_app_note_by_id(note_id)
        if note:
            # Remap key names so NoteReaderDialog gets what it expects
            note.setdefault('date', note.get('updated_at', '')[:16])
            dialog = NoteReaderDialog(note, self)
            dialog.exec()