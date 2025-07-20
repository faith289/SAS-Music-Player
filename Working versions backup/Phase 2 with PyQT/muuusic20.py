#App Created by FAiTH aka aRkO

import sys
import os
import random
import io
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QStyledItemDelegate, QSpacerItem, 
    QListWidget, QListWidgetItem, QSlider, QHBoxLayout, QSizePolicy, QVBoxLayout,
    QFileDialog, QMenu, QGraphicsBlurEffect, QGraphicsDropShadowEffect, QSystemTrayIcon, 
    QMenu, QGraphicsOpacityEffect
)

from PyQt6.QtGui import QPixmap, QImage, QFont, QColor, QPalette, QIcon, QPainterPath, QPainter, QBrush, QPen, QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QRect, QEvent, QSize, QPropertyAnimation
import vlc
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageFilter

class ReorderablePlaylist(QListWidget):
    def __init__(self, parent=None, on_reorder_callback=None):
        super().__init__(parent)
        self.on_reorder_callback = on_reorder_callback

    def dropEvent(self, event):
        super().dropEvent(event)
        if self.on_reorder_callback:
            self.on_reorder_callback()


class FAiTHPlayer(QMainWindow):
    song_ended_signal = pyqtSignal()
    def __init__(self):
        super().__init__()
        self.setup_ui()

        self.album_original_image = None
        self.album_blurred_pixmap = None
        self.fade_animations = []  # Hold references to fade-in animations


        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("FAiTH Music Player")
        self.resize(self.minimumWidth(), self.minimumHeight())
        self.move(100, 100)  # Optional: still center or set position
        self.setMinimumSize(600, 500)
        self.setMaximumSize(2000, 1200)

        self.vlc_instance = vlc.Instance()
        self.player = self.vlc_instance.media_player_new()
        event_manager = self.player.event_manager()
        event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self.handle_song_end)
        event_manager.event_attach(vlc.EventType.MediaPlayerLengthChanged, self.on_length_known)
    

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

        self.tray_icon = QSystemTrayIcon(self)
        self.setWindowIcon(QIcon("assets/icon.ico"))  # Match tray icon path
        self.tray_icon.setIcon(QIcon("assets/icon.ico"))  # Make sure icon exists

        # Create tray menu
        tray_menu = QMenu()

        self.toggle_action = QAction("▶️ Play" if not self.player.is_playing() else "⏸ Pause")
        self.toggle_action.triggered.connect(self.toggle_play_pause)

        self.show_action = QAction("🔼 Show Player")
        self.show_action.triggered.connect(self.restore_window)

        self.exit_action = QAction("❌ Exit")
        self.exit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(self.toggle_action)
        tray_menu.addSeparator()
        tray_menu.addAction(self.show_action)
        tray_menu.addAction(self.exit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("FAiTH Music Player")
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.handle_tray_click)

        #App Created by FAiTH aka aRkO


    def setup_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        button_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """

        btn = QPushButton("New Feature")
        btn.setStyleSheet(button_style)


        # --- BACKGROUND & BLUR LAYERS ---
        self.bg_blur_label = QLabel(self.central_widget)
        self.bg_blur_label.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label.setScaledContents(True)
        self.bg_blur_label.lower()

        self.dark_overlay = QLabel(self.central_widget)
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.dark_overlay.lower()

        self.sidebar_blur_layer = QLabel(self.central_widget)
        self.sidebar_blur_layer.setGeometry(0, 0, 200, self.height())
        self.sidebar_blur_layer.setStyleSheet("""
            background-color: rgba(30, 120, 80, 90);
            border-top-left-radius: 15px;
            border-bottom-left-radius: 15px;
        """)
        self.sidebar_blur_layer.lower()

        self.playlist_glass = QLabel(self.central_widget)
        self.playlist_glass.setGeometry(0, 0, 200, self.height())
        self.playlist_glass.setStyleSheet("border-radius: 0px;")
        self.playlist_glass.lower()

        self.green_overlay = QLabel(self.central_widget)
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.green_overlay.setStyleSheet("background-color: rgba(30, 120, 80, 140);")
        self.green_overlay.lower()

        # --- SIDEBAR ---
        self.sidebar = QVBoxLayout()

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

        self.playlist_widget = ReorderablePlaylist(on_reorder_callback=self.sync_playlist_order)
        self.playlist_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self.show_playlist_context_menu)
        self.playlist_widget.setAlternatingRowColors(True)

        self.playlist_widget.setItemDelegate(PulsingDelegate(self.playlist_widget, lambda: self.current_index))
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background-color: rgba(0, 0, 0, 100);
                color: white;
                border: 1px solid rgba(255, 255, 255, 30);
                border-radius: 8px;
                padding: 5px;
                font-size: 10pt;
                font-weight: 600;
            }
            QListWidget::item {
                background-color: transparent;
            }
            QListWidget::item:alternate {
                background-color: rgba(255, 255, 255, 10);
            }
            QListWidget::item:selected {
                background-color: rgba(30, 120, 80, 180);
                color: white;
                border-radius: 4px;
            }
        """)

        self.sidebar.addWidget(button_container)
        self.sidebar.addSpacing(10)
        self.sidebar.addWidget(self.playlist_widget)

        # --- MAIN AREA ---
        self.main_layout = QVBoxLayout()

        self.green_glass = QLabel(self.central_widget)
        self.green_glass.setGeometry(200, 0, self.width() - 200, self.height())
        self.green_glass.setStyleSheet("""
            background-color: rgba(30, 120, 80, 150);
            border-radius: 25px;
        """)
        self.green_glass.lower()

        self.album_art_label = QLabel()
        self.album_art_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.album_art_label, 25, 0, 4, QColor(0, 0, 0, 160))

        self.song_label = QLabel("No song loaded")
        self.song_label.setFont(QFont("Segoe UI", 14))
        self.song_label.setStyleSheet("color: white;")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.song_label)

        self.meta_label = QLabel("")
        self.meta_label.setFont(QFont("Segoe UI", 10))
        self.meta_label.setStyleSheet("color: white;")
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.meta_label, 8, 1, 1)

        self.meta_layout = QVBoxLayout()
        self.meta_layout.setSpacing(8)
        self.meta_layout.setContentsMargins(0, 0, 0, 0)
        self.meta_layout.addWidget(self.album_art_label)
        self.meta_layout.addWidget(self.song_label)
        self.meta_layout.addWidget(self.meta_label)

        # --- SEEK BAR ---
        self.elapsed_label = QLabel("00:00")
        self.elapsed_label.setFont(QFont("Segoe UI", 9))
        self.elapsed_label.setStyleSheet("color: lightgray;")
        self.apply_shadow(self.elapsed_label, 6, 1, 1)

        self.duration_label = QLabel("00:00")
        self.duration_label.setFont(QFont("Segoe UI", 9))
        self.duration_label.setStyleSheet("color: lightgray;")
        self.apply_shadow(self.duration_label, 6, 1, 1)

        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setSingleStep(1)
        self.seek_slider.setRange(0, 1000)
        self.seek_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 10px;
                background: rgba(255, 255, 255, 0.07);
                border-radius: 5px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(30, 120, 80, 220),
                    stop:1 rgba(100, 255, 180, 200)
                );
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: white;
                border: 1px solid rgba(0, 0, 0, 0.15);
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
        """)


        self.seek_row = QHBoxLayout()
        self.seek_row.addWidget(self.elapsed_label)
        self.seek_row.addWidget(self.seek_slider)
        self.seek_row.addWidget(self.duration_label)

        # --- CONTROL BUTTONS ---
        self.controls = QHBoxLayout()
        self.controls.setContentsMargins(0, 0, 0, 0)
        self.controls.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.play_icon = QIcon("assets/play.png")
        self.pause_icon = QIcon("assets/pause.png")
        self.next_icon = QIcon("assets/next.png")
        self.prev_icon = QIcon("assets/prev.png")

        def make_button(icon):
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(button_style)
            glow = QGraphicsDropShadowEffect()
            glow.setBlurRadius(12)
            glow.setColor(QColor(0, 255, 150, 180))
            glow.setOffset(0, 2)
            btn.setGraphicsEffect(glow)
            return btn

        self.prev_btn = make_button(self.prev_icon)
        self.play_btn = make_button(self.play_icon)
        self.next_btn = make_button(self.next_icon)

        self.controls.addWidget(self.prev_btn)
        self.controls.addSpacerItem(QSpacerItem(12, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.controls.addWidget(self.play_btn)
        self.controls.addSpacerItem(QSpacerItem(12, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Minimum))
        self.controls.addWidget(self.next_btn)

        # --- VOLUME SLIDER ---
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 6px;
                background: rgba(255, 255, 255, 0.08);
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(0, 0, 0, 0.2);
                width: 14px;
                height: 14px;
                margin: -4px 0;
                border-radius: 7px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(30, 180, 100, 180),
                    stop:1 rgba(60, 255, 160, 180)
                );
                border-radius: 3px;
            }
        """)


        # --- BOTTOM CONTROLS SECTION ---
        self.bottom_controls_layout = QVBoxLayout()
        self.bottom_controls_layout.setSpacing(12)

        self.bottom_controls_layout.addLayout(self.seek_row)

        controls_holder = QWidget()
        controls_holder.setLayout(self.controls)

        controls_wrapper = QHBoxLayout()
        controls_wrapper.setContentsMargins(0, 0, 0, 0)
        controls_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        controls_wrapper.addWidget(controls_holder)

        self.bottom_controls_layout.addLayout(controls_wrapper)

        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        volume_row.addWidget(self.volume_slider)

        self.bottom_controls_layout.addLayout(volume_row)

        # --- COMBINE MAIN LAYOUTS ---
        self.main_layout.addLayout(self.meta_layout)
        self.main_layout.addSpacing(15)
        self.main_layout.addLayout(self.bottom_controls_layout)

        # --- SIDEBAR + MAIN PLAYER LAYOUT ---
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar)
        sidebar_widget.setFixedWidth(200)

        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)
        main_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.layout.addWidget(sidebar_widget, 0)
        self.layout.addWidget(main_widget, 1)

        self.central_widget.setLayout(self.layout)
        self.central_widget.raise_()

    def fade_in_widget(self, widget, duration=350):
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        # Keep reference so it's not garbage collected
        self.fade_animations.append(anim)

        def remove_anim():
            self.fade_animations.remove(anim)

        anim.finished.connect(remove_anim)
        anim.start()


    
        #App Created by FAiTH aka aRkO
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

    #def changeEvent(self, event):
        #if event.type() == QtCore.QEvent.Type.WindowStateChange:
            #if self.isMinimized():
                #QTimer.singleShot(250, self.hide)  # Hide after minimize

    def closeEvent(self, event):
        # Allow app to close normally
        event.accept()



        #App Created by FAiTH aka aRkO
    def sync_playlist_order(self):
        new_playlist = []
        for i in range(self.playlist_widget.count()):
            item_text = self.playlist_widget.item(i).text()
            for path in self.playlist:
                if os.path.basename(path) == item_text:
                    new_playlist.append(path)
                    break
        self.playlist = new_playlist


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
        # Reset icons for all items
        for i in range(self.playlist_widget.count()):
            self.playlist_widget.item(i).setIcon(QIcon())  # clear all icons

        # Set highlight and icon for the current song
        self.playlist_widget.setCurrentRow(index)
        playing_icon = QIcon("assets/play.png")  # ✅ use your own PNG
        self.playlist_widget.item(index).setIcon(playing_icon)

        # Reset formatting
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            item.setForeground(QColor("white"))
            font = item.font()
            font.setBold(False)
            item.setFont(font)

        # Highlight current
        current_item = self.playlist_widget.item(index)
        current_item.setForeground(QColor("#48fa6c"))  # Spotify green
        font = current_item.font()
        font.setBold(True)
        current_item.setFont(font)



        path = self.playlist[index]
        self.media = self.vlc_instance.media_new(path)
        self.player.set_media(self.media)

        self.display_album_art(path)
        self.display_metadata(path)

        # Animate fade-in on song change
        for widget in [self.album_art_label, self.song_label, self.meta_label]:
            self.fade_in_widget(widget)

        self.player.play()
        self.player.audio_set_volume(self.volume_slider.value())
        QTimer.singleShot(300, self.check_duration)
        self.play_btn.setIcon(self.pause_icon)

    def display_album_art(self, file_path):
        
        if self.isMinimized() or not self.isVisible():
            return

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
       
        # Convert to QImage
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # Create rounded pixmap
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.GlobalColor.transparent)

        painter = QPainter(rounded)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path = QPainterPath()
            path.addRoundedRect(0, 0, pixmap.width(), pixmap.height(), 20, 20)
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
        finally:
            painter.end()  # ✅ Always ends properly, avoiding the crash

        # Set to label
        self.album_art_label.setPixmap(rounded)



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
        if not self.playlist:  # No songs loaded
            self.load_songs()
            return

        if self.player.is_playing():
            self.player.pause()
            self.play_btn.setIcon(self.play_icon)
        else:
            self.player.play()
            self.play_btn.setIcon(self.pause_icon)






    def restore_window(self):
        self.show()
        self.setWindowState(Qt.WindowState.WindowActive)

    def handle_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.restore_window()

        #App Created by FAiTH aka aRkO

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
                current_ms = self.player.get_time()
                self.elapsed_label.setText(self.format_time(current_ms // 1000))
                duration_ms = self.player.get_length()
                self.duration_label.setText(self.format_time(duration_ms // 1000))


    


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

    def show_playlist_context_menu(self, position):
        item = self.playlist_widget.itemAt(position)
        if not item:
            return

        menu = QMenu()
        play_action = menu.addAction("▶️ Play")
        remove_action = menu.addAction("❌ Remove from Playlist")
        show_action = menu.addAction("📁 Show in Folder")

        action = menu.exec(self.playlist_widget.mapToGlobal(position))

        if action == play_action:
            self.playlist_widget.setCurrentItem(item)
            self.play_selected()
        elif action == remove_action:
            row = self.playlist_widget.row(item)
            self.playlist_widget.takeItem(row)
            if 0 <= row < len(self.playlist):
                del self.playlist[row]
        elif action == show_action:
            row = self.playlist_widget.row(item)
            if 0 <= row < len(self.playlist):
                path = self.playlist[row]
                folder = os.path.dirname(path)
                os.startfile(folder)  # Windows only


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
            self.play_btn.setIcon("assets/pause.png")
        elif self.repeat_mode == "all":
            self.play_next()
        else:
            if self.current_index + 1 < len(self.playlist):
                self.play_next()
            else:
                self.play_btn.setIcon("assets/play.png")

    def on_length_known(self, event):
        self.duration_ms = self.player.get_length()

class PulsingDelegate(QStyledItemDelegate):
    def __init__(self, parent, get_current_index_func):
        super().__init__(parent)
        self.pulse_value = 0
        self.increasing = True
        self.get_current_index = get_current_index_func

        # Timer to animate the pulse
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pulse)
        self.timer.start(60)  # update every 60 ms

    def update_pulse(self):
        if self.increasing:
            self.pulse_value += 5
            if self.pulse_value >= 100:
                self.increasing = False
        else:
            self.pulse_value -= 5
            if self.pulse_value <= 20:
                self.increasing = True
        self.parent().viewport().update()  # repaint

    def paint(self, painter, option, index):
        current_row = self.get_current_index()
        if index.row() == current_row:
            rect = option.rect
            pulse_alpha = int(100 + self.pulse_value)  # 120–200 alpha range

            # Pulsing green glow background
            glow_color = QColor(30, 200, 120, pulse_alpha)
            painter.save()
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)
            painter.restore()

        # Default painting
        super().paint(painter, option, index)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = FAiTHPlayer()
    player.show()
    sys.exit(app.exec())

    #App Created by FAiTH aka aRkO