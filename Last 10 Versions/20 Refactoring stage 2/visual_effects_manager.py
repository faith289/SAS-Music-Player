# visual_effects_manager.py - Visual Effects Manager for SAS Music Player
# Extracted visual effects and animation logic from main application

import os
import sys
from PIL import Image, ImageFilter
from PyQt6.QtWidgets import (
    QGraphicsOpacityEffect, QGraphicsBlurEffect, QLabel, QWidget
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty

class VisualEffectsManager:
    """Handles all visual effects, animations, and blur management for the SAS Music Player"""
    
    def __init__(self, parent):
        """Initialize VisualEffectsManager with reference to parent SASPlayer instance"""
        self.parent = parent
        self.fade_animations = []  # Hold references to fade-in animations
        
    def animate_dark_overlay(self, target_opacity, duration=350):
        """Animate the dark overlay to target opacity"""
        if not hasattr(self.parent, "dark_overlay_opacity_effect"):
            from PyQt6.QtWidgets import QGraphicsOpacityEffect
            self.parent.dark_overlay_opacity_effect = QGraphicsOpacityEffect(self.parent.dark_overlay)
            self.parent.dark_overlay.setGraphicsEffect(self.parent.dark_overlay_opacity_effect)

        self.parent.dark_overlay_animation = QPropertyAnimation(self.parent.dark_overlay_opacity_effect, b"opacity")
        self.parent.dark_overlay_animation.setDuration(duration)
        self.parent.dark_overlay_animation.setStartValue(self.parent.dark_overlay_opacity_effect.opacity())
        self.parent.dark_overlay_animation.setEndValue(target_opacity)
        self.parent.dark_overlay_animation.start()

    def fade_in_widget(self, widget, duration=350):
        """Create fade-in effect for widgets"""
        effect = QGraphicsOpacityEffect()
        widget.setGraphicsEffect(effect)
        
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        
        # Keep reference so it's not garbage collected
        self.fade_animations.append(anim)
        
        def remove_anim():
            if anim in self.fade_animations:
                self.fade_animations.remove(anim)
        
        anim.finished.connect(remove_anim)
        anim.start()

    def fade_in_dialog(self, dialog, duration=300):
        """Create a smooth fade-in effect for dialogs"""
        if not hasattr(self.parent, '_dialog_fade_animations'):
            self.parent._dialog_fade_animations = []

        # Create fade-in animation
        fade_anim = QPropertyAnimation(dialog, b"windowOpacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Store reference to prevent garbage collection
        self.parent._dialog_fade_animations.append(fade_anim)

        # Clean up animation reference when finished
        def cleanup():
            if fade_anim in self.parent._dialog_fade_animations:
                self.parent._dialog_fade_animations.remove(fade_anim)

        fade_anim.finished.connect(cleanup)
        fade_anim.start()

    def fade_out_dialog(self, dialog, duration=250):
        """Create a smooth fade-out effect for dialogs"""
        if not hasattr(self.parent, '_dialog_fade_animations'):
            self.parent._dialog_fade_animations = []

        # Create fade-out animation
        fade_anim = QPropertyAnimation(dialog, b"windowOpacity")
        fade_anim.setDuration(duration)
        fade_anim.setStartValue(dialog.windowOpacity())
        fade_anim.setEndValue(0.0)
        fade_anim.setEasingCurve(QEasingCurve.Type.InCubic)

        # Store reference to prevent garbage collection
        self.parent._dialog_fade_animations.append(fade_anim)

        # Close dialog when fade-out completes
        def close_dialog():
            dialog.accept()
            if fade_anim in self.parent._dialog_fade_animations:
                self.parent._dialog_fade_animations.remove(fade_anim)

        fade_anim.finished.connect(close_dialog)
        fade_anim.start()

    def update_blurred_background(self):
        """Basic blurred background update"""
        if isinstance(self.parent.album_original_image, Image.Image):
            try:
                resized = self.parent.album_original_image.resize((self.parent.width(), self.parent.height()))
                blurred = resized.filter(ImageFilter.GaussianBlur(35))
                bg_data = blurred.convert("RGB").tobytes("raw", "RGB")
                bg_qimage = QImage(bg_data, blurred.width, blurred.height, QImage.Format.Format_RGB888)
                bg_pixmap = QPixmap.fromImage(bg_qimage)
                self.parent.bg_blur_label_1.setPixmap(bg_pixmap)
            except Exception as e:
                print("Error updating blurred background:", e)

    def update_blurred_background_smooth(self):
        """Update blurred background with smooth fade-in transition"""
        if not hasattr(self.parent, 'album_blurred_pixmap') or self.parent.album_blurred_pixmap is None:
            return

        try:
            # Scale the blurred pixmap to current window size
            scaled_blur = self.parent.album_blurred_pixmap.scaled(
                self.parent.width(),
                self.parent.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation
            )

            # Initialize the label tracker if it doesn't exist
            if not hasattr(self.parent, '_current_bg_label'):
                self.parent._current_bg_label = 1

            # Determine which labels to use
            if self.parent._current_bg_label == 1:
                target_label = self.parent.bg_blur_label_2
                previous_label = self.parent.bg_blur_label_1
                self.parent._current_bg_label = 2
            else:
                target_label = self.parent.bg_blur_label_1
                previous_label = self.parent.bg_blur_label_2
                self.parent._current_bg_label = 1

            # Set the new background (initially invisible)
            target_label.setPixmap(scaled_blur)

            # Keep all backgrounds at the bottom
            self.parent.bg_blur_label_1.lower()
            self.parent.bg_blur_label_2.lower()

            # Ensure UI elements stay above
            self.parent.central_widget.raise_()

            # Keep brightness button on top
            if hasattr(self.parent, 'brightness_btn'):
                self.parent.brightness_btn.raise_()
                self.parent.brightness_btn.show()

            # Create fade-in effect for the new background
            self.create_background_fade_in(target_label, previous_label)

            print(f"Background switched to label {self.parent._current_bg_label} with fade-in effect")

        except Exception as e:
            print(f"Error updating blurred background: {e}")

    def create_background_fade_in(self, target_label, previous_label):
        """Create a smooth cross-fade effect for background transitions"""
        # Create opacity effects for both labels
        target_opacity_effect = QGraphicsOpacityEffect()
        target_label.setGraphicsEffect(target_opacity_effect)
        target_opacity_effect.setOpacity(0.0)

        # If previous label doesn't have an opacity effect, create one
        previous_opacity_effect = previous_label.graphicsEffect()
        if not isinstance(previous_opacity_effect, QGraphicsOpacityEffect):
            previous_opacity_effect = QGraphicsOpacityEffect()
            previous_label.setGraphicsEffect(previous_opacity_effect)
            previous_opacity_effect.setOpacity(1.0)

        # Fade IN animation for target label
        self.parent.bg_fade_in_animation = QPropertyAnimation(target_opacity_effect, b"opacity")
        self.parent.bg_fade_in_animation.setDuration(600)  # 600ms fade duration
        self.parent.bg_fade_in_animation.setStartValue(0.0)
        self.parent.bg_fade_in_animation.setEndValue(1.0)
        self.parent.bg_fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Fade OUT animation for previous label
        self.parent.bg_fade_out_animation = QPropertyAnimation(previous_opacity_effect, b"opacity")
        self.parent.bg_fade_out_animation.setDuration(600)  # Same duration for smooth cross-fade
        self.parent.bg_fade_out_animation.setStartValue(1.0)
        self.parent.bg_fade_out_animation.setEndValue(0.0)
        self.parent.bg_fade_out_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Clean up when both animations complete
        def on_fade_complete():
            previous_label.clear()
            # Clean up animation references
            if hasattr(self.parent, 'bg_fade_in_animation'):
                delattr(self.parent, 'bg_fade_in_animation')
            if hasattr(self.parent, 'bg_fade_out_animation'):
                delattr(self.parent, 'bg_fade_out_animation')

        self.parent.bg_fade_in_animation.finished.connect(on_fade_complete)

        # Start both animations simultaneously for cross-fade effect
        self.parent.bg_fade_in_animation.start()
        self.parent.bg_fade_out_animation.start()

    def ensure_proper_layer_order(self):
        """Ensure UI elements stay above background layers"""
        # Keep all background elements at the bottom
        if hasattr(self.parent, 'bg_blur_label_1'):
            self.parent.bg_blur_label_1.lower()
        if hasattr(self.parent, 'bg_blur_label_2'):
            self.parent.bg_blur_label_2.lower()
        if hasattr(self.parent, 'dark_overlay'):
            self.parent.dark_overlay.lower()
        if hasattr(self.parent, 'playlist_glass'):
            self.parent.playlist_glass.lower()
        if hasattr(self.parent, 'green_overlay'):
            self.parent.green_overlay.lower()

        # Raise all main UI elements
        if hasattr(self.parent, 'central_widget'):
            self.parent.central_widget.raise_()

        # Ensure all main UI elements stay above backgrounds
        ui_elements = ['album_art_label', 'song_label', 'meta_label', 'play_btn', 'prev_btn', 'next_btn',
                       'shuffle_btn', 'repeat_btn', 'seek_slider', 'volume_slider', 'playlist_widget']
        
        for element in ui_elements:
            if hasattr(self.parent, element):
                getattr(self.parent, element).raise_()

        # CRITICAL: Brightness button must be ABSOLUTELY on top
        if hasattr(self.parent, 'brightness_btn'):
            # Remove any mouse event blocking
            self.parent.brightness_btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
            # Ensure it's visible and clickable
            self.parent.brightness_btn.setEnabled(True)
            self.parent.brightness_btn.show()
            self.parent.brightness_btn.raise_()
            # Force it to be the topmost widget
            self.parent.brightness_btn.activateWindow()

    def set_blur(self, enabled: bool, popup=None):
        """Complete blur system with overlays and animations"""
        if enabled:
            # Screenshot+blur overlay with true fade
            if not hasattr(self.parent, '_blur_overlay_widget') or self.parent._blur_overlay_widget is None:
                
                class BlurOverlayWidget(QLabel):
                    def __init__(self, parent, blurred_img):
                        super().__init__(parent)
                        self.setGeometry(parent.rect())
                        self._blurred_img = blurred_img.convert("RGBA")
                        self._fade = 0.0

                        # Create a fully transparent version of the blurred image
                        self._blurred_img_clear = self._blurred_img.copy()
                        self._blurred_img_clear.putalpha(0)

                        self.updatePixmap()
                        self.show()
                        self.raise_()

                    def getFade(self):
                        return self._fade

                    def setFade(self, value):
                        self._fade = value
                        self.updatePixmap()

                    def updatePixmap(self):
                        # Blend between fully transparent blurred and fully opaque blurred
                        blended = Image.blend(self._blurred_img_clear, self._blurred_img, self._fade)
                        data = blended.tobytes("raw", "RGBA")
                        qimg_blend = QImage(data, blended.width, blended.height, QImage.Format.Format_RGBA8888)
                        pixmap_blend = QPixmap.fromImage(qimg_blend)
                        self.setPixmap(pixmap_blend)
                        self.setScaledContents(True)

                    fade = pyqtProperty(float, fget=getFade, fset=setFade)

                # Grab screenshot of main window
                pixmap = self.parent.grab()
                qimg = pixmap.toImage().convertToFormat(QImage.Format.Format_RGBA8888)
                width, height = qimg.width(), qimg.height()
                ptr = qimg.bits()
                ptr.setsize(qimg.sizeInBytes())
                arr = bytes(ptr)
                img = Image.frombytes("RGBA", (width, height), arr)
                blurred = img.filter(ImageFilter.GaussianBlur(8))

                self.parent._blur_overlay_widget = BlurOverlayWidget(self.parent, blurred)

            else:
                self.parent._blur_overlay_widget.setGeometry(self.parent.rect())
                self.parent._blur_overlay_widget.show()
                self.parent._blur_overlay_widget.raise_()

            # Animate fade in
            self.parent._blur_fade_anim = QPropertyAnimation(self.parent._blur_overlay_widget, b'fade')
            self.parent._blur_fade_anim.setStartValue(0.0)
            self.parent._blur_fade_anim.setEndValue(1.0)
            self.parent._blur_fade_anim.setDuration(400)
            self.parent._blur_fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.parent._blur_fade_anim.start()

            # Add click-blocking overlay
            if not hasattr(self.parent, '_blur_overlay'):
                
                class BlurClickOverlay(QWidget):
                    def __init__(self, parent, popup):
                        super().__init__(parent)
                        self.popup = popup
                        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
                        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
                        self.setStyleSheet('background: rgba(0,0,0,0);')
                        self.setGeometry(parent.rect())
                        self.show()
                        self.raise_()

                    def mousePressEvent(self, event):
                        if self.popup:
                            self.popup.reject()  # Close the popup
                        self.hide()  # Hide overlay after first click

                self.parent._blur_overlay = BlurClickOverlay(self.parent, popup)
            else:
                self.parent._blur_overlay.popup = popup
                self.parent._blur_overlay.setGeometry(self.parent.rect())
                self.parent._blur_overlay.show()

        else:
            # Animate fade out, then hide and delete overlay
            if hasattr(self.parent, '_blur_overlay_widget') and self.parent._blur_overlay_widget is not None:
                overlay = self.parent._blur_overlay_widget
                anim = QPropertyAnimation(overlay, b'fade')
                overlay._fade_anim = anim  # Prevent GC
                anim.setStartValue(overlay._fade)
                anim.setEndValue(0.0)
                anim.setDuration(400)
                anim.setEasingCurve(QEasingCurve.Type.OutCubic)

                def cleanup():
                    if hasattr(self.parent, '_blur_overlay_widget') and self.parent._blur_overlay_widget is not None:
                        self.parent._blur_overlay_widget.hide()
                        self.parent._blur_overlay_widget.deleteLater()
                        self.parent._blur_overlay_widget = None

                anim.finished.connect(cleanup)
                anim.start()
