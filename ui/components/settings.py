# ui/components/settings.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout,
                           QPushButton, QSpinBox, QMessageBox, QLabel, QComboBox)
from PyQt6.QtCore import pyqtSignal, Qt

class Settings(QWidget):
    settingsChanged = pyqtSignal()

    # Define available languages
    LANGUAGES = [
        ("Japanese", "ja"),
        ("English", "en"),
        ("Chinese", "zh"),
        ("Korean", "ko"),
        ("Spanish", "es"),
        ("French", "fr"),
        ("German", "de"),
        ("Vietnamese", "vi"),
        ("Thai", "th"),
        ("Indonesian", "id"),
    ]

    def __init__(self, review_system):
        super().__init__()
        self.review_system = review_system
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: #1f2937;
            margin-bottom: 16px;
        """)
        layout.addWidget(title)

        # Language Settings Group
        language_group = QGroupBox("Language Settings")
        language_group.setStyleSheet("""
            QGroupBox {
                font-size: 16px;
                font-weight: 500;
                padding: 24px;
                margin-top: 16px;
                border: 1px solid #e5e7eb;
                border-radius: 12px;
                background: white;
            }
            QGroupBox::title {
                color: #1f2937;
                padding: 0 12px;
            }
        """)
        
        language_layout = QFormLayout()
        language_layout.setSpacing(16)
        language_layout.setContentsMargins(16, 24, 16, 16)
        
        # Language selectors
        self.learning_language = QComboBox()
        self.learning_language.setFixedHeight(36)
        self.native_language = QComboBox()
        self.native_language.setFixedHeight(36)
        
        for name, code in self.LANGUAGES:
            self.learning_language.addItem(name, code)
            self.native_language.addItem(name, code)

        # Style the comboboxes
        combo_style = """
            QComboBox {
                padding: 4px 8px;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                font-size: 14px;
            }
            QComboBox:focus {
                border: 2px solid #2196F3;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 8px;
            }
        """
        self.learning_language.setStyleSheet(combo_style)
        self.native_language.setStyleSheet(combo_style)

        # Language labels
        language_label_style = """
            QLabel {
                font-size: 14px;
                color: #4b5563;
            }
        """
        learning_label = QLabel("Learning Language:")
        learning_label.setStyleSheet(language_label_style)
        native_label = QLabel("Reference Language:")
        native_label.setStyleSheet(language_label_style)

        language_layout.addRow(learning_label, self.learning_language)
        language_layout.addRow(native_label, self.native_language)
        
        language_group.setLayout(language_layout)
        layout.addWidget(language_group)

        # Study Settings Group (existing)
        study_group = QGroupBox("Learning Settings")
        study_group.setStyleSheet(language_group.styleSheet())  # Use same style
        
        study_layout = QFormLayout()
        study_layout.setSpacing(16)
        study_layout.setContentsMargins(16, 24, 16, 16)
        
        # New cards per day setting
        self.new_cards_limit = QSpinBox()
        self.new_cards_limit.setRange(1, 100)
        self.new_cards_limit.setFixedHeight(36)
        self.new_cards_limit.setToolTip(
            "Maximum number of new cards you want to learn each day.\n"
            "Due cards will always be shown for review."
        )
        self.new_cards_limit.setStyleSheet("""
            QSpinBox {
                padding: 4px 8px;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                font-size: 14px;
            }
            QSpinBox:focus {
                border: 2px solid #2196F3;
            }
        """)

        # Cards per session setting
        self.cards_per_session = QSpinBox()
        self.cards_per_session.setRange(1, 5)
        self.cards_per_session.setFixedHeight(36)
        self.cards_per_session.setToolTip(
            "How many cards to show at once.\n"
            "Smaller groups can help prevent overwhelm."
        )
        self.cards_per_session.setStyleSheet(self.new_cards_limit.styleSheet())

        # Labels styling
        label_style = """
            QLabel {
                font-size: 14px;
                color: #4b5563;
            }
        """
        new_cards_label = QLabel("New cards Learned per day:")
        new_cards_label.setStyleSheet(label_style)
        
        cards_per_session_label = QLabel("Cards shown at once in Review Feed:")
        cards_per_session_label.setStyleSheet(label_style)
        
        study_layout.addRow(new_cards_label, self.new_cards_limit)
        study_layout.addRow(cards_per_session_label, self.cards_per_session)

        # Reset Progress button
        reset_progress_btn = QPushButton("Reset Learning Progress")
        reset_progress_btn.setToolTip(
            "Reset all learning progress.\n"
            "Cards will be marked as new but their content will be preserved."
        )
        reset_progress_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_progress_btn.setStyleSheet("""
            QPushButton {
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: 500;
                margin-top: 16px;
            }
            QPushButton:hover {
                background: #dc2626;
            }
        """)
        reset_progress_btn.clicked.connect(self.reset_stats)
        study_layout.addRow("", reset_progress_btn)
        
        study_group.setLayout(study_layout)
        layout.addWidget(study_group)

        # Description text
        description = QLabel(
            "Note: Due cards will always be shown regardless of settings, "
            "as they need to be reviewed to maintain your progress."
        )
        description.setWordWrap(True)
        description.setStyleSheet("""
            color: #6b7280;
            font-size: 13px;
            font-style: italic;
            margin-top: 8px;
        """)
        layout.addWidget(description)

        # Save Button
        save_btn = QPushButton("Save Changes")
        save_btn.setFixedHeight(44)
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 0 32px;
                font-size: 14px;
                font-weight: 500;
                margin-top: 24px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)

        layout.addStretch()

        # Main widget styling
        self.setStyleSheet("""
            QWidget {
                background: #f9fafb;
            }
        """)

    def load_current_settings(self):
        """Load current settings into UI"""
        try:
            settings = self.review_system.get_settings()
            self.new_cards_limit.setValue(settings.get('daily_new_cards', 20))
            self.cards_per_session.setValue(settings.get('cards_per_session', 3))
            
            # Set language selections
            learning_idx = self.learning_language.findData(settings.get('learning_language', 'ja'))
            native_idx = self.native_language.findData(settings.get('native_language', 'en'))
            
            if learning_idx >= 0:
                self.learning_language.setCurrentIndex(learning_idx)
            if native_idx >= 0:
                self.native_language.setCurrentIndex(native_idx)
                
        except Exception as e:
            print(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Warning", "Could not load current settings.")

    def save_settings(self):
        """Save settings and notify of changes"""
        try:
            self.review_system.update_settings(
                daily_new_cards=self.new_cards_limit.value(),
                cards_per_session=self.cards_per_session.value(),
                learning_language=self.learning_language.currentData(),
                native_language=self.native_language.currentData()
            )
            
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("Settings saved successfully!")
            msg.setWindowTitle("Success")
            msg.setStyleSheet("""
                QMessageBox {
                    background: white;
                }
                QMessageBox QLabel {
                    color: #1f2937;
                }
                QPushButton {
                    background: #2196F3;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background: #1976D2;
                }
            """)
            msg.exec()
            
            self.settingsChanged.emit()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save settings: {str(e)}"
            )

    def reset_stats(self):
        """Reset all statistics with clear explanation"""
        msg = QMessageBox(self)
        msg.setWindowTitle("Reset Learning Progress")
        msg.setIcon(QMessageBox.Icon.Warning)
        
        explanation = (
            "This will reset:\n"
            "• All learning progress\n"
            "• Study streak\n"
            "• Review history\n"
            "• Card intervals\n\n"
            "Cards will be marked as new again, but their content will be preserved.\n"
            "This cannot be undone. Continue?"
        )
        
        msg.setText(explanation)
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | 
            QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.No)
        
        msg.setStyleSheet("""
            QMessageBox {
                background: white;
            }
            QMessageBox QLabel {
                color: #1f2937;
                font-size: 14px;
                min-width: 300px;
            }
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton[text="Yes"] {
                background: #ef4444;
                color: white;
                border: none;
            }
            QPushButton[text="Yes"]:hover {
                background: #dc2626;
            }
            QPushButton[text="No"] {
                background: #e5e7eb;
                color: #374151;
                border: none;
            }
            QPushButton[text="No"]:hover {
                background: #d1d5db;
            }
        """)
        
        if msg.exec() == QMessageBox.StandardButton.Yes:
            try:
                self.review_system.reset_stats()
                self.settingsChanged.emit()
                
                QMessageBox.information(
                    self,
                    "Success",
                    "Learning progress has been reset.\n"
                    "All cards are now marked as new."
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to reset progress: {str(e)}"
                )