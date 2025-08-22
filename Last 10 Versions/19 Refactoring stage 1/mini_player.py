from PyQt6.QtWidgets import QWidget, QPushButton, QApplication
from PyQt6.QtCore import Qt, QPoint, QSize, QTimer
from PyQt6.QtGui import QPixmap, QIcon, QPainter, QImage, QRegion, QPainterPath, QColor
from PIL import Image, ImageFilter
import io

MINI_RADIUS = 40

class TintedAlbumArt(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setGeometry(0, 0, 220, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def resizeEvent(self, event):
        self.setGeometry(0, 0, self.width(), self.height())
        super().resizeEvent(event)

    def setPixmap(self, pixmap):
        self._pixmap = pixmap
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # No clipping path applied
        
        if self._pixmap:
            scaled = self._pixmap.scaled(220, 220, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(0, 0, scaled)
        else:
            painter.fillRect(0, 0, 220, 220, Qt.GlobalColor.darkGray)

class MiniPlayer(QWidget):
    def __init__(self, main_player, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_player = main_player
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(220, 220)
        self._drag_pos = None
        self._setup_ui()
        # Removed drop shadow effect for a clean edge

    def _setup_ui(self):
        self.album_art = TintedAlbumArt(self)
        self.album_art.setGeometry(0, 0, self.width(), self.height())
        btn_style = """
            QPushButton {
                background: rgba(0,0,0,80);
                border: none;
                border-radius: 18px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,140);
            }
        """
        # Control buttons
        self.prev_btn = QPushButton(self)
        self.prev_btn.setIcon(QIcon(self.main_player.prev_icon))
        self.prev_btn.setIconSize(QSize(20, 20))
        self.prev_btn.setGeometry(20, 94, 36, 36)
        self.prev_btn.setStyleSheet(btn_style)
        self.play_btn = QPushButton(self)
        self.play_btn.setIcon(QIcon(self.main_player.play_icon))
        self.play_btn.setIconSize(QSize(24, 24))
        self.play_btn.setGeometry(90, 90, 40, 40)
        self.play_btn.setStyleSheet(btn_style)
        self.next_btn = QPushButton(self)
        self.next_btn.setIcon(QIcon(self.main_player.next_icon))
        self.next_btn.setIconSize(QSize(20, 20))
        self.next_btn.setGeometry(164, 94, 36, 36)
        self.next_btn.setStyleSheet(btn_style)
        self.close_btn = QPushButton('✕', self)
        self.close_btn.setGeometry(172, 24, 24, 24)  # More inside
        self.close_btn.setStyleSheet("QPushButton { background: rgba(0,0,0,120); border: none; border-radius: 12px; color: white; font-size: 16px; } QPushButton:hover { background: rgba(255,0,0,180); }")
        self.return_btn = QPushButton('⮌', self)
        self.return_btn.setGeometry(24, 24, 24, 24)  # More inside
        self.return_btn.setStyleSheet("QPushButton { background: rgba(0,0,0,120); border: none; border-radius: 12px; color: white; font-size: 16px; } QPushButton:hover { background: rgba(0,255,0,180); }")
        # Connect
        self.prev_btn.clicked.connect(self.main_player.play_previous)
        self.play_btn.clicked.connect(self.main_player.toggle_play_pause)
        self.next_btn.clicked.connect(self.main_player.play_next)
        self.close_btn.clicked.connect(self._close)
        self.return_btn.clicked.connect(self._return_to_main)
        
        # Connect to main player's state changes to update play button icon
        self.main_player.controller.track_ended.connect(self.update_play_button_icon)

        # Connect to main player signal if it exists
        if hasattr(self.main_player, 'play_state_changed_signal'):
            self.main_player.play_state_changed_signal.connect(self.update_play_button_icon)
                
        # Set up a timer to periodically check the main player's state
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.update_play_button_icon)
        self.sync_timer.start(50)  # Check every 50ms for faster response

    def update_play_button_icon(self):
        """Update the play button icon based on the main player's state"""
        if self.main_player.controller.is_playing():
            self.play_btn.setIcon(QIcon(self.main_player.pause_icon))
        else:
            self.play_btn.setIcon(QIcon(self.main_player.play_icon))

    def set_album_art(self, pixmap):
        self.album_art.setPixmap(pixmap)

    def _close(self):
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        app = QApplication.instance()
        if app is not None:
            app.quit()

    def _return_to_main(self):
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        self.close()
        self.main_player.show()

    def showEvent(self, event):
        """Restart the sync timer when the mini player is shown"""
        super().showEvent(event)
        if hasattr(self, 'sync_timer'):
            self.sync_timer.start(50)  # Restart the timer
        # Immediately update the play button icon
        self.update_play_button_icon()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None 

    def closeEvent(self, event):
        if hasattr(self, 'sync_timer'):
            self.sync_timer.stop()
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Set a rounded mask for the window
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), MINI_RADIUS, MINI_RADIUS)
        region = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(region)
        # Ensure album art always fills the window
        self.album_art.setGeometry(0, 0, self.width(), self.height()) 