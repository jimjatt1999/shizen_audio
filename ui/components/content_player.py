from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                           QLabel, QSlider, QScrollArea, QSplitter)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl
from .waveform import PulsingWaveform  # Import the waveform component

class ContentPlayer(QWidget):

    def __init__(self, audio_path: str, segments: list):
        super().__init__()
        self.audio_path = audio_path
        self.segments = segments
        self.current_segment = None
        self.is_playing = False
        
        # Setup audio
        try:
            self.player = QMediaPlayer()
            self.audio_output = QAudioOutput()
            self.player.setAudioOutput(self.audio_output)
            self.player.setSource(QUrl.fromLocalFile(self.audio_path))
            self.audio_output.setVolume(1.0)
            
            # Connect signals
            self.player.positionChanged.connect(self.update_position)
            self.player.durationChanged.connect(self.update_duration)
            
            print(f"Audio setup complete for: {self.audio_path}")  # Debug print
        except Exception as e:
            print(f"Error setting up audio: {e}")  # Debug print
            raise
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Main content splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Player controls and waveform
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        # Player controls
        controls = QHBoxLayout()
        
        self.play_btn = QPushButton("▶")
        self.play_btn.setFixedSize(40, 40)
        self.play_btn.clicked.connect(self.toggle_playback)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background: #2196F3;
                color: white;
                border: none;
                border-radius: 20px;
                font-size: 16px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        """)
        
        # Add waveform
        self.waveform = PulsingWaveform()
        self.waveform.seeked.connect(self.seek_to_position)
        
        # Time label
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setStyleSheet("color: #6b7280; font-size: 13px;")
        
        controls.addWidget(self.play_btn)
        controls.addWidget(self.waveform, stretch=1)
        controls.addWidget(self.time_label)
        
        left_layout.addLayout(controls)
        
        # Right side - Segments text
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        segments_scroll = QScrollArea()
        segments_scroll.setWidgetResizable(True)
        segments_widget = QWidget()
        self.segments_layout = QVBoxLayout(segments_widget)
        
        for segment in self.segments:
            segment_widget = self.create_segment_widget(segment)
            self.segments_layout.addWidget(segment_widget)
        
        segments_scroll.setWidget(segments_widget)
        right_layout.addWidget(segments_scroll)
        
        # Add widgets to splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # Set initial sizes (40% left, 60% right)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)

    def create_segment_widget(self, segment):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)
        
        time_btn = QPushButton(self.format_time(segment['start']))
        time_btn.setFixedWidth(60)
        time_btn.clicked.connect(lambda: self.seek_to_segment(segment))
        time_btn.setStyleSheet("""
            QPushButton {
                background: #f3f4f6;
                border: none;
                border-radius: 4px;
                padding: 4px;
                color: #6b7280;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e5e7eb;
            }
        """)
        
        text = QLabel(segment['text'])
        text.setWordWrap(True)
        text.setStyleSheet("color: #1f2937; font-size: 14px;")
        
        layout.addWidget(time_btn)
        layout.addWidget(text, stretch=1)
        
        widget.setStyleSheet("""
            QWidget {
                background: white;
                border-radius: 4px;
            }
            QWidget:hover {
                background: #f9fafb;
            }
        """)
        
        return widget

    def toggle_playback(self):
        """Toggle between playing and stopping audio"""
        try:
            if self.is_playing:
                self.player.pause()
                self.play_btn.setText("▶")
                self.is_playing = False
                self.waveform.stop_animation()
            else:
                print(f"Starting playback of: {self.audio_path}")  # Debug print
                self.player.play()
                self.play_btn.setText("⏸")
                self.is_playing = True
                self.waveform.start_animation()
        except Exception as e:
            print(f"Playback error: {str(e)}")  # Debug print
            QMessageBox.critical(
                self,
                "Playback Error",
                f"Failed to play audio: {str(e)}"
            )

    def seek_to_position(self, position):
        duration = self.player.duration()
        self.player.setPosition(int(position * duration))

    def seek_to_segment(self, segment):
        position = int(segment['start'] * 1000)  # Convert to milliseconds
        self.player.setPosition(position)
        if not self.is_playing:
            self.toggle_playback()

    def update_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            self.waveform.set_progress(position / duration)
        self.time_label.setText(
            f"{self.format_time(position/1000)} / "
            f"{self.format_time(duration/1000)}"
        )

    def update_duration(self, duration):
        self.time_label.setText(
            f"00:00 / {self.format_time(duration/1000)}"
        )

    def format_time(self, seconds):
        minutes = int(seconds / 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def cleanup(self):
        """Clean up resources"""
        if self.player:
            self.player.stop()
            self.player.deleteLater()
        if self.audio_output:
            self.audio_output.deleteLater()