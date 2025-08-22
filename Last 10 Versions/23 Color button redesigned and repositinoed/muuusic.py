#App Created by FAiTH 

import os
import sys
if getattr(sys, 'frozen', False):
    os.environ['VLC_PLUGIN_PATH'] = os.path.join(sys._MEIPASS, 'plugins')
import random
import io
from PyQt6 import QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QStyledItemDelegate, QSpacerItem, 
    QListWidget, QListWidgetItem, QSlider, QHBoxLayout, QSizePolicy, QVBoxLayout,
    QFileDialog, QMenu, QGraphicsBlurEffect, QGraphicsDropShadowEffect, QSystemTrayIcon, 
    QGraphicsOpacityEffect, QDialog, QVBoxLayout, QLabel, QSlider, QGridLayout, QPushButton, QHBoxLayout
)

from PyQt6.QtGui import QPixmap, QLinearGradient, QImage, QFont, QFontMetrics, QColor, QPalette, QIcon, QPainterPath, QPainter, QBrush, QPen, QAction
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot, QRect, QEvent, QSize, QPropertyAnimation, QEasingCurve, QTimer, pyqtProperty
import vlc
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from mutagen.easyid3 import EasyID3
from PIL import Image, ImageFilter
from widgets import ScrollingLabel, GlowButton, ShadowLabel, ReorderablePlaylist, PulsingDelegate, AlbumArtWidget
from styles import (
    SIDEBAR_BG_COLOR, SIDEBAR_HOVER_COLOR, SPOTIFY_GREEN, SPOTIFY_GREEN_HOVER, WHITE, BLACK,
    ICON_PLAY, ICON_PAUSE, ICON_NEXT, ICON_PREV, ICON_BRIGHTNESS, ICON_APP,
    BUTTON_STYLE_TRANSPARENT, BUTTON_STYLE_SIDEBAR, BUTTON_STYLE_SIDEBAR_ACTIVE, VOLUME_BUTTON_STYLE,
    get_button_style_sidebar_active, get_seek_slider_style, get_volume_slider_style
)
from color_settings import ColorSettings, ColorSettingsDialog
from audio_controller import AudioController
from mini_player import MiniPlayer

# Add this import at the top with other imports
from utils import format_time, is_audio_file, calculate_brightness, get_safe_basename, create_color_variants
from audio_controller import AudioController

from ui_builder import UIBuilder
from color_dialog_manager import ColorDialogManager
from visual_effects_manager import VisualEffectsManager
from sleep_timer_dialog import SleepTimerDialog
from album_art_manager import AlbumArtManager





# --- UI STYLES & CONSTANTS ---

def resource_path(relative_path):
    # Get absolute path to resource, works for dev and for PyInstaller .exe
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath('.'), relative_path)


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


class SASPlayer(QMainWindow):
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

        self.setWindowTitle("SAS Music Player")
        self.resize(self.minimumWidth(), self.minimumHeight())
        self.move(100, 100)  # Optional: still center or set position
        self.setMinimumSize(600, 500)
        self.setMaximumSize(2000, 1200)

        # NEW CODE:
        self.controller = AudioController()
        self.controller.track_ended.connect(self.on_song_end)
        self.controller.length_changed.connect(self.on_length_known)

        # Add playlist management directly to main class
        self.playlist = []
        self.current_index = -1
        self.shuffle = False
        self.repeat_mode = "off"

        # Initialize color settings
        self.color_settings = ColorSettings()

        # Initialize color dialog manager
        self.color_dialog_manager = ColorDialogManager(self)

        # Initialize visual effects manager
        self.visual_effects = VisualEffectsManager(self)

        # Initialize album art manager
        self.album_art_manager = AlbumArtManager(self)


        # Create and set central widget FIRST (ADD THESE LINES)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        self.album_art_manager.album_art_cache = {}
        self.taskbar_progress = TaskbarProgress(self) if sys.platform == 'win32' else None
        self.setup_ui()
        self.setAcceptDrops(True)
        self.setup_events()
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_seek_bar)
        self.update_timer.start(500)
        self.sleep_update_timer = QTimer()
        self.sleep_update_timer.timeout.connect(self.update_sleep_button_display)
        self.sleep_update_timer.start(1000)

        self.tray_icon = QSystemTrayIcon(self)
        self.setWindowIcon(QIcon(resource_path(ICON_APP)))  # Match tray icon path
        self.tray_icon.setIcon(QIcon(resource_path(ICON_APP)))  # Make sure icon exists

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
        self.tray_icon.setToolTip("SAS Music Player")
        self.tray_icon.show()

        self.tray_icon.activated.connect(self.handle_tray_click)

        #App Created by FAiTH in collaboration with LazyCr0w and subhaNAG2001


    def setup_ui(self):
        """Main UI setup using UIBuilder"""
        self.ui_builder = UIBuilder(self)
        self.ui_builder.setup_ui()
        # Remove conflicting central widget code - UIBuilder handles this
        self.ensure_proper_layer_order()

  

    def animate_dark_overlay(self, target_opacity, duration=350):
        """Animate dark overlay using VisualEffectsManager"""
        self.visual_effects.animate_dark_overlay(target_opacity, duration)

    def fade_in_widget(self, widget, duration=350):
        """Fade in widget using VisualEffectsManager"""
        self.visual_effects.fade_in_widget(widget, duration)

    def fade_in_dialog(self, dialog, duration=300):
        """Fade in dialog using VisualEffectsManager"""
        self.visual_effects.fade_in_dialog(dialog, duration)

    def fade_out_dialog(self, dialog, duration=250):
        """Fade out dialog using VisualEffectsManager"""
        self.visual_effects.fade_out_dialog(dialog, duration)


    
        #App Created by FAiTH in collaboration with LazyCr0w and subhaNAG2001
    def setup_events(self):
        self.load_btn.clicked.connect(self.load_songs)
        self.shuffle_btn.clicked.connect(self.toggle_shuffle)
        self.repeat_btn.clicked.connect(self.toggle_repeat)
        self.color_btn.clicked.connect(self.show_color_settings)
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
        """Final cleanup before closing"""
        # Cleanup audio controller
        try:
            if hasattr(self, 'controller'):
                self.controller.cleanup()
        except Exception as e:
            print(f"Final cleanup error (non-fatal): {e}")
            
        self._is_fading_out = False
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
            self.tray_icon.deleteLater()
        super().close()
        app = QApplication.instance()
        if app is not None:
            QTimer.singleShot(0, app.quit)



        #App Created by FAiTH in collaboration with LazyCr0w and subhaNAG2001
    def sync_playlist_order(self):
        # Update playlist order based on UI
        new_playlist = []
        new_index = -1
        
        # Fix 1: Get current song path from main class instead of controller
        current_song_path = None
        if 0 <= self.current_index < len(self.playlist):
            current_song_path = self.playlist[self.current_index]
        
        for i in range(self.playlist_widget.count()):
            item_text = self.playlist_widget.item(i).text()
            for path in self.playlist:
                if os.path.basename(path) == item_text:
                    new_playlist.append(path)
                    if path == current_song_path:
                        new_index = i
                    break
        
        # Fix 2: Update playlist in main class instead of controller
        self.playlist = new_playlist
        self.current_index = new_index



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
                self.playlist_widget.addItem(get_safe_basename(f))
            self.load_song(0)
            self.update_load_button_style()


    def update_load_button_style(self):
        if self.playlist:
            self.load_btn.setStyleSheet(get_button_style_sidebar_active(
                self.color_settings.get_primary_green().name(),
                self.color_settings.get_hover_green().name()
            ))
        else:
            self.load_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)


    def load_song(self, index):
        if not (0 <= index < len(self.playlist)):
            return
        self.current_index = index  # Ensure current_index is always set
        file_path = self.playlist[index]
        if self.controller.load_file(file_path):
            self.controller.play()
        # Reset icons for all items
        for i in range(self.playlist_widget.count()):
            item = self.playlist_widget.item(i)
            if item is not None:
                item.setIcon(QIcon())
        self.playlist_widget.setCurrentRow(index)
        playing_icon = QIcon(resource_path(ICON_PLAY))
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
            # Use accent color for current playing item
            accent_color = self.color_settings.get_accent_green()
            current_item.setForeground(accent_color)
            font = current_item.font()
            font.setBold(True)
            current_item.setFont(font)
        path = self.playlist[index]
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
        """Display album art using AlbumArtManager"""
        self.album_art_manager.display_album_art(file_path)


    def set_album_art(self, image):
        """Set album art using AlbumArtManager"""
        self.album_art_manager.set_album_art(image)

    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.playlist_glass.setGeometry(0, 0, 200, self.height())
        self.green_overlay.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_1.setGeometry(0, 0, self.width(), self.height())
        self.bg_blur_label_2.setGeometry(0, 0, self.width(), self.height())
        self.dark_overlay.setGeometry(0, 0, self.width(), self.height())

        # Move brightness button to far top right, very close to border
        margin = 4
        self.brightness_btn.move(self.width() - self.brightness_btn.width() - margin, margin)
        
        # Reposition color button below brightness button after resize
        if hasattr(self, 'ui_builder'):
            # Use QTimer to delay positioning until after resize is complete
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self.ui_builder.position_color_below_brightness)

        # Update blurred background for new window size
        if hasattr(self, 'album_blurred_pixmap') and self.album_blurred_pixmap:
            scaled = self.album_blurred_pixmap.scaled(
                self.width(), self.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )
            # Update both background labels
            self.bg_blur_label_1.setPixmap(scaled)
            self.bg_blur_label_2.setPixmap(scaled)

        self.update_bottom_shadow()
        
        # CRITICAL: Maintain proper layer order and brightness button functionality
        self.ensure_proper_layer_order()

    def update_bottom_shadow(self):
        width = self.width()
        height = 250
        
        # Get current primary color for a subtle tint in the shadow
        primary_color = self.color_settings.get_primary_green()
        
        # Create gradient with slight color tint
        gradient = QLinearGradient(0, height, 0, 0)
        
        # Mix black with a hint of the primary color
        shadow_color = QColor(
            min(255, primary_color.red() // 4),
            min(255, primary_color.green() // 4), 
            min(255, primary_color.blue() // 4),
            255
        )
        
        gradient.setColorAt(0, shadow_color)  # tinted shadow at bottom
        gradient.setColorAt(1, QColor(0, 0, 0, 0))  # fully transparent at top
        
        # Create and apply the pixmap
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(0, 0, width, height, QBrush(gradient))
        painter.end()
        
        # Apply and pin to bottom
        self.bottom_shadow.setPixmap(pixmap)
        self.bottom_shadow.setGeometry(0, self.height() - height, width, height)
        
        # Force immediate update
        self.bottom_shadow.update()
        self.bottom_shadow.repaint()


    def update_blurred_background(self):
        """Update blurred background using VisualEffectsManager"""
        self.visual_effects.update_blurred_background()

    def update_blurred_background_smooth(self):
        """Update blurred background smooth using VisualEffectsManager"""
        self.visual_effects.update_blurred_background_smooth()

    def create_background_fade_in(self, target_label, previous_label):
        """Create background fade in using VisualEffectsManager"""
        self.visual_effects.create_background_fade_in(target_label, previous_label)

    def ensure_proper_layer_order(self):
        """Ensure proper layer order using VisualEffectsManager"""
        self.visual_effects.ensure_proper_layer_order()

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
        self.song_label.setText(get_safe_basename(file_path))

    def toggle_play_pause(self):
        if not self.playlist:
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
            if is_audio_file(file_path):
                self.playlist.append(file_path)
                self.playlist_widget.addItem(get_safe_basename(file_path))
        if self.current_index == -1 and self.playlist:
            self.load_song(0)
        self.update_load_button_style()


        #App Created by FAiTH in collaboration with LazyCr0w and subhaNAG2001
    

    def toggle_shuffle(self):
        new_shuffle = not self.shuffle
        self.shuffle = new_shuffle
        if self.shuffle:
            self.shuffle_btn.setText("Shuffle: ON")
            self.shuffle_btn.setStyleSheet(get_button_style_sidebar_active(
                self.color_settings.get_primary_green().name(),
                self.color_settings.get_hover_green().name()
            ))
        else:
            self.shuffle_btn.setText("Shuffle: OFF")
            self.shuffle_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)


    def toggle_repeat(self):
        modes = {"off": "one", "one": "all", "all": "off"}
        new_mode = modes[self.repeat_mode]
        self.repeat_mode = new_mode
        if self.repeat_mode == "off":
            self.repeat_btn.setText("Repeat: OFF")
            self.repeat_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
        else:
            self.repeat_btn.setText(f"Repeat: {self.repeat_mode.upper()}")
            self.repeat_btn.setStyleSheet(get_button_style_sidebar_active(
                self.color_settings.get_primary_green().name(),
                self.color_settings.get_hover_green().name()
            ))


    def change_volume(self, val):
        self.controller.set_volume(val)
    
    #App Created by FAiTH in collaboration with LazyCr0w and subhaNAG2001
    def update_seek_bar(self):
        # Fix 1: Replace duration_ms with get_length()
        if self.controller.player and self.controller.get_length() > 0:
            current_ms = self.controller.get_position()
            if current_ms >= 0:
                # Fix 2: Use get_length() instead of duration_ms
                duration_ms = self.controller.get_length()
                progress = int((current_ms / duration_ms) * 1000)
                self.seek_slider.blockSignals(True)
                self.seek_slider.setValue(progress)
                self.seek_slider.blockSignals(False)
                # Keep your NEW CODE as is - it's correct
                self.elapsed_label.setText(format_time(current_ms // 1000))
                self.duration_label.setText(format_time(duration_ms // 1000))

        if self.controller.is_playing() and self.current_index != -1:
            pos = self.controller.get_position()
            # Fix 3: Replace duration_ms with get_length()
            dur = self.controller.get_length()
            if self.taskbar_progress:
                self.taskbar_progress.set_progress(pos, dur)
        else:
            if self.taskbar_progress:
                self.taskbar_progress.clear()

    


    def seek_song(self):
        if self.controller.get_length() > 0:
            duration_ms = self.controller.get_length()
            new_time = self.seek_slider.value() / 1000 * duration_ms
            position_ms = int((self.seek_slider.value() / 1000) * self.controller.get_length())
            self.controller.set_position(position_ms)

    def check_duration(self, retries=10):
        length = self.controller.get_length()
        if length > 0:
            # Duration is handled internally by AudioController - no assignment needed
            pass
        elif retries > 0:
            QTimer.singleShot(300, lambda: self.check_duration(retries - 1))
        else:
            # Duration is handled internally by AudioController - no assignment needed  
            pass  # fallback


    #def format_time(self, seconds):
        #m, s = divmod(int(seconds), 60)
       # return f"{m:02}:{s:02}"

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
            if self.current_index in rows_to_delete:
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
                self.current_index = -1
            for row in sorted(rows_to_delete, reverse=True):
                self.playlist_widget.takeItem(row)
                if 0 <= row < len(self.playlist):
                    del self.playlist[row]
            if not self.playlist:
                self.current_index = -1
                self.update_load_button_style()
        elif action == show_action and clicked_item:
            row = self.playlist_widget.row(clicked_item)
            if 0 <= row < len(self.playlist):
                folder = os.path.dirname(self.playlist[row])
                if hasattr(os, 'startfile'):
                    os.startfile(folder)




    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Delete:
            selected_items = self.playlist_widget.selectedItems()
            selected_rows = [self.playlist_widget.row(item) for item in selected_items]
            if self.current_index in selected_rows:
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
                self.current_index = -1
            for row in sorted(selected_rows, reverse=True):
                self.playlist_widget.takeItem(row)
                if 0 <= row < len(self.playlist):
                    del self.playlist[row]
            if not self.playlist:
                self.current_index = -1
                self.update_load_button_style()

    
    def closeEvent(self, event):
        """Handle application close event with proper cleanup"""
        if self._is_fading_out:
            # Cleanup audio controller first
            try:
                if hasattr(self, 'controller'):
                    self.controller.cleanup()
                
                # Stop any active timers
                if hasattr(self, 'sleep_timer'):
                    self.sleep_timer.stop()
                if hasattr(self, 'update_timer'):
                    self.update_timer.stop()
                    
            except Exception as e:
                print(f"Cleanup error (non-fatal): {e}")
            
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





    def play_next(self):
        if self.playlist:
            if self.shuffle:
                self.current_index = random.randint(0, len(self.playlist) - 1)
            else:
                self.current_index = (self.current_index + 1) % len(self.playlist)
            self.load_song(self.current_index)

    def play_previous(self):
        if self.playlist:
            if self.shuffle:
                self.current_index = random.randint(0, len(self.playlist) - 1)
            else:
                self.current_index = (self.current_index - 1) % len(self.playlist)
            self.load_song(self.current_index)

    
    def handle_song_end(self, event):
        self.song_ended_signal.emit()
    
    @pyqtSlot()
    def on_song_end(self):
        if self.repeat_mode == "one":
            self.controller.stop()
            self.load_song(self.current_index)
            self.play_btn.setIcon(QIcon(resource_path(ICON_PAUSE)))
            # Emit signal for play state change
            self.play_state_changed_signal.emit()
            # Update mini player play button icon if it exists
            if hasattr(self, 'mini_player') and self.mini_player is not None:
                self.mini_player.update_play_button_icon()
        elif self.repeat_mode == "all":
            self.play_next()
        else:
            if self.current_index + 1 < len(self.playlist):
                self.play_next()
            else:
                self.play_btn.setIcon(QIcon(resource_path(ICON_PLAY)))
                # Emit signal for play state change
                self.play_state_changed_signal.emit()
                # Update mini player play button icon if it exists
                if hasattr(self, 'mini_player') and self.mini_player is not None:
                    self.mini_player.update_play_button_icon()
        if self.taskbar_progress:
            self.taskbar_progress.clear()

    def on_length_known(self, event):
        # AudioController handles duration internally - no assignment needed
        pass

    def show_mini_player(self):
        self.hide()
        if not hasattr(self, 'mini_player'):
            from mini_player import MiniPlayer
            self.mini_player = MiniPlayer(self)
            # Set album art if available
            pixmap = getattr(self.album_art_label, '_pixmap', None)
            if pixmap is not None:
                self.mini_player.set_album_art(pixmap)
        self.mini_player.show()

    def update_sleep_button_display(self):
        # Safely check if sleep_btn exists before accessing it
        if not hasattr(self, 'sleep_btn') or self.sleep_btn is None:
            return
            
        try:
            self.sleep_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255,255,255,0.08);
                    border: none;
                    border-radius: 8px;
                    font-size: 11px;
                    color: white;
                }
                QPushButton:hover {
                    background: rgba(255,255,255,0.18);
                }
            """)
            
            if self.sleep_timer.isActive():
                remaining_ms = self.sleep_timer.remainingTime()
                total_seconds = max(0, remaining_ms // 1000)
                if total_seconds >= 60:
                    mins = total_seconds // 60
                    self.sleep_btn.setText(f"{mins:02}")
                else:
                    self.sleep_btn.setText(f"{total_seconds:02}")
            else:
                self.sleep_btn.setText("🌙")
        except RuntimeError:
            # Widget has been deleted, stop the timer that calls this method
            if hasattr(self, 'sleep_update_timer'):
                self.sleep_update_timer.stop()


    def start_sleep_timer_seconds(self, seconds):
        self.sleep_timer.start(seconds * 1000)
        self.update_sleep_button_display()

    def show_sleep_timer_menu(self):
        timer_active = self.sleep_timer.isActive()
        
        if timer_active:
            remaining_ms = self.sleep_timer.remainingTime()
            remaining_min = remaining_ms // 60000
            remaining_sec = (remaining_ms % 60000) // 1000
        else:
            remaining_min = 0
            remaining_sec = 0
        
        dlg = SleepTimerDialog(self, timer_active=timer_active, remaining_min=remaining_min, remaining_sec=remaining_sec)
        
        # START WITH DIALOG INVISIBLE
        dlg.setWindowOpacity(0.0)
        
        self.set_blur(True, popup=dlg)
        dlg.move(self.geometry().center() - dlg.rect().center())
        
        # SHOW DIALOG AND FADE IN
        dlg.show()
        self.fade_in_dialog(dlg)
        
        result = dlg.exec()
        self.set_blur(False)
        
        if hasattr(self, '_blur_overlay'):
            self._blur_overlay.hide()
        
        # Handle stop button first (highest priority)
        if getattr(dlg, 'stop_clicked', False):
            self.cancel_sleep_timer()
            return

        # Only process timer start if dialog was properly accepted AND not cancelled
        if result == QDialog.DialogCode.Accepted and not hasattr(dlg, 'result_code'):
            if getattr(dlg, 'use_end_of_song', False):
                if self.controller and self.controller.get_length() > 0:
                    remaining_ms = self.controller.get_length() - self.controller.get_position()
                    seconds = max(1, int(remaining_ms // 1000))
                    self.start_sleep_timer_seconds(seconds)
            elif timer_active and hasattr(dlg, 'adjusted_seconds'):
                seconds = dlg.adjusted_seconds
                if seconds is not None and seconds <= 0:
                    self.cancel_sleep_timer()
                else:
                    self.start_sleep_timer_seconds(seconds)
            else:
                minutes = dlg.get_minutes()
                self.start_sleep_timer(minutes)

        # If dialog was rejected or cancelled, do nothing (no timer starts)
        elif result == QDialog.DialogCode.Rejected or getattr(dlg, 'result_code', None) == 'cancelled':
            print("Sleep timer cancelled - no timer started")  # Debug line you can remove later



    def start_sleep_timer(self, minutes):
        """Start sleep timer for specified minutes"""
        milliseconds = minutes * 60 * 1000
        self.sleep_timer.start(milliseconds)
        self.update_sleep_button_display()

    def cancel_sleep_timer(self):
        """Cancel the active sleep timer"""
        self.sleep_timer.stop()
        self.sleep_btn.setText("🌙")
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.08);
                border: none;
                border-radius: 8px;
                font-size: 16px;
                color: white;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.18);
            }
        """)

    def stop_playback(self):
        """Stop playback when sleep timer expires"""
        self.controller.pause()
        self.cancel_sleep_timer()
        # Update play button icon
        self.play_btn.setIcon(QIcon(resource_path(ICON_PLAY)))
        self.play_state_changed_signal.emit()

    def show_color_settings(self):
        """Show color settings dialog using ColorDialogManager"""
        self.color_dialog_manager.show_color_settings()

    def update_colors(self):
        """Update all UI elements with new colors"""
        # Update button styles
        self.update_load_button_style()
        self.update_shuffle_repeat_styles()
        
        # Update sliders
        self.seek_slider.setStyleSheet(get_seek_slider_style(self.color_settings.get_accent_green().name()))
        self.volume_slider.setStyleSheet(get_volume_slider_style(self.color_settings.get_accent_green().name()))
        
        # Update green overlay color
        self.update_green_overlay_color()
        
        # Force update of bottom shadow with new colors
        self.update_bottom_shadow()
        
        # Update playlist delegate colors
        self.playlist_widget.viewport().update()

        self.update_playlist_colors()  # Update playlist selection colors
        
        # Update Done button if dialog is open
        if hasattr(self, '_current_color_dialog_done_btn'):
            self._current_color_dialog_done_btn()
        
        # Force repaint of the entire window to ensure all elements update
        self.update()

    def update_playlist_colors(self):
        """Update playlist item colors to match current theme"""
        if not hasattr(self, 'playlist_widget'):
            return
            
        primary_color = self.color_settings.get_primary_green()
        hover_color = self.color_settings.get_hover_green()
        accent_color = self.color_settings.get_accent_green()
        
        # Create better hover effect that matches theme
        hover_rgba = f"rgba({hover_color.red()}, {hover_color.green()}, {hover_color.blue()}, 100)"
        primary_rgba = f"rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 180)"
        
        # Update the playlist widget styling with dynamic colors
        self.playlist_widget.setStyleSheet(f"""
        QListWidget {{
            background-color: rgba(0, 0, 0, 100);
            color: white;
            border: 1px solid rgba(255, 255, 255, 30);
            border-radius: 8px;
            padding: 5px;
            font-size: 9pt;
            font-weight: 500;
        }}
        QListWidget::item {{
            background-color: transparent;
            padding: 2px;
            border-radius: 3px;
            margin: 1px;
        }}
        QListWidget::item:alternate {{
            background-color: rgba(255, 255, 255, 10);
        }}
        QListWidget::item:selected {{
            background-color: {primary_rgba};
            color: white;
            border-radius: 3px;
        }}
        QListWidget::item:hover {{
            background-color: {hover_rgba};
            color: white;
            border-radius: 3px;
        }}
        QListWidget::item:selected:hover {{
            background-color: {primary_rgba};
            color: white;
            border-radius: 3px;
        }}
        """)
        
        # Force immediate update
        self.playlist_widget.update()



    def update_green_overlay_color(self):
        """Update the green overlay color based on current color settings"""
        primary_color = self.color_settings.get_primary_green()
        
        # Create a more visible semi-transparent version of the primary color
        overlay_color = f"rgba({primary_color.red()}, {primary_color.green()}, {primary_color.blue()}, 80)"
        self.green_overlay.setStyleSheet(f"background-color: {overlay_color};")
        
        # Force immediate visual update
        self.green_overlay.update()
        self.green_overlay.repaint()

    def update_shuffle_repeat_styles(self):
        """Update shuffle and repeat button styles"""
        if self.shuffle:
            self.shuffle_btn.setStyleSheet(get_button_style_sidebar_active(
                self.color_settings.get_primary_green().name(),
                self.color_settings.get_hover_green().name()
            ))
        else:
            self.shuffle_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)
        
        if self.repeat_mode != "off":
            self.repeat_btn.setStyleSheet(get_button_style_sidebar_active(
                self.color_settings.get_primary_green().name(),
                self.color_settings.get_hover_green().name()
            ))
        else:
            self.repeat_btn.setStyleSheet(BUTTON_STYLE_SIDEBAR)

    # Keep your existing methods unchanged
    def show_lyrics_panel(self):
        # Placeholder for lyrics panel logic
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Lyrics", "Lyrics panel will appear here.")

    def set_blur(self, enabled: bool, popup=None):
        """Set blur using VisualEffectsManager"""
        self.visual_effects.set_blur(enabled, popup)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    player = SASPlayer()
    player.show()
    sys.exit(app.exec())

    #App Created by FAiTH 