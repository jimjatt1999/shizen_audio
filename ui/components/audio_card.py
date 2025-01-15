# ui/components/audio_card.py

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QGraphicsDropShadowEffect,
                           QMessageBox, QInputDialog)
from PyQt6.QtCore import pyqtSignal, QUrl, Qt
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtGui import QColor
from .waveform import PulsingWaveform
from ..components.analysis_dialog import AnalysisDialog
from audio_processors.ai_service import AIHelper

class AudioCard(QWidget):
    reviewed = pyqtSignal(str, str)  # segment_id, response
    deleted = pyqtSignal(str)  # segment_id
    skipped = pyqtSignal(str)  # segment_id
    edited = pyqtSignal(str, str)  # segment_id, new_text

    def get_review_status(self, reviews):
        if reviews == 0:
            return "New"
        elif reviews < 3:
            return f"Reviewed {reviews}x"
        else:
            return f"Mastered ({reviews}x)"


    def __init__(self, segment, audio_path, review_system):
        super().__init__()
        self.segment = segment
        self.audio_path = audio_path
        self.review_system = review_system
        self.is_playing = False
        self.player = None
        self.audio_output = None
        self.speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        self.current_speed_index = 2  # Default 1.0
        
        # Initialize audio before UI
        self.setup_audio()
        self.setup_ui()
        
    def __init__(self, segment, audio_path, review_system):
        super().__init__()
        self.segment = segment
        self.audio_path = audio_path
        self.review_system = review_system
        self.is_playing = False
        self.player = None
        self.audio_output = None
        self.speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
        self.current_speed_index = 2  # Default 1.0
        
        # Initialize audio before UI
        self.setup_audio()
        self.setup_ui()

    def setup_ui(self):
        """Setup the UI components"""
        # Main card layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(20)

        # Top row with play button and actions
        top_row = QHBoxLayout()
        top_row.setSpacing(16)

        # Status label
        stats_label = QLabel(self.get_review_status(self.segment.get('reviews', 0)))
        stats_label.setStyleSheet("""
            color: #9ca3af;
            font-size: 12px;
        """)
        top_row.addWidget(stats_label)
        top_row.addStretch()

        # Play controls container
        play_controls = QHBoxLayout()
        play_controls.setSpacing(8)

        # Play button
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(28, 28)
        self.play_btn.clicked.connect(self.toggle_audio)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #666;
                border: none;
                border-radius: 14px;
                font-size: 13px;
                padding: 0;
            }
            QPushButton:hover {
                background: #e5e7eb;
                color: #333;
            }
        """)

        # Add waveform with seeking
        self.waveform = PulsingWaveform()
        self.waveform.seeked.connect(self.seek_audio)

        # Speed button
        self.speed_btn = QPushButton("1.0x")
        self.speed_btn.setFixedHeight(28)
        self.speed_btn.clicked.connect(self.cycle_speed)
        self.speed_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                color: #666;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: #e5e7eb;
                color: #333;
            }
        """)

        play_controls.addWidget(self.play_btn)
        play_controls.addWidget(self.waveform, 1)  # Add stretch factor of 1
        play_controls.addWidget(self.speed_btn)

        # Action buttons
        actions_container = QWidget()
        actions_layout = QHBoxLayout(actions_container)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        actions_layout.setSpacing(8)

        # Create action buttons
        skip_btn = QPushButton("Skip")
        edit_btn = QPushButton("Edit")
        delete_btn = QPushButton("Delete")

        for btn in [skip_btn, edit_btn, delete_btn]:
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #f3f4f6;
                    color: #666;
                    border: none;
                    border-radius: 4px;
                    font-size: 12px;
                    padding: 0 12px;
                }
                QPushButton:hover {
                    background: #e5e7eb;
                    color: #333;
                }
            """)
            actions_layout.addWidget(btn)

        # Connect action buttons
        skip_btn.clicked.connect(self.skip_card)
        edit_btn.clicked.connect(self.edit_card)
        delete_btn.clicked.connect(self.delete_card)

        top_row.addLayout(play_controls)
        top_row.addWidget(actions_container)

        # Japanese text
        text_label = QLabel(self.segment['text'])
        text_label.setWordWrap(True)
        text_label.setStyleSheet("""
            font-size: 16px;
            color: #1f2937;
            line-height: 1.6;
            padding: 0;
            background: transparent;
        """)

        # Response buttons row
        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        # Button styles
        buttons = [
            ("Again", "#fef2f2", "#ef4444", "#dc2626"),
            ("Hard", "#fffbeb", "#f59e0b", "#d97706"),
            ("Good", "#f0fdf4", "#22c55e", "#16a34a"),
            ("Easy", "#eff6ff", "#3b82f6", "#2563eb")
        ]

        for btn_text, bg_color, text_color, hover_color in buttons:
            btn = QPushButton(btn_text)
            btn.clicked.connect(lambda checked, t=btn_text.lower(): self.handle_response(t))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(36)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg_color};
                    color: {text_color};
                    border: none;
                    border-radius: 6px;
                    padding: 0 24px;
                    font-size: 13px;
                    font-weight: 500;
                }}
                QPushButton:hover {{
                    background: {hover_color};
                    color: white;
                }}
            """)
            button_row.addWidget(btn)

        # Add all components to main layout
        layout.addLayout(top_row)
        layout.addWidget(text_label)
        layout.addLayout(button_row)

        # Card styling
        self.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 12px;
                border: 1px solid #e5e7eb;
            }
        """)
        
        # Add drop shadow effect
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 25))
        self.setGraphicsEffect(shadow)
        ai_btn = QPushButton("AI Help")
        ai_btn.setFixedHeight(28)
        ai_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ai_btn.setStyleSheet("""
            QPushButton {
                background: #8b5cf6;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                padding: 0 12px;
            }
            QPushButton:hover {
                background: #7c3aed;
            }
        """)
        ai_btn.clicked.connect(self.show_analysis)
        actions_layout.addWidget(ai_btn)
        
    def show_analysis(self):
        """Show AI analysis dialog"""
        try:
            # Create and show dialog with review_system
            dialog = AnalysisDialog(
                text=self.segment['text'],
                review_system=self.review_system,  # Pass entire review_system instead of individual components
                parent=self
            )
            dialog.exec()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to show analysis: {str(e)}"
            )

    def seek_audio(self, position):
        """Handle seeking in audio"""
        if self.player:
            start_time = int(self.segment['start_time'] * 1000)
            end_time = int(self.segment['end_time'] * 1000)
            duration = end_time - start_time
            
            # Calculate new position
            new_pos = start_time + (duration * position)
            
            # Set position
            self.player.setPosition(int(new_pos))
            self.waveform.set_progress(position)
            
            # Start playing if not already
            if not self.is_playing:
                self.play_audio()

    def setup_audio(self):
        """Initialize the audio player"""
        try:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.player.positionChanged.connect(self.check_position)
            self.player.setSource(QUrl.fromLocalFile(self.audio_path))
            self.audio_output.setVolume(1.0)
            print(f"Audio setup complete for: {self.audio_path}")
        except Exception as e:
            print(f"Error setting up audio: {e}")

    def cycle_speed(self):
        """Cycle through playback speeds"""
        self.current_speed_index = (self.current_speed_index + 1) % len(self.speeds)
        speed = self.speeds[self.current_speed_index]
        self.player.setPlaybackRate(speed)
        self.speed_btn.setText(f"{speed}x")

    def toggle_audio(self):
        """Toggle between playing and stopping audio"""
        if self.is_playing:
            self.stop_audio()
        else:
            self.play_audio()

    def play_audio(self):
        """Start playing the audio segment"""
        try:
            start_pos = int(self.segment['start_time'] * 1000)
            self.player.setPosition(start_pos)
            self.player.play()
            self.is_playing = True
            self.waveform.start_animation()
            self.play_btn.setText("■")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background: #e5e7eb;
                    color: #333;
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #d1d5db;
                }
            """)
        except Exception as e:
            print(f"Error playing audio: {e}")

    def check_position(self, position):
        """Update waveform progress as audio plays"""
        if self.is_playing:
            start_time = int(self.segment['start_time'] * 1000)
            end_time = int(self.segment['end_time'] * 1000)
            duration = end_time - start_time
            current = position - start_time
            
            # Update waveform progress
            if duration > 0:
                progress = current / duration
                self.waveform.set_progress(progress)
            
            # Check if we've reached the end
            if position >= end_time:
                self.stop_audio()

    def stop_audio(self):
        """Stop the audio playback"""
        try:
            if self.player:
                self.player.stop()
            self.is_playing = False
            self.waveform.stop_animation()
            self.play_btn.setText("▶")
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background: #f3f4f6;
                    color: #666;
                    border: none;
                    border-radius: 14px;
                    font-size: 13px;
                    padding: 0;
                }
                QPushButton:hover {
                    background: #e5e7eb;
                    color: #333;
                }
            """)
        except Exception as e:
            print(f"Error stopping audio: {e}")

    def handle_response(self, response):
        """Handle review response button clicks"""
        self.stop_audio()
        self.reviewed.emit(self.segment['id'], response)

    def skip_card(self):
        """Skip this card for now"""
        self.stop_audio()
        self.skipped.emit(self.segment['id'])

    def delete_card(self):
        """Delete this card permanently"""
        reply = QMessageBox.question(
            self, 
            'Confirm Deletion',
            'Delete this card permanently?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.stop_audio()
            self.deleted.emit(self.segment['id'])

    def edit_card(self):
        """Edit card text"""
        text, ok = QInputDialog.getMultiLineText(
            self,
            'Edit Card',
            'Edit text:',
            self.segment['text']
        )
        if ok and text.strip():
            self.edited.emit(self.segment['id'], text.strip())

    def cleanup(self):
        """Clean up media resources"""
        try:
            if self.player:
                self.stop_audio()
                self.player.deleteLater()
                self.player = None
            if self.audio_output:
                self.audio_output.deleteLater()
                self.audio_output = None
        except Exception as e:
            print(f"Error during cleanup: {e}")