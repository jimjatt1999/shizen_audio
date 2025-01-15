# Create NEW FILE: ui/components/card_browser.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QScrollArea, QWidget, QMessageBox, QInputDialog)
from PyQt6.QtCore import Qt
from .audio_card import AudioCard

class CardBrowserDialog(QDialog):
    def __init__(self, review_system, source_path, parent=None):
        super().__init__(parent)
        self.review_system = review_system
        self.source_path = source_path
        self.cards = []
        self.setup_ui()
        self.load_cards()
        
        # Set window properties
        self.setWindowTitle("Browse Cards")
        self.resize(600, 800)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        
        # Title
        title = QLabel("Browse Cards")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        header.addWidget(title)
        
        # Card count
        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #6b7280; font-size: 14px;")
        header.addWidget(self.count_label)
        
        header.addStretch()
        layout.addLayout(header)

        # Cards scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #d1d5db;
                border-radius: 4px;
            }
        """)
        
        content = QWidget()
        self.cards_layout = QVBoxLayout(content)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(12)
        self.cards_layout.addStretch()
        
        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

    def load_cards(self):
        """Load cards from the source"""
        try:
            # Get cards for this source
            self.cards = [
                card for card in self.review_system.items 
                if card['audio_path'] == self.source_path
            ]
            
            # Update count
            self.count_label.setText(f"{len(self.cards)} cards")
            
            # Clear existing cards
            while self.cards_layout.count() > 1:  # Keep the stretch
                item = self.cards_layout.takeAt(0)
                if item.widget():
                    if isinstance(item.widget(), AudioCard):
                        item.widget().cleanup()
                    item.widget().deleteLater()
            
            # Add cards
            for card in self.cards:
                card_widget = self.create_card_widget(card)
                self.cards_layout.insertWidget(
                    self.cards_layout.count() - 1,
                    card_widget
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load cards: {str(e)}"
            )

    def create_card_widget(self, card):
        """Create a widget for a card"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Card content
        content = QHBoxLayout()
        
        # Text
        text = QLabel(card['text'])
        text.setWordWrap(True)
        text.setStyleSheet("font-size: 14px; color: #1f2937;")
        content.addWidget(text, stretch=1)
        
        # Stats
        stats = QLabel(f"Reviews: {card.get('reviews', 0)}")
        stats.setStyleSheet("color: #6b7280; font-size: 12px;")
        content.addWidget(stats)
        
        layout.addLayout(content)
        
        # Actions row
        actions = QHBoxLayout()
        actions.setSpacing(8)
        
        # Play button
        play_btn = QPushButton("Play")
        play_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        play_btn.clicked.connect(lambda: self.play_card(card))
        play_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(lambda: self.edit_card(card))
        edit_btn.setStyleSheet(play_btn.styleSheet())
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(lambda: self.delete_card(card))
        delete_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        
        actions.addWidget(play_btn)
        actions.addWidget(edit_btn)
        actions.addWidget(delete_btn)
        actions.addStretch()
        
        layout.addLayout(actions)
        
        # Widget styling
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
            }
        """)
        
        return widget

    def play_card(self, card):
        """Play card audio"""
        try:
            audio_card = AudioCard(card, card['audio_path'], self.review_system)
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Play Card")
            dialog.setLayout(QVBoxLayout())
            dialog.layout().addWidget(audio_card)
            dialog.resize(500, 200)
            dialog.exec()
            
            audio_card.cleanup()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to play card: {str(e)}"
            )

    def edit_card(self, card):
        """Edit card text"""
        try:
            text, ok = QInputDialog.getMultiLineText(
                self,
                "Edit Card",
                "Edit text:",
                card['text']
            )
            
            if ok and text.strip():
                self.review_system.edit_card_text(card['id'], text.strip())
                self.load_cards()  # Refresh view
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to edit card: {str(e)}"
            )

    def delete_card(self, card):
        """Delete card"""
        try:
            reply = QMessageBox.question(
                self,
                "Confirm Deletion",
                "Delete this card permanently?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.review_system.delete_card(card['id'])
                self.load_cards()  # Refresh view
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to delete card: {str(e)}"
            )

    def closeEvent(self, event):
        """Clean up on close"""
        # Clean up any playing audio
        for i in range(self.cards_layout.count()):
            item = self.cards_layout.itemAt(i)
            if item and item.widget():
                if isinstance(item.widget(), AudioCard):
                    item.widget().cleanup()
        event.accept()