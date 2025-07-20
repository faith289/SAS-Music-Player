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
    QGraphicsOpacityEffect
)

from PyQt6.QtGui import QPixmap, QLinearGradient, QImage, QFont, QFontMetrics, QColor, QPalette, QIcon, QPainterPath, QPainter, QBrush, QPen, QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QRect, QEvent, QSize, QPropertyAnimation, QEasingCurve
import vlc
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageFilter

from widgets import ScrollingLabel, GlowButton, ShadowLabel, ReorderablePlaylist, PulsingDelegate, AlbumArtWidget
from styles import (
    SIDEBAR_BG_COLOR, SIDEBAR_HOVER_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER, WHITE, BLACK,
    ICON_PLAY, ICON_PAUSE, ICON_NEXT, ICON_PREV, ICON_BRIGHTNESS, ICON_APP,
    BUTTON_STYLE_TRANSPARENT, BUTTON_STYLE_SIDEBAR, BUTTON_STYLE_SIDEBAR_ACTIVE, VOLUME_BUTTON_STYLE
)

from player_controller import PlayerController
from mini_player import MiniPlayer

# --- UI STYLES & CONSTANTS ---


if sys.platform == 'win32':
    import win32gui
    import win32con
    import win32api
    import win32com.client
    from ctypes import windll

class TaskbarProgress:
    TBPF_NOPROGRESS = 0x0
    TBPF_INDETERMINATE = 0x1
    TBPF_NORMAL = 0x2
    TBPF_ERROR = 0x4
    TBPF_PAUSED = 0x8

    def __init__(self, window):
        self.window = window
        self.hwnd = int(window.winId()) if sys.platform == 'win32' else None
        self.taskbar = None
        if sys.platform == 'win32':
            try:
                CLSID_TaskbarList = '{56FDF344-FD6D-11d0-958A-006097C9A090}'
                IID_ITaskbarList3 = '{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEA84}'
                self.taskbar = win32com.client.Dispatch(CLSID_TaskbarList)
                self.taskbar.HrInit()
            except Exception:
                self.taskbar = None

    def set_progress(self, value, maximum):
        if self.taskbar and self.hwnd:
            try:
                self.taskbar.SetProgressState(self.hwnd, self.TBPF_NORMAL)
                self.taskbar.SetProgressValue(self.hwnd, int(value), int(max(1, maximum)))
            except Exception:
                pass

    def clear(self):
        if self.taskbar and self.hwnd:
            try:
                self.taskbar.SetProgressState(self.hwnd, self.TBPF_NOPROGRESS)
            except Exception:
                pass


