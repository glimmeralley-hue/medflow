"""Digital library section for medical books."""
from pathlib import Path
from typing import List, Dict, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QScrollArea, QFrame, QDialog, QMessageBox,
    QFileDialog, QProgressBar, QSizePolicy
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from medflow.database import Database
from medflow.utils.validators import validate_file_path, sanitize_string
from .constants import LIBRARY_CATEGORIES
class LibrarySection(QWidget):
    """Digital library for medical books"""
    def __init__(self, database: Database):
        super().__init__()
        self.db = database
        self.books = []
        self.current_category = "All"
        self.init_ui()
        self.load_books()
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 20, 30, 20)
        # Header
        header = QHBoxLayout()
        title = QLabel("Medical Library")
        title.setStyleSheet("font-size: 28px; font-weight: 700; ")
        header.addWidget(title)
        self.stats_label = QLabel("0 books")
        self.stats_label.setStyleSheet("font-size: 14px; padding: 5px 15px; border-radius: 10px;")
        header.addWidget(self.stats_label)
        header.addStretch()
        add_btn = QPushButton("Add Book")
        add_btn.setStyleSheet("color: white; border: none; padding: 10px 20px; border-radius: 10px; font-weight: 600;")
        add_btn.clicked.connect(self.show_add_book_dialog)
        header.addWidget(add_btn)
        layout.addLayout(header)
        # Filter bar
        filter_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search books...")
        self.search_input.setStyleSheet("padding: 10px; border-radius: 10px; ")
        self.search_input.textChanged.connect(self.load_books)
        filter_bar.addWidget(self.search_input, stretch=2)
        self.category_combo = QComboBox()
        self.category_combo.addItems(LIBRARY_CATEGORIES)
        self.category_combo.setStyleSheet("padding: 10px; border-radius: 10px; ")
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        filter_bar.addWidget(QLabel("Category:"))
        filter_bar.addWidget(self.category_combo)
        layout.addLayout(filter_bar)
        # Grid container for books
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        self.books_container = QWidget()
        self.books_grid = QGridLayout()
        self.books_grid.setSpacing(15)
        self.books_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.books_container.setLayout(self.books_grid)
        scroll.setWidget(self.books_container)
        layout.addWidget(scroll)
        self.setLayout(layout)
    def on_category_changed(self, category):
        self.current_category = category
        self.load_books()
    def load_books(self):
        # Clear grid
        while self.books_grid.count() > 0:
            item = self.books_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        search_text = self.search_input.text().strip()
        if search_text:
            self.books = self.db.get_library_books(search=search_text)
        elif self.current_category != "All":
            self.books = self.db.get_library_books(category=self.current_category)
        else:
            self.books = self.db.get_library_books()
        total = len(self.books)
        read_count = sum(1 for b in self.books if b.get('is_read'))
        self.stats_label.setText(f"{total} books • {read_count} read")
        if not self.books:
            empty = QLabel("No books yet. Click 'Add Book' to start!")
            empty.setStyleSheet("font-size: 16px; padding: 50px;")
            empty.setAlignment(Qt.AlignCenter)
            self.books_grid.addWidget(empty, 0, 0)
        else:
            # Add books in grid (3 columns)
            for idx, book in enumerate(self.books):
                row = idx // 3
                col = idx % 3
                card = self.create_book_card(book)
                self.books_grid.addWidget(card, row, col)
    def create_book_card(self, book):
        card = QFrame()
        card.setMinimumSize(200, 270)
        card.setMaximumWidth(260)
        card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
            }
            QFrame:hover {
                }
        """)
        layout = QVBoxLayout()
        layout.setSpacing(7)
        layout.setContentsMargins(12, 12, 12, 12)
        # Book cover/icon area
        cover = QLabel("📖" if not book.get('is_read') else "✓")
        cover.setAlignment(Qt.AlignCenter)
        cover.setStyleSheet("""
            font-size: 52px;
            border-radius: 10px;
            padding: 12px;
        """)
        layout.addWidget(cover)
        # Title
        title_text = book['title']
        title = QLabel(title_text)
        title.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            """)
        title.setWordWrap(True)
        title.setToolTip(title_text)
        layout.addWidget(title)
        # Author
        if book.get('author'):
            author_text = book['author'][:20] + "..." if len(book['author']) > 20 else book['author']
            author = QLabel(f"By {author_text}")
            author.setStyleSheet("font-size: 11px; ")
            layout.addWidget(author)
        # Category badge
        cat = book.get('custom_category') or book.get('category', 'General')
        cat_label = QLabel(f"{cat[:15]}")
        cat_label.setStyleSheet("""
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 8px;
        """)
        layout.addWidget(cat_label)
        # Reading progress bar
        pages = book.get('pages') or 0
        current_page = book.get('current_page') or 0
        if pages > 0:
            progress_pct = min(100, int(current_page / pages * 100))
            prog_label = QLabel(f"p.{current_page}/{pages}  ({progress_pct}%)")
            prog_label.setStyleSheet("font-size: 10px; ")
            layout.addWidget(prog_label)
            prog_bar = QProgressBar()
            prog_bar.setValue(progress_pct)
            prog_bar.setFixedHeight(6)
            prog_bar.setTextVisible(False)
            prog_bar.setStyleSheet("""
                QProgressBar {
                    border: none;
                    border-radius: 3px;
                    }
                QProgressBar::chunk {
                    border-radius: 3px;
                }
            """)
            layout.addWidget(prog_bar)
        # Rating stars
        if book.get('rating'):
            stars = QLabel("★" * book['rating']) + QLabel("☆" * (5 - book['rating']))
            stars.setStyleSheet("font-size: 11px;")
            layout.addWidget(stars)
        layout.addStretch()
        # Buttons row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        read_btn = QPushButton("📖")
        read_btn.setFixedSize(32, 32)
        read_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                }
        """)
        read_btn.setToolTip("Read")
        read_btn.clicked.connect(lambda: self.open_book(book['id']))
        btn_layout.addWidget(read_btn)
        rate_btn = QPushButton("★")
        rate_btn.setFixedSize(32, 32)
        rate_btn.setStyleSheet("""
            QPushButton {
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover {
                }
        """)
        rate_btn.setToolTip("Rate")
        rate_btn.clicked.connect(lambda: self.rate_book(book['id']))
        btn_layout.addWidget(rate_btn)
        del_btn = QPushButton("Delete")
        del_btn.setFixedSize(32, 32)
        del_btn.setStyleSheet("""
            QPushButton {
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 11px;
            }
            QPushButton:hover {
                }
        """)
        del_btn.setToolTip("Remove")
        del_btn.clicked.connect(lambda: self.delete_book(book['id']))
        btn_layout.addWidget(del_btn)
        layout.addLayout(btn_layout)
        card.setLayout(layout)
        return card
    def show_add_book_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Book")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout()
        title = QLineEdit()
        title.setPlaceholderText("Book Title")
        title.setStyleSheet("padding: 12px; border-radius: 10px;")
        layout.addWidget(title)
        author = QLineEdit()
        author.setPlaceholderText("Author")
        author.setStyleSheet("padding: 12px; border-radius: 10px;")
        layout.addWidget(author)
        cat = QComboBox()
        cat.addItems(LIBRARY_CATEGORIES)
        cat.setStyleSheet("padding: 12px; border-radius: 10px;")
        layout.addWidget(cat)
        custom = QLineEdit()
        custom.setPlaceholderText("Custom Category")
        custom.setStyleSheet("padding: 12px; border-radius: 10px;")
        layout.addWidget(custom)
        file_btn = QPushButton("Select File")
        file_path = [None]
        def select_file():
            path, _ = QFileDialog.getOpenFileName(dialog, "Select Book", str(Path.home()), "Books (*.pdf *.epub *.txt)")
            if path:
                file_path[0] = path
                file_btn.setText(f"{Path(path).name[:20]}...")
        file_btn.clicked.connect(select_file)
        file_btn.setStyleSheet("padding: 10px; border-radius: 10px; font-size: 13px;")
        layout.addWidget(file_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(lambda: self.save_book(dialog, title.text(), author.text(), cat.currentText(), custom.text(), file_path[0]))
        save_btn.setStyleSheet("color: white; border: none; padding: 12px 24px; border-radius: 10px; font-weight: 600; font-size: 14px;")
        layout.addWidget(save_btn)
        dialog.setLayout(layout)
        dialog.exec()
    def save_book(self, dialog, title, author, category, custom, file_path):
        if not title or not file_path:
            QMessageBox.warning(dialog, "Missing Fields", "Book title and file path are required.")
            return
        try:
            validate_file_path(file_path, must_exist=True, allowed_extensions=['.pdf', '.epub', '.txt'])
        except Exception as exc:
            QMessageBox.warning(dialog, "Invalid File", str(exc))
            return
        try:
            sanitize_string(title, max_length=200)
        except Exception as exc:
            QMessageBox.warning(dialog, "Invalid Title", str(exc))
            return
        custom_cat = custom if category == "Custom" else ""
        self.db.add_library_book(title, author, file_path, category, custom_cat)
        dialog.accept()
        self.load_books()
    def open_book(self, book_id):
        book = next((b for b in self.books if b['id'] == book_id), None)
        if not book:
            QMessageBox.warning(self, "Not Found", "Book record not found.")
            return
        try:
            safe_path = validate_file_path(
                book['file_path'], must_exist=True,
                allowed_extensions=['.pdf', '.epub', '.txt']
            )
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(safe_path)))
        except Exception as exc:
            QMessageBox.warning(self, "Cannot Open", f"Could not open book: {exc}")
    def rate_book(self, book_id):
        dialog = QDialog(self)
        dialog.setWindowTitle("Rate Book")
        layout = QVBoxLayout()
        for i in range(1, 6):
            btn = QPushButton("★" * i)
            btn.clicked.connect(lambda checked, r=i: self.save_rating(book_id, r, dialog))
            layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec()
    def save_rating(self, book_id, rating, dialog):
        self.db.update_book_rating(book_id, rating)
        dialog.accept()
        self.load_books()
    def delete_book(self, book_id):
        reply = QMessageBox.question(self, "Confirm", "Remove this book from library?")
        if reply == QMessageBox.Yes:
            self.db.delete_library_book(book_id)
            self.load_books()