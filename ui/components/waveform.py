# ui/components/waveform.py

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QPainterPath, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class PulsingWaveform(QWidget):
    seeked = pyqtSignal(float)  # Signal to emit seek position (0.0 to 1.0)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setMinimumWidth(200)
        self.bars = 24  # Number of bars
        self.is_playing = False
        self.progress = 0
        self.amplitudes = [0.3] * self.bars
        
        # Animation timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_amplitudes)
        self.timer.setInterval(50)  # Update every 50ms for smoother animation
        
        # Enable mouse tracking
        self.setMouseTracking(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def start_animation(self):
        self.is_playing = True
        self.timer.start()

    def stop_animation(self):
        self.is_playing = False
        self.timer.stop()
        self.amplitudes = [0.3] * self.bars
        self.update()

    def set_progress(self, value):
        """Set the current playback progress (0.0 to 1.0)"""
        self.progress = max(0, min(1, value))
        self.update()

    def update_amplitudes(self):
        """Create random amplitudes for animation effect"""
        if self.is_playing:
            import random
            # More natural-looking animation
            new_amplitudes = []
            for i, current in enumerate(self.amplitudes):
                # Smooth transition between amplitudes
                target = random.uniform(0.2, 0.8)
                new_amp = current + (target - current) * 0.3
                new_amplitudes.append(new_amp)
            self.amplitudes = new_amplitudes
            self.update()

    def mousePressEvent(self, event):
        """Handle click for seeking"""
        x = event.position().x()
        width = self.width()
        position = max(0, min(1, x / width))
        self.seeked.emit(position)

    def mouseMoveEvent(self, event):
        """Show seek preview on hover"""
        # Could add hover effect here if desired
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()
        bar_width = width / (self.bars * 2)  # Leave space between bars
        
        # Draw background
        painter.fillRect(0, 0, width, height, QColor("#f3f4f6"))

        # Calculate progress width
        progress_width = width * self.progress

        for i in range(self.bars):
            # Calculate bar dimensions
            x = i * (width / self.bars)
            amplitude = self.amplitudes[i]
            bar_height = height * amplitude
            y = (height - bar_height) / 2

            # Create bar path
            path = QPainterPath()
            path.addRoundedRect(x + 2, y, bar_width, bar_height, 2, 2)

            # Determine bar color based on position and playing state
            if x <= progress_width:
                if self.is_playing:
                    painter.fillPath(path, QColor("#2196F3"))  # Blue for played portion
                else:
                    painter.fillPath(path, QColor("#90CAF9"))  # Lighter blue when paused
            else:
                painter.fillPath(path, QColor("#e5e7eb"))  # Gray for unplayed portion