class FAiTHPlayer(QMainWindow):
    song_ended_signal = pyqtSignal()
    play_state_changed_signal = pyqtSignal()
    def __init__(self):
        super().__init__()

        self.album_original_image = None
        self.album_blurred_pixmap = None
        self.fade_animations = []  # Hold references to fade-in animations
        self._fade_anim = None
        self._is_fading_out = False


        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.setWindowTitle("FAiTH Music Player")
        self.resize(self.minimumWidth(), self.minimumHeight())
        self.move(100, 100)  # Optional: still center or set position
        self.setMinimumSize(600, 500)
        self.setMaximumSize(2000, 1200)

        # Use PlayerController for all playback and state
        self.controller = PlayerController()
        self.controller.song_ended_signal.connect(self.on_song_end)
        self.controller.length_known_signal.connect(self.on_length_known)

        self.album_art_cache = {}
        self.taskbar_progress = TaskbarProgress(self) if sys.platform == 'win32' else None
        self.setup_ui()
        self.setAcceptDrops(True)
        self.setup_events()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_seek_bar)
        self.update_timer.start(500)

        self.tray_icon = QSystemTrayIcon(self)
        self.setWindowIcon(QIcon(ICON_APP))  # Match tray icon path
        self.tray_icon.setIcon(QIcon(ICON_APP))  # Make sure icon exists

        # Create tray menu
        tray_menu = QMenu()

        self.toggle_action = QAction("▶️ Play" if not self.controller.is_playing() else "⏸ Pause")
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

        self._setup_background_layers()
        self._setup_sidebar()
        self._setup_main_area()
        self._setup_seek_bar()
        self._setup_control_buttons()
        self._setup_volume_controls()
        self._compose_layouts()
        self.central_widget.raise_()
        self.brightness_btn.raise_()
        self._setup_bottom_shadow()

    def _setup_background_layers(self):
        self.brightness_btn = GlowButton(self.central_widget)
        self.brightness_btn.setIcon(QIcon(ICON_BRIGHTNESS))
        self.brightness_btn.setIconSize(QSize(20, 20))
        self.brightness_btn.setFixedSize(28, 28)
        self.brightness_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        self.brightness_btn.clicked.connect(self.toggle_darkness)

        self.mini_btn = QPushButton(self.central_widget)
        self.mini_btn.setIcon(QIcon(ICON_APP))
        self.mini_btn.setIconSize(QSize(20, 20))
        self.mini_btn.setFixedSize(28, 28)
        self.mini_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 20);
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 40);
            }
        """)
        self.mini_btn.clicked.connect(self.show_mini_player)
        self.mini_btn.raise_()

        self.bg_blur_label_1 = QLabel(self.central_widget)
        self.bg_blur_label_1.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_1.setScaledContents(True)
        self.bg_blur_label_1.lower()

        self.bg_blur_label_2 = QLabel(self.central_widget)
        self.bg_blur_label_2.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_2.setScaledContents(True)
        self.bg_blur_label_2.lower()

        self.bg_blur_label_1.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.bg_blur_label_2.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.dark_overlay = QLabel(self.central_widget)
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.dark_overlay.lower()
        self.dark_overlay_opacity_effect = QGraphicsOpacityEffect(self.dark_overlay)
        self.dark_overlay.setGraphicsEffect(self.dark_overlay_opacity_effect)
        self.dark_overlay_opacity_effect.setOpacity(0.6)
        self.dark_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        self.playlist_glass = QLabel(self.central_widget)
        self.playlist_glass.setGeometry(0, 0, 200, self.height())
        self.playlist_glass.setStyleSheet("border-radius: 0px;")
        self.playlist_glass.lower()

        self.green_overlay = QLabel(self.central_widget)
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.green_overlay.setStyleSheet("background-color: rgba(30, 120, 80, 130);")
        self.green_overlay.lower()
        self.green_overlay.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def _setup_sidebar(self):
        self.sidebar = QVBoxLayout()
        self.load_btn = QPushButton("Load Songs")
        self.shuffle_btn = QPushButton("Shuffle: OFF")
        self.repeat_btn = QPushButton("Repeat: OFF")
        button_container = QWidget()
        button_layout = QVBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(10, 20, 10, 10)
        self.load_btn.setFixedHeight(40)
        self.load_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.load_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
        button_layout.addWidget(self.load_btn)
        for btn in [self.shuffle_btn, self.repeat_btn]:
            btn.setFixedHeight(40)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
            button_layout.addWidget(btn)
        button_container.setLayout(button_layout)
        self.playlist_widget = ReorderablePlaylist(on_reorder_callback=self.sync_playlist_order)
        self.playlist_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.playlist_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.playlist_widget.customContextMenuRequested.connect(self.show_playlist_context_menu)
        self.playlist_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.playlist_widget.setAlternatingRowColors(True)
        # Ensure PulsingDelegate is set with correct lambda for current index
        from widgets import PulsingDelegate
        self.playlist_widget.setItemDelegate(PulsingDelegate(self.playlist_widget, lambda: self.controller.current_index))
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

    def _setup_main_area(self):
        self.main_layout = QVBoxLayout()
        self.album_art_label = AlbumArtWidget()
        # AlbumArtWidget handles its own size and background
        # Add a soft, more visible drop shadow effect to the album art
        soft_shadow = QGraphicsDropShadowEffect(self.album_art_label)
        soft_shadow.setBlurRadius(60)
        soft_shadow.setOffset(0, 12)
        soft_shadow.setColor(QColor(0, 0, 0, 180))
        self.album_art_label.setGraphicsEffect(soft_shadow)
        self.song_label = ScrollingLabel("No song loaded")
        self.song_label.setFont(QFont("Segoe UI", 14))
        self.song_label.setStyleSheet("color: white;")
        self.song_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        shadow = QGraphicsDropShadowEffect(self.song_label)
        shadow.setBlurRadius(25)
        shadow.setOffset(3, 3)
        shadow.setColor(QColor(0, 0, 0, 220))
        self.song_label.setGraphicsEffect(shadow)
        self.meta_label = ScrollingLabel("")
        self.meta_label.setFont(QFont("Segoe UI", 10))
        self.meta_label.setStyleSheet("color: white;")
        self.meta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.apply_shadow(self.meta_label, 8, 1, 1)
        self.meta_layout = QVBoxLayout()
        self.meta_layout.setSpacing(8)
        self.meta_layout.setContentsMargins(0, 16, 0, 0)  # Add top margin for shadow
        self.meta_layout.addWidget(self.album_art_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.meta_layout.addWidget(self.song_label)
        self.meta_layout.addWidget(self.meta_label)
        self.main_layout.addLayout(self.meta_layout)
        self.main_layout.addSpacing(15)


    def _setup_seek_bar(self):
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
        self.main_layout.addLayout(self.seek_row)

    def _setup_control_buttons(self):
        self.controls = QHBoxLayout()
        self.controls.setContentsMargins(0, 0, 0, 0)
        self.controls.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.play_icon = QIcon(ICON_PLAY)
        self.pause_icon = QIcon(ICON_PAUSE)
        self.next_icon = QIcon(ICON_NEXT)
        self.prev_icon = QIcon(ICON_PREV)
        def make_button(icon):
            btn = QPushButton()
            btn.setIcon(icon)
            btn.setIconSize(QSize(24, 24))
            btn.setFixedSize(40, 40)
            btn.setStyleSheet(BUTTON_STYLE_TRANSPARENT)
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
        controls_holder = QWidget()
        controls_holder.setLayout(self.controls)
        controls_wrapper = QVBoxLayout()
        controls_wrapper.setContentsMargins(0, 0, 0, 0)
        controls_wrapper.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        controls_wrapper.addWidget(controls_holder)

        # Add volume slider with - and + buttons below the play/pause button
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(8)
        volume_row.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.vol_down_btn = QPushButton("−")
        self.vol_down_btn.setFixedSize(24, 24)
        self.vol_down_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 60);
            }
        """)
        self.vol_up_btn = QPushButton("+")
        self.vol_up_btn.setFixedSize(24, 24)
        self.vol_up_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 30);
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 60);
            }
        """)
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(120)
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
        self.volume_slider.valueChanged.connect(self.change_volume)
        self.vol_down_btn.clicked.connect(lambda: self.volume_slider.setValue(max(0, self.volume_slider.value() - 5)))
        self.vol_up_btn.clicked.connect(lambda: self.volume_slider.setValue(min(100, self.volume_slider.value() + 5)))
        volume_row.addWidget(self.vol_down_btn)
        volume_row.addWidget(self.volume_slider)
        volume_row.addWidget(self.vol_up_btn)
        controls_wrapper.addSpacing(8)
        controls_wrapper.addLayout(volume_row)

        self.main_layout.addLayout(controls_wrapper)

    def _setup_volume_controls(self):
        # Sleep timer button
        self.sleep_btn = QPushButton("💤")
        self.sleep_btn.setFixedSize(36, 36)
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,40);
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,80);
            }
        """)
        self.sleep_btn.clicked.connect(self.show_sleep_timer_menu)
        
        # Sleep timer
        self.sleep_timer = QTimer()
        self.sleep_timer.timeout.connect(self.stop_playback)
        self.sleep_timer.setSingleShot(True)
        
        # Create main row with sleep button on the far right
        volume_row = QHBoxLayout()
        volume_row.setContentsMargins(0, 0, 0, 0)
        volume_row.setSpacing(0)
        
        # Add flexible space to push sleep button to the far right
        volume_row.addStretch(1)
        
        # Add sleep button on the far right
        volume_row.addWidget(self.sleep_btn)
        
        self.main_layout.addLayout(volume_row)

    def _compose_layouts(self):
        self.main_layout_container = QHBoxLayout()
        self.main_layout_container.setContentsMargins(0, 0, 0, 0)
        self.main_layout_container.setSpacing(0)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar)
        sidebar_widget.setFixedWidth(200)
        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)
        main_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.main_layout_container.addWidget(sidebar_widget, 0)
        self.main_layout_container.addWidget(main_widget, 1)
        self.central_widget.setLayout(self.main_layout_container)

    def _setup_bottom_shadow(self):
        self.bottom_shadow = QLabel(self.central_widget)
        self.bottom_shadow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.bottom_shadow.setStyleSheet("background: transparent;")
        self.bottom_shadow.lower()




    def animate_dark_overlay(self, target_opacity, duration=350):
        if not hasattr(self, "dark_overlay_opacity_effect"):
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            self.dark_overlay_opacity_effect = QGraphicsOpacityEffect(self.dark_overlay)
            self.dark_overlay.setGraphicsEffect(self.dark_overlay_opacity_effect)

        self.dark_overlay_animation = QPropertyAnimation(self.dark_overlay_opacity_effect, b"opacity")
        self.dark_overlay_animation.setDuration(duration)
        self.dark_overlay_animation.setStartValue(self.dark_overlay_opacity_effect.opacity())
        self.dark_overlay_animation.setEndValue(target_opacity)
        self.dark_overlay_animation.start()



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

        self.seek_slider.sliderReleased.connect(self.seek_song)

    #def changeEvent(self, event):
        #if event.type() == QtCore.QEvent.Type.WindowStateChange:
            #if self.isMinimized():
                #QTimer.singleShot(250, self.hide)  # Hide after minimize

    def showEvent(self, event):
        super().showEvent(event)
        self.setWindowOpacity(0.0)
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.start()

    def closeEvent(self, event):
        if self._is_fading_out:
            event.accept()
            return
        event.ignore()
        self._is_fading_out = True
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(250)
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_anim.finished.connect(self._final_close)
        self._fade_anim.start()

    def _final_close(self):
        self._is_fading_out = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
        super().close()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)



        #App Created by FAiTH aka aRkO
    def sync_playlist_order(self):
        # Update controller playlist order based on UI
        new_playlist = []
        new_index = -1
        current_song_path = self.controller.get_current_song_path()
        for i in range(self.playlist_widget.count()):
            item_text = self.playlist_widget.item(i).text()
            for path in self.controller.playlist:
                if os.path.basename(path) == item_text:
                    new_playlist.append(path)
                    if path == current_song_path:
                        new_index = i
                    break
        self.controller.reorder_playlist(new_playlist)
        self.controller.current_index = new_index



    def apply_shadow(self, label, blur_radius=12, x_offset=2, y_offset=2, color=QColor(0,0,0,180)):
        shadow = QGraphicsDropShadowEffect(label)
        shadow.setBlurRadius(blur_radius)
        shadow.setOffset(x_offset, y_offset)
        shadow.setColor(color)
        label.setGraphicsEffect(shadow)


    def load_songs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Open Files", "", "Audio Files (*.mp3 *.wav *.flac)")
        if files:
            self.controller.set_playlist(files)
            self.playlist_widget.clear()
            for f in files:
                self.playlist_widget.addItem(os.path.basename(f))
            self.load_song(0)
            self.update_load_button_style()


    def update_load_button_style(self):
        if self.controller.playlist:
            self.load_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR_ACTIVE)
        else:
            self.load_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)


    def load_song(self, index):
        if not (0 <= index < len(self.controller.playlist)):
            return
        self.controller.current_index = index  # Ensure current_index is always set
        self.controller.play_song(index)
        # Reset icons for all items
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item is not None:
                item.setIcon(QIcon())
        self.playlist_widget.setCurrentRow(index)
        playing_icon = QIcon(ICON_PLAY)
        item = self.playlist_widget.item(index)
        if item is not None:
            item.setIcon(playing_icon)
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item is not None:
                item.setForeground(QColor("white"))
                font = item.font()
                font.setBold(False)
                item.setFont(font)
        current_item = self.playlist_widget.item(index)
        if current_item is not None:
            current_item.setForeground(QColor("#48fa6c"))
            font = current_item.font()
            font.setBold(True)
            current_item.setFont(font)
        path = self.controller.playlist[index]
        self.display_album_art(path)
        self.display_metadata(path)
        for widget in [self.album_art_label, self.song_label, self.meta_label]:
            self.fade_in_widget(widget)
        self.play_btn.setIcon(self.pause_icon)
        # Emit signal for play state change
        self.play_state_changed_signal.emit()
        # Update mini player play button icon if it exists
        if hasattr(self, 'mini_player') and self.mini_player is not None:
            self.mini_player.update_play_button_icon()
        # Force repaint for pulsing effect
        viewport = self.playlist_widget.viewport()
        if viewport is not None:
            viewport.update()

    def display_album_art(self, file_path):
        # Always update mini player if it exists
        mini_player_pixmap = None
        if file_path in self.album_art_cache:
            self.set_album_art(self.album_art_cache[file_path])
            # set_album_art already updates mini player
            return
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is not None:
                for tag in audio.tags.values():
                    if isinstance(tag, APIC):
                        data = getattr(tag, 'data', None)
                        if data is not None:
                            image = Image.open(io.BytesIO(data)).resize((200, 200))
                            self.album_art_cache[file_path] = image
                            self.set_album_art(image)
                            # set_album_art already updates mini player
                            return
        except Exception as e:
            print(f"[Album Art Error] {e}")
            pass
        # No album art: set dark grey pixmap
        dark_pixmap = QPixmap(220, 220)
        dark_pixmap.fill(QColor(30, 30, 30))
        self.album_art_label.setPixmap(dark_pixmap)
        if hasattr(self, 'mini_player') and self.mini_player is not None:
            self.mini_player.set_album_art(dark_pixmap)

    def set_album_art(self, image):
        self.album_original_image = image
        data = image.convert("RGB").tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
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
            painter.end()
        padded = QPixmap(220, 220)
        padded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(padded)
        try:
            x = (220 - rounded.width()) // 2
            y = (220 - rounded.height()) // 2
            painter.drawPixmap(x, y, rounded)
        finally:
            painter.end()
        self.album_art_label.setPixmap(padded)
        if hasattr(self, 'mini_player') and self.mini_player is not None:
            self.mini_player.set_album_art(padded)



        # Normal blur for full background
        blurred = image.resize((900, 600)).filter(ImageFilter.GaussianBlur(15))
        bg_data = blurred.convert("RGB").tobytes("raw", "RGB")
        bg_qimage = QImage(bg_data, blurred.width, blurred.height, QImage.Format.Format_RGB888)
        bg_pixmap = QPixmap.fromImage(bg_qimage)

        # Scale the pixmap to fit the window
        scaled_pixmap = bg_pixmap.scaled(
            self.width(), self.height(),
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation
        )

        # Set the new image on the second label (top layer)
        self.bg_blur_label_2.setPixmap(scaled_pixmap)
        self.bg_blur_label_2.lower()  # Keep it behind all widgets
        self.bg_blur_label_1.lower()


        # Apply fade effect
        effect = QGraphicsOpacityEffect()
        self.bg_blur_label_2.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(350)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)

        def finish_transition():
            # Copy new image to base label
            self.bg_blur_label_1.setPixmap(scaled_pixmap)
            self.bg_blur_label_2.clear()
            self.bg_blur_label_2.setGraphicsEffect(None)
            self.bg_blur_label_2.lower()  # send back under everything

        anim.finished.connect(finish_transition)
        anim.start()
        self.fade_animations.append(anim)



        # Extra blur for sidebar
        #extra_blur = image.resize((900, 600)).filter(ImageFilter.GaussianBlur(65))
        #extra_data = extra_blur.convert("RGB").tobytes("raw", "RGB")
        #extra_qimg = QImage(extra_data, extra_blur.width, extra_blur.height, QImage.Format.Format_RGB888)
        #self.sidebar_extra_blurred_pixmap = QPixmap.fromImage(extra_qimg)

        #self.sidebar_blur_layer.setPixmap(self.sidebar_extra_blurred_pixmap.scaled(
            #200, self.height(),
            #Qt.AspectRatioMode.KeepAspectRatioByExpanding,
           # Qt.TransformationMode.SmoothTransformation
        #))


    
    def resizeEvent(self, event):
        super().resizeEvent(event)

        self.playlist_glass.setGeometry(0, 0, 200, self.height())
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_1.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_2.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())
        self.brightness_btn.move(self.width() - 50, 10)
        self.mini_btn.move(self.width() - 50, 44)
        self.mini_btn.raise_()
        #self.sidebar_blur_layer.setGeometry(0, 0, 200, self.height())

        # Update scaled version of sidebar blur
        #if hasattr(self, 'sidebar_extra_blurred_pixmap'):
            #scaled_sidebar_blur = self.sidebar_extra_blurred_pixmap.scaled(
                #200, self.height(),
                #Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                #Qt.TransformationMode.SmoothTransformation
            #)
            #self.sidebar_blur_layer.setPixmap(scaled_sidebar_blur)


        if self.album_blurred_pixmap:
            scaled = self.album_blurred_pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
        self.update_bottom_shadow()


    def update_bottom_shadow(self):
        width = self.width()
        height = 250

        # Inverted gradient: start at (0,height) → end at (0,0)
        gradient = QLinearGradient(0, height, 0, 0)
        gradient.setColorAt(0, QColor(0, 0, 0, 255))  # dark opaque at bottom
        gradient.setColorAt(1, QColor(0, 0, 0,   0))  # fully transparent at top

        # Create a pixmap matching window width
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        painter.end()

        # Apply and pin to bottom
        self.bottom_shadow.setPixmap(pixmap)
        self.bottom_shadow.setGeometry(0, self.height() - height, width, height)






            


    def update_blurred_background(self):
        if isinstance(self.album_original_image, Image.Image):
            try:
                resized = self.album_original_image.resize((self.width(), self.height()))
                blurred = resized.filter(ImageFilter.GaussianBlur(35))
                bg_data = blurred.convert("RGB").tobytes("raw", "RGB")
                bg_qimage = QImage(bg_data, blurred.width, blurred.height, QImage.Format.Format_RGB888)
                bg_pixmap = QPixmap.fromImage(bg_qimage)
                self.bg_blur_label_1.setPixmap(bg_pixmap)
            except Exception as e:
                print("Error updating blurred background:", e)

    def display_metadata(self, file_path):
        try:
            tags = EasyID3(file_path)
            artist = tags.get('artist', ['Unknown Artist'])
            album = tags.get('album', ['Unknown Album'])
            title = tags.get('title', ['Unknown Title'])
            artist = artist[0] if artist else 'Unknown Artist'
            album = album[0] if album else 'Unknown Album'
            title = title[0] if title else 'Unknown Title'
            text = f"{artist} — {album} — {title}"
        except Exception as e:
            print(f"[Metadata Error] {e}")
            text = "Metadata not found"
        self.meta_label.setText(text)
        self.song_label.setText(os.path.basename(file_path))

    def toggle_play_pause(self):
        if not self.controller.playlist:
            self.load_songs()
            return
        if self.controller.is_playing():
            self.controller.pause()
            self.play_btn.setIcon(self.play_icon)
        else:
            self.controller.play()
            self.play_btn.setIcon(self.pause_icon)
        # Emit signal for play state change
        self.play_state_changed_signal.emit()
        # Update mini player play button icon if it exists
        if hasattr(self, 'mini_player') and self.mini_player is not None:
            self.mini_player.update_play_button_icon()

    def toggle_darkness(self):
        # Toggle between 150 and 0
        effect = self.dark_overlay.graphicsEffect()
        current_opacity = effect.opacity() if isinstance(effect, QGraphicsOpacityEffect) else 1.0
        new_opacity = 0.0 if current_opacity > 0.5 else 0.6  # 0.6 ~ 150 alpha
        self.animate_dark_overlay(new_opacity)

    def restore_window(self):
        self.show()
        self.setWindowState(Qt.WindowState.WindowActive)

    def handle_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.restore_window()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith((".mp3", ".flac", ".wav")):
                self.controller.playlist.append(file_path)
                self.playlist_widget.addItem(os.path.basename(file_path))
        if self.controller.current_index == -1 and self.controller.playlist:
            self.load_song(0)
        self.update_load_button_style()


        #App Created by FAiTH aka aRkO
    

    def toggle_shuffle(self):
        new_shuffle = not self.controller.shuffle
        self.controller.set_shuffle(new_shuffle)
        if self.controller.shuffle:
            self.shuffle_btn.setText("Shuffle: ON")
            self.shuffle_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR_ACTIVE)
        else:
            self.shuffle_btn.setText("Shuffle: OFF")
            self.shuffle_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)


    def toggle_repeat(self):
        modes = {"off": "one", "one": "all", "all": "off"}
        new_mode = modes[self.controller.repeat_mode]
        self.controller.set_repeat_mode(new_mode)
        if self.controller.repeat_mode == "off":
            self.repeat_btn.setText("Repeat: OFF")
            self.repeat_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
        else:
            self.repeat_btn.setText(f"Repeat: {self.controller.repeat_mode.upper()}")
            self.repeat_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR_ACTIVE)


    def change_volume(self, val):
        self.controller.set_volume(val)
    
    #App Created by FAiTH aka aRkO
    def update_seek_bar(self):
        if self.controller.player and self.controller.duration_ms > 0:
            current_ms = self.controller.get_time()
            if current_ms >= 0:
                progress = int((current_ms / self.controller.duration_ms) * 1000)
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(progress)
                self.seek_slider.blockSignals(False)
                self.elapsed_label.setText(self.format_time(current_ms // 1000))
                duration_ms = self.controller.get_length()
                self.duration_label.setText(self.format_time(duration_ms // 1000))
        if self.controller.is_playing() and self.controller.current_index != -1:
            pos = self.controller.get_time()
            dur = self.controller.duration_ms
            if self.taskbar_progress:
                self.taskbar_progress.set_progress(pos, dur)
        else:
            if self.taskbar_progress:
                self.taskbar_progress.clear()


    


    def seek_song(self):
        if self.controller.duration_ms > 0:
            new_time = self.seek_slider.value() / 1000 * self.controller.duration_ms
            self.controller.seek(self.seek_slider.value())

    def check_duration(self, retries=10):
        length = self.controller.get_length()
        if length > 0:
            self.controller.duration_ms = length
        elif retries > 0:
            QTimer.singleShot(300, lambda: self.check_duration(retries - 1))
        else:
            self.controller.duration_ms = 0  # fallback


    def format_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        return f"{m:02}:{s:02}"

    def play_selected(self):
        self.load_song(self.playlist_widget.currentRow())

    def show_playlist_context_menu(self, position):
        clicked_item = self.playlist_widget.itemAt(position)
        if not clicked_item:
            return
        selected_items = self.playlist_widget.selectedItems()
        if clicked_item not in selected_items:
            self.playlist_widget.setCurrentItem(clicked_item)
            selected_items = [clicked_item]
        menu = QMenu()
        play_action = menu.addAction("▶️ Play")
        remove_action = menu.addAction("❌ Remove from Playlist")
        show_action = menu.addAction("📁 Show in Folder")
        action = menu.exec(self.playlist_widget.mapToGlobal(position))
        if action == play_action:
            self.play_selected()
        elif action == remove_action:
            rows_to_delete = [self.playlist_widget.row(item) for item in selected_items]
            if self.controller.current_index in rows_to_delete:
                self.controller.stop()
                self.album_art_label.clear()
                self.song_label.setText("No song loaded")
                self.meta_label.setText("")
                self.play_btn.setIcon(self.play_icon)
                # Emit signal for play state change
                self.play_state_changed_signal.emit()
                # Update mini player play button icon if it exists
                if hasattr(self, 'mini_player') and self.mini_player is not None:
                    self.mini_player.update_play_button_icon()
                self.controller.current_index = -1
            for row in sorted(rows_to_delete, reverse=True):
                self.playlist_widget.takeItem(row)
                if 0 <= row < len(self.controller.playlist):
                    del self.controller.playlist[row]
            if not self.controller.playlist:
                self.controller.current_index = -1
                self.update_load_button_style()
        elif action == show_action and clicked_item:
            row = self.playlist_widget.row(clicked_item)
            if 0 <= row < len(self.controller.playlist):
                folder = os.path.dirname(self.controller.playlist[row])
                if hasattr(os, 'startfile'):
                    os.startfile(folder)




    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.playlist_widget.selectedItems()
            selected_rows = [self.playlist_widget.row(item) for item in selected_items]
            if self.controller.current_index in selected_rows:
                self.controller.stop()
                self.album_art_label.clear()
                self.song_label.setText("No song loaded")
                self.meta_label.setText("")
                self.play_btn.setIcon(self.play_icon)
                # Emit signal for play state change
                self.play_state_changed_signal.emit()
                # Update mini player play button icon if it exists
                if hasattr(self, 'mini_player') and self.mini_player is not None:
                    self.mini_player.update_play_button_icon()
                self.controller.current_index = -1
            for row in sorted(selected_rows, reverse=True):
                self.playlist_widget.takeItem(row)
                if 0 <= row < len(self.controller.playlist):
                    del self.controller.playlist[row]
            if not self.controller.playlist:
                self.controller.current_index = -1
                self.update_load_button_style()





    def play_next(self):
        self.controller.play_next()
        self.load_song(self.controller.current_index)

    def play_previous(self):
        self.controller.play_previous()
        self.load_song(self.controller.current_index)
    
    def handle_song_end(self, event):
        self.song_ended_signal.emit()
    
    @pyqtSlot()
    def on_song_end(self):
        if self.controller.repeat_mode == "one":
            self.controller.stop()
            self.controller.play_song(self.controller.current_index)
            self.play_btn.setIcon(QIcon(ICON_PAUSE))
            # Emit signal for play state change
            self.play_state_changed_signal.emit()
            # Update mini player play button icon if it exists
            if hasattr(self, 'mini_player') and self.mini_player is not None:
                self.mini_player.update_play_button_icon()
        elif self.controller.repeat_mode == "all":
            self.play_next()
        else:
            if self.controller.current_index + 1 < len(self.controller.playlist):
                self.play_next()
            else:
                self.play_btn.setIcon(QIcon(ICON_PLAY))
                # Emit signal for play state change
                self.play_state_changed_signal.emit()
                # Update mini player play button icon if it exists
                if hasattr(self, 'mini_player') and self.mini_player is not None:
                    self.mini_player.update_play_button_icon()
        if self.taskbar_progress:
            self.taskbar_progress.clear()

    def on_length_known(self, event):
        self.controller.duration_ms = self.controller.get_length()

    def show_mini_player(self):
        self.hide()
        if not hasattr(self, 'mini_player'):
            from mini_player import MiniPlayer
            self.mini_player = MiniPlayer(self)
        self.mini_player.show()

    def show_sleep_timer_menu(self):
        """Show sleep timer menu with 10, 20, 30 minute options"""
        from PyQt6.QtWidgets import QMenu
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: rgba(40, 40, 40, 200);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        # Check if timer is active
        if self.sleep_timer.isActive():
            remaining_time = self.sleep_timer.remainingTime() // 60000  # Convert to minutes
            cancel_action = menu.addAction(f"Cancel Timer ({remaining_time} min)")
            cancel_action.triggered.connect(self.cancel_sleep_timer)
            menu.addSeparator()
        
        # Add timer options
        action_10 = menu.addAction("10 minutes")
        action_20 = menu.addAction("20 minutes")
        action_30 = menu.addAction("30 minutes")
        
        action_10.triggered.connect(lambda: self.start_sleep_timer(10))
        action_20.triggered.connect(lambda: self.start_sleep_timer(20))
        action_30.triggered.connect(lambda: self.start_sleep_timer(30))
        
        # Show menu at button position
        button_pos = self.sleep_btn.mapToGlobal(self.sleep_btn.rect().bottomLeft())
        menu.exec(button_pos)

    def start_sleep_timer(self, minutes):
        """Start sleep timer for specified minutes"""
        milliseconds = minutes * 60 * 1000
        self.sleep_timer.start(milliseconds)
        self.sleep_btn.setText(f"{minutes}")
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,40);
                border: none;
                border-radius: 8px;
                color: rgba(255,255,255,0.7);
                font-size: 14px;
                font-weight: normal;
            }
            QPushButton:hover {
                background: rgba(0,0,0,80);
            }
        """)

    def cancel_sleep_timer(self):
        """Cancel the active sleep timer"""
        self.sleep_timer.stop()
        self.sleep_btn.setText("💤")
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background: rgba(0,0,0,40);
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background: rgba(0,0,0,80);
            }
        """)

    def stop_playback(self):
        """Stop playback when sleep timer expires"""
        self.controller.pause()
        self.cancel_sleep_timer()
        # Update play button icon
        self.play_btn.setIcon(QIcon(self.play_icon))
        self.play_state_changed_signal.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = FAiTHPlayer()
    player.show()
    sys.exit(app.exec())

    #App Created by FAiTH aka aRkO