#App Created by FAiTH aka aRkO

import sys
import os
import random
import io
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QListWidget, QSlider, QHBoxLayout, QSizePolicy, QVBoxLayout, QFileDialog,
    QGraphicsBlurEffect, QGraphicsDropShadowEffect
)
from PyQt6.QtGui import QPixmap, QImage, QFont, QColor, QPalette
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
import vlc
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageFilter


class FAiTHPlayer(QMainWindow):
    song_ended_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setup_ui()

        self.album_original_image = None
        self.album_blurred_pixmap = None
        

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("FAiTH Music Player")
        self.setGeometry(100, 100, 900, 600)
        self.setMinimumSize(600, 500)
        self.setMaximumSize(2000, 1200)

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        event_manager = self.player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_song_end)
        self.song_ended_signal.connect(self.on_song_end)

        self.media = None

        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = "off"
        self.duration_ms = 0
        self.album_art_cache = {}

        self.setup_ui()
        self.setup_events()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_seek_bar)
        self.update_timer.start(500)

    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # --- BACKGROUND BLUR & OVERLAY (unchanged) ---
        self.bg_blur_label = QLabel(self.central_widget)
        self.bg_blur_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label.setScaledContents(True)
        self.bg_blur_label.lower()

        self.dark_overlay = QLabel(self.central_widget)
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.dark_overlay.lower()

        # Extra blur background just for the sidebar (more blur than main)
        self.sidebar_blur_layer = QLabel(self.central_widget)
        self.sidebar_blur_layer.setGeometry(0, 0, 200, self.height())  # 200 = sidebar width
        self.sidebar_blur_layer.setStyleSheet("""background-color: rgba(30, 120, 80, 90);  /* lighter tint = more glass */border-top-left-radius: 15px;
        border-bottom-left-radius: 15px;""")
        self.sidebar_blur_layer.lower()  # Keep below sidebar widgets

        # --- Heavily blurred playlist background (stronger than main area) ---
        self.playlist_glass = QLabel(self.central_widget)
        self.playlist_glass.setGeometry(0, 0, 200, self.height())  # 200 = sidebar width
        self.playlist_glass.setStyleSheet("border-radius: 0px;")
        self.playlist_glass.lower()  # keep below widgets, above dark/bg blur


        # --- GREEN GLASS OVERLAY ---
        self.green_overlay = QLabel(self.central_widget)
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.green_overlay.setStyleSheet("""
            background-color: rgba(30, 120, 80, 140);  /* Frosted green */
        """)
        self.green_overlay.lower()  # Make sure it's above bg_blur but below all widgets


        # --- Sidebar Layout ---
        self.sidebar = QVBoxLayout()

        # --- Button Container ---
        self.load_btn = QPushButton("Load Songs")
        self.shuffle_btn = QPushButton("Shuffle: OFF")
        self.repeat_btn = QPushButton("Repeat: OFF")

        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 20, 10, 10)

        for btn in [self.load_btn, self.shuffle_btn, self.repeat_btn]:
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1DB954;
                    color: black;
                    font-weight: bold;
                    border-radius: 8px;
                }
                QPushButton:hover {
                    background-color: #25e06a;
                }
            """)
            button_layout.addWidget(btn)

        button_container.setLayout(button_layout)

        # --- Playlist Widget ---
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            background-color: transparent;
            color: white;
            border: none;
        """)

        # --- Add everything to the sidebar in correct order ---
        self.sidebar.addWidget(button_container)
        self.sidebar.addSpacing(10)  # gap between buttons and playlist
        self.sidebar.addWidget(self.playlist_widget)






        for btn in (self.load_btn, self.shuffle_btn, self.repeat_btn):
            btn.setStyleSheet("background-color: #1DB954; color: black; font-weight: bold;")
            self.sidebar.addWidget(btn)
        self.sidebar.addWidget(self.playlist_widget)

        # --- Main Area ---
        self.main_layout = QVBoxLayout()

        # Frosted green background for main content
        self.green_glass = QLabel(self.central_widget)
        self.green_glass.setGeometry(200, 0, self.width() - 200, self.height())
        self.green_glass.setStyleSheet("""
            background-color: rgba(30, 120, 80, 150);  /* Green tint */
            border-radius: 25px;
        """)
        self.green_glass.lower()  # Place it above bg_blur but below main content


        # Album art
        self.album_art_label = QLabel()
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 1) Song title + shadow
        self.song_label = QLabel("No song loaded")
        self.song_label.setFont(QFont("Segoe UI", 14))
        self.song_label.setStyleSheet("color: white;")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.song_label, blur_radius=12, x_offset=2, y_offset=2)

        # 2) Metadata + shadow
        self.meta_label = QLabel("")
        self.meta_label.setFont(QFont("Segoe UI", 10))
        self.meta_label.setStyleSheet("color: white;")
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.meta_label, blur_radius=8, x_offset=1, y_offset=1)

        # 3) Time label + shadow
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFont(QFont("Segoe UI", 10))
        self.time_label.setStyleSheet("color: gray;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.time_label, blur_radius=6, x_offset=1, y_offset=1)

        # Seek slider, controls, volume
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setRange(0, 1000)

        self.controls = QHBoxLayout()
        self.prev_btn = QPushButton("⏮")
        self.play_btn = QPushButton("▶")
        self.next_btn = QPushButton("⏭")
        for btn in (self.prev_btn, self.play_btn, self.next_btn):
            self.controls.addWidget(btn)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)

        # Assemble main layout
        self.main_layout.addWidget(self.album_art_label)
        self.main_layout.addWidget(self.song_label)
        self.main_layout.addWidget(self.meta_label)
        self.main_layout.addWidget(self.seek_slider)
        self.main_layout.addWidget(self.time_label)
        self.main_layout.addLayout(self.controls)
        self.main_layout.addWidget(self.volume_slider)

        # Combine sidebar + main
        self.layout = QHBoxLayout()
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar)
        sidebar_widget.setFixedWidth(200)

        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)

        self.layout.addWidget(sidebar_widget)
        self.layout.addWidget(main_widget)
        self.central_widget.setLayout(self.layout)
        self.central_widget.raise_()

   
    def setup_events(self):
        self.load_btn.clicked.connect(self.load_songs)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.repeat_btn.clicked.connect(self.toggle_repeat)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected)
        self.play_btn.clicked.connect(self.toggle_play_pause)
        self.prev_btn.clicked.connect(self.play_previous)
        self.next_btn.clicked.connect(self.play_next)
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.seek_slider.sliderReleased.connect(self.seek_song)

    def apply_shadow(self, label, blur_radius=12, x_offset=2, y_offset=2, color=QColor(0,0,0,180)):
        shadow = QGraphicsDropShadowEffect(label)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(x_offset, y_offset)
        shadow.setColor(color)
        label.setGraphicsEffect(shadow)


    def load_songs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Audio Files (*.mp3 *.wav *.flac)")
        if files:
            self.playlist = files
            self.playlist_widget.clear()
            for f in files:
                self.playlist_widget.addItem(os.path.basename(f))
            self.load_song(0)

    def load_song(self, index):
        if not (0 <= index < len(self.playlist)):
            return

        self.current_index = index
        self.playlist_widget.setCurrentRow(index)

        path = self.playlist[index]
        self.media = self.vlc_instance.media_new(path)
        self.player.set_media(self.media)

        self.display_album_art(path)
        self.display_metadata(path)

        self.player.play()
        self.player.audio_set_volume(self.volume_slider.value())
        QTimer.singleShot(300, self.check_duration)
        self.play_btn.setText("⏸")

    def display_album_art(self, file_path):
        if file_path in self.album_art_cache:
            self.set_album_art(self.album_art_cache[file_path])
            return
        try:
            audio = MP3(file_path, ID3=ID3)
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    image = Image.open(io.BytesIO(tag.data)).resize((200, 200))
                    self.album_art_cache[file_path] = image
                    self.set_album_art(image)
                    return
        except:
            pass
        self.album_art_label.setText("No Album Art")
        
        #App Created by FAiTH aka aRkO
    
    def set_album_art(self, image):
        self.album_original_image = image

        # Album art display (top center)
        data = image.convert("RGB").tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        self.album_art_label.setPixmap(pixmap)

        # Normal blur for full background
        blurred = image.resize((900, 600)).filter(ImageFilter.GaussianBlur(35))
        bg_data = blurred.convert("RGB").tobytes("raw", "RGB")
        bg_qimage = QImage(bg_data, blurred.width, blurred.height, QImage.Format.Format_RGB888)
        self.album_blurred_pixmap = QPixmap.fromImage(bg_qimage)

        self.bg_blur_label.setPixmap(self.album_blurred_pixmap.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        ))

        # Extra blur for sidebar
        extra_blur = image.resize((900, 600)).filter(ImageFilter.GaussianBlur(65))
        extra_data = extra_blur.convert("RGB").tobytes("raw", "RGB")
        extra_qimg = QImage(extra_data, extra_blur.width, extra_blur.height, QImage.Format.Format_RGB888)
        self.sidebar_extra_blurred_pixmap = QPixmap.fromImage(extra_qimg)

        self.sidebar_blur_layer.setPixmap(self.sidebar_extra_blurred_pixmap.scaled(
            200, self.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        ))


    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.playlist_glass.setGeometry(0, 0, 200, self.height())
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        self.sidebar_blur_layer.setGeometry(0, 0, 200, self.height())

        # Update scaled version of sidebar blur
        if hasattr(self, 'sidebar_extra_blurred_pixmap'):
            scaled_sidebar_blur = self.sidebar_extra_blurred_pixmap.scaled(
                200, self.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.sidebar_blur_layer.setPixmap(scaled_sidebar_blur)


        if self.album_blurred_pixmap:
            scaled = self.album_blurred_pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            self.bg_blur_label.setPixmap(scaled)


    def update_blurred_background(self):
        if isinstance(self.album_original_image, Image.Image):
            try:
                resized = self.album_original_image.resize((self.width(), self.height()))
                blurred = resized.filter(ImageFilter.GaussianBlur(35))
                bg_data = blurred.convert("RGB").tobytes("raw", "RGB")
                bg_qimage = QImage(bg_data, blurred.width, blurred.height, QImage.Format.Format_RGB888)
                bg_pixmap = QPixmap.fromImage(bg_qimage)
                self.bg_blur_label.setPixmap(bg_pixmap)
            except Exception as e:
                print("Error updating blurred background:", e)

    def display_metadata(self, file_path):
        try:
            tags = EasyID3(file_path)
            artist = tags.get('artist', ['Unknown Artist'])[0]
            album = tags.get('album', ['Unknown Album'])[0]
            title = tags.get('title', ['Unknown Title'])[0]
            text = f"{artist} — {album} — {title}"
        except:
            text = "Metadata not found"
        self.meta_label.setText(text)
        self.song_label.setText(os.path.basename(file_path))

    def toggle_play_pause(self):
        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setText("▶")
        else:
            self.player.play()
            self.play_btn.setText("⏸")

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        self.shuffle_btn.setText("Shuffle: ON" if self.shuffle else "Shuffle: OFF")

    def toggle_repeat(self):
        modes = {"off": "one", "one": "all", "all": "off"}
        self.repeat_mode = modes[self.repeat_mode]
        self.repeat_btn.setText(f"Repeat: {self.repeat_mode.upper()}") if self.repeat_mode != "off" else self.repeat_btn.setText("Repeat: OFF")

    def change_volume(self, val):
        self.player.audio_set_volume(val)
    
    #App Created by FAiTH aka aRkO
    def update_seek_bar(self):
        if self.player and self.duration_ms > 0:
            current_ms = self.player.get_time()
            if current_ms >= 0:
                progress = int((current_ms / self.duration_ms) * 1000)
                self.seek_slider.blockSignals(True)  # prevent triggering seek while updating
                self.seek_slider.setValue(progress)
                self.seek_slider.blockSignals(False)
                self.time_label.setText(f"{self.format_time(current_ms / 1000)} / {self.format_time(self.duration_ms / 1000)}")

    def seek_song(self):
        if self.duration_ms > 0:
            new_time = self.seek_slider.value() / 1000 * self.duration_ms
            self.player.set_time(int(new_time))

    def check_duration(self, retries=10):
        length = self.player.get_length()
        if length > 0:
            self.duration_ms = length
        elif retries > 0:
            QTimer.singleShot(300, lambda: self.check_duration(retries - 1))
        else:
            self.duration_ms = 0  # fallback


    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def play_selected(self):
        self.load_song(self.playlist_widget.currentRow())

    def play_next(self):
        if not self.playlist:
            return
        next_index = random.randint(0, len(self.playlist) - 1) if self.shuffle else self.current_index + 1
        if next_index >= len(self.playlist):
            next_index = 0 if self.repeat_mode == "all" else len(self.playlist) - 1
        self.load_song(next_index)

    def play_previous(self):
        if not self.playlist:
            return
        prev_index = self.current_index - 1
        if prev_index < 0:
            prev_index = len(self.playlist) - 1 if self.repeat_mode == "all" else 0
        self.load_song(prev_index)
    
    def handle_song_end(self, event):
        self.song_ended_signal.emit()  # safely notify the main thread
    
    @pyqtSlot()
    def on_song_end(self):
        if self.repeat_mode == "one":
            self.player.stop()
            media = self.vlc_instance.media_new(self.playlist[self.current_index])
            self.media = media
            self.player.set_media(media)
            self.player.play()
            self.player.audio_set_volume(self.volume_slider.value())
            QTimer.singleShot(300, self.check_duration)
            self.play_btn.setText("⏸")
        elif self.repeat_mode == "all":
            self.play_next()
        else:
            if self.current_index + 1 < len(self.playlist):
                self.play_next()
            else:
                self.play_btn.setText("▶")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = FAiTHPlayer()
    player.show()
    sys.exit(app.exec())

