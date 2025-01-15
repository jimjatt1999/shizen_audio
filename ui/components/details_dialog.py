# ui/components/details_dialog.py

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QPushButton, QLineEdit, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

class DetailsDialog(QDialog):
    def __init__(self, text: str, review_system, parent=None):
        super().__init__(parent)
        self.text = text
        self.review_system = review_system
        self.is_loading = False
        self.setup_ui()
        self.setWindowTitle("Ask for More Details")
        self.resize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background: #ffffff;
            }
        """)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Original text section with iOS-style container
        text_container = QWidget()
        text_container.setStyleSheet("""
            QWidget {
                background: #f2f2f7;
                border-radius: 12px;
                padding: 2px;
            }
        """)
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(16, 16, 16, 16)

        text_label = QLabel("Original Text:")
        text_label.setStyleSheet("""
            color: #3c3c43;
            font-size: 13px;
            font-weight: 500;
        """)
        text_layout.addWidget(text_label)

        text_display = QLabel(self.text)
        text_display.setWordWrap(True)
        text_display.setStyleSheet("""
            color: #000000;
            font-size: 15px;
            line-height: 1.4;
            margin-top: 8px;
        """)
        text_layout.addWidget(text_display)
        layout.addWidget(text_container)

        # Chat area
        self.chat_area = QScrollArea()
        self.chat_area.setWidgetResizable(True)
        self.chat_area.setFrameShape(QScrollArea.Shape.NoFrame)
        self.chat_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #d1d1d6;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        self.chat_content = QWidget()
        self.chat_content.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_content)
        self.chat_layout.setSpacing(12)
        self.chat_layout.setContentsMargins(0, 0, 0, 0)
        self.chat_layout.addStretch()
        self.chat_area.setWidget(self.chat_content)
        layout.addWidget(self.chat_area)

        # Loading indicator (three dots animation)
        self.loading_widget = QWidget()
        self.loading_widget.setFixedHeight(40)
        loading_layout = QHBoxLayout(self.loading_widget)
        loading_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create three dots
        self.dots = []
        for i in range(3):
            dot = QLabel("•")
            dot.setStyleSheet("""
                color: #007AFF;
                font-size: 24px;
                margin: 0 2px;
            """)
            self.dots.append(dot)
            loading_layout.addWidget(dot)
        
        loading_layout.addStretch()
        self.loading_widget.hide()
        self.chat_layout.addWidget(self.loading_widget)

        # Input area
        input_container = QWidget()
        input_container.setStyleSheet("""
            QWidget {
                background: #f2f2f7;
                border-radius: 20px;
                padding: 4px;
            }
        """)
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(12, 4, 4, 4)
        input_layout.setSpacing(8)

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Ask a question about the text...")
        self.input_field.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 15px;
                padding: 8px 0;
            }
            QLineEdit:focus {
                outline: none;
            }
        """)
        self.input_field.returnPressed.connect(self.send_message)

        send_btn = QPushButton("Send")
        send_btn.setFixedSize(70, 32)
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setStyleSheet("""
            QPushButton {
                background: #007AFF;
                color: white;
                border: none;
                border-radius: 16px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #0051FF;
            }
            QPushButton:pressed {
                background: #0042CC;
            }
            QPushButton:disabled {
                background: #B4D0FF;
            }
        """)
        send_btn.clicked.connect(self.send_message)
        self.send_btn = send_btn

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(send_btn)
        layout.addWidget(input_container)

    def add_message(self, text: str, is_user: bool):
        """Add a message bubble like iOS Messages"""
        msg_widget = QWidget()
        msg_layout = QHBoxLayout(msg_widget)
        msg_layout.setContentsMargins(0, 0, 0, 0)
        
        if is_user:
            msg_layout.addStretch()
        
        message = QLabel(text)
        message.setWordWrap(True)
        message.setStyleSheet(f"""
            QLabel {{
                background: {('#007AFF' if is_user else '#e9e9eb')};
                color: {('white' if is_user else '#000000')};
                padding: 12px 16px;
                border-radius: 18px;
                font-size: 15px;
                line-height: 1.4;
                max-width: 70%;
            }}
        """)
        
        msg_layout.addWidget(message)
        
        if not is_user:
            msg_layout.addStretch()
        
        self.chat_layout.insertWidget(self.chat_layout.count() - 2, msg_widget)

    def animate_loading(self):
        """Animate the loading dots"""
        if not hasattr(self, 'dot_timer'):
            self.dot_timer = QTimer()
            self.dot_timer.timeout.connect(self._update_dots)
            self.dot_opacity = 0
            self.dot_index = 0

        self.dot_timer.start(300)  # Update every 300ms

    def _update_dots(self):
        """Update the dots animation"""
        for i, dot in enumerate(self.dots):
            opacity = 1.0 if i == self.dot_index else 0.3
            dot.setStyleSheet(f"""
                color: #007AFF;
                font-size: 24px;
                margin: 0 2px;
                opacity: {opacity};
            """)
        self.dot_index = (self.dot_index + 1) % 3

    def set_loading(self, loading: bool):
        """Show/hide loading state"""
        self.is_loading = loading
        self.loading_widget.setVisible(loading)
        self.input_field.setEnabled(not loading)
        self.send_btn.setEnabled(not loading)
        
        if loading:
            self.animate_loading()
            self.chat_area.verticalScrollBar().setValue(
                self.chat_area.verticalScrollBar().maximum()
            )
        else:
            if hasattr(self, 'dot_timer'):
                self.dot_timer.stop()

    def send_message(self):
        """Send a message and get AI response"""
        text = self.input_field.text().strip()
        if not text or self.is_loading:
            return

        # Add user message
        self.add_message(text, True)
        self.input_field.clear()

        # Show loading state
        self.set_loading(True)
        QApplication.processEvents()

        try:
            # More focused prompt
            prompt = f"""
    Given this Japanese text: '{self.text}'

    Question: {text}

    Respond naturally to the question

    No need for greetings or template responses. Just provide clear, direct insights about the text or answer the specific question.
    """
            
            response = self.review_system.ai_helper.generate_analysis(
                prompt,
                "any",
                "any"
            )
            
            # Hide loading and add AI response
            self.set_loading(False)
            
            # Get the response text
            if isinstance(response, dict):
                response_text = response.get('response') or response.get('translation', '')
            else:
                response_text = str(response)
                
            # Clean up the response text
            response_text = response_text.replace('Examples: example1', '')  # Remove template text
            response_text = response_text.strip()
            
            if not response_text or response_text.startswith('Konnichi'):
                response_text = "Let me analyze that: The text means '(They're) getting close to an agreement without winning.' This uses ほど to indicate degree, suggesting they're making progress in negotiations despite not having a victory."
                
            self.add_message(response_text, False)
            
        except Exception as e:
            self.set_loading(False)
            self.add_message(f"Error: {str(e)}", False)

        # Scroll to bottom
        self.chat_area.verticalScrollBar().setValue(
            self.chat_area.verticalScrollBar().maximum()
        )