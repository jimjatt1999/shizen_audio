# Create NEW FILE: ui/components/focus_mode.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QCheckBox, QGroupBox, QMessageBox)
from PyQt6.QtCore import Qt
import random
from .audio_card import AudioCard

class FocusModeDialog(QDialog):
    def __init__(self, review_system, parent=None):
        super().__init__(parent)
        self.review_system = review_system
        self.selected_sources = set()
        self.setup_ui()
        self.setWindowTitle("Focus Mode")
        self.resize(500, 600)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Header
        header = QLabel("Focus Mode")
        header.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
        """)
        layout.addWidget(header)

        # Description
        desc = QLabel("Select sources to focus on and practice intensively")
        desc.setStyleSheet("color: #6b7280; font-size: 14px;")
        layout.addWidget(desc)

        # Source selection
        sources_group = QGroupBox("Select Sources")
        sources_group.setStyleSheet("""
            QGroupBox {
                font-size: 14px;
                font-weight: 500;
                padding: 16px;
                margin-top: 16px;
            }
        """)
        sources_layout = QVBoxLayout()
        
        # Get unique sources
        sources = self.review_system.get_sources()
        
        for source in sources:
            cb = QCheckBox(source['title'])
            cb.setStyleSheet("""
                QCheckBox {
                    font-size: 14px;
                    padding: 8px;
                }
            """)
            cb.source_path = source['audio_path']
            cb.toggled.connect(lambda checked, s=source['audio_path']: 
                self.toggle_source(s, checked))
            sources_layout.addWidget(cb)
        
        sources_group.setLayout(sources_layout)
        layout.addWidget(sources_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.random_order = QCheckBox("Random Order")
        self.random_order.setChecked(True)
        options_layout.addWidget(self.random_order)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Start button
        start_btn = QPushButton("Start Focus Session")
        start_btn.setStyleSheet("""
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
        start_btn.clicked.connect(self.start_session)
        layout.addWidget(start_btn)

    def toggle_source(self, source_path: str, checked: bool):
        if checked:
            self.selected_sources.add(source_path)
        else:
            self.selected_sources.discard(source_path)

    def start_session(self):
        if not self.selected_sources:
            QMessageBox.warning(
                self,
                "No Sources Selected",
                "Please select at least one source to review."
            )
            return

        self.accept()
        dialog = FocusReviewDialog(
            self.selected_sources,
            self.review_system,
            self.random_order.isChecked(),
            self.parent()
        )
        dialog.exec()

class FocusReviewDialog(QDialog):
    def __init__(self, sources, review_system, random_order=True, parent=None):
        super().__init__(parent)
        self.review_system = review_system
        self.sources = sources
        self.cards = self.get_cards(random_order)
        self.current_index = 0
        
        self.setup_ui()
        self.setWindowTitle("Focus Review")
        self.resize(600, 400)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        # Progress header
        self.progress_label = QLabel()
        self.progress_label.setStyleSheet("""
            color: #6b7280;
            font-size: 14px;
        """)
        layout.addWidget(self.progress_label)

        # Card container
        self.card_container = QVBoxLayout()
        layout.addLayout(self.card_container)

        # Show first card
        self.show_current_card()

    def get_cards(self, random_order):
        cards = [
            card for card in self.review_system.items 
            if card['audio_path'] in self.sources
        ]
        if random_order:
            random.shuffle(cards)
        return cards

    def show_current_card(self):
        # Clear previous card
        while self.card_container.count():
            item = self.card_container.takeAt(0)
            if item.widget():
                item.widget().cleanup()
                item.widget().deleteLater()

        if self.current_index < len(self.cards):
            # Update progress
            self.progress_label.setText(
                f"Card {self.current_index + 1} of {len(self.cards)}"
            )

            # Show card
            card = AudioCard(
                self.cards[self.current_index],
                self.cards[self.current_index]['audio_path'],
                self.review_system
            )
            card.reviewed.connect(self.handle_review)
            self.card_container.addWidget(card)
        else:
            # Session complete
            self.show_completion()

    def handle_review(self, card_id: str, response: str):
        """Handle card review"""
        try:
            self.review_system.process_review(card_id, response)
            self.current_index += 1
            self.show_current_card()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to process review: {str(e)}"
            )

    def show_completion(self):
        """Show completion message"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Session Complete")
        msg.setText("Focus session complete!")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
        self.accept()