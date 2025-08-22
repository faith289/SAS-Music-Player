# album_art_manager.py - Album Art Processing Manager for SAS Music Player
# Extracted album art processing logic from main application

import os
import io
import colorsys
from PIL import Image, ImageFilter
from PyQt6.QtWidgets import QLabel
from PyQt6.QtGui import QPixmap, QImage, QColor, QPainterPath, QPainter
from PyQt6.QtCore import Qt
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from utils import calculate_brightness, get_safe_basename

class AlbumArtManager:
    """Handles all album art processing, color extraction, and image management for the SAS Music Player"""
    
    def __init__(self, parent):
        """Initialize AlbumArtManager with reference to parent SASPlayer instance"""
        self.parent = parent
        self.album_art_cache = {}
        
    def extract_dominant_color(self, image):
        """Extract dominant color from PIL Image"""
        if image is None:
            print("Warning: No image provided for color extraction")
            return QColor('#1DB954')  # Return default green

        try:
            # Resize image for faster processing
            small_image = image.resize((50, 50))
            # Convert to RGB if not already
            if small_image.mode != 'RGB':
                small_image = small_image.convert('RGB')

            # Get all pixels
            pixels = list(small_image.getdata())

            # Filter out very dark and very light pixels for better color selection
            filtered_pixels = []
            for r, g, b in pixels:
                # Convert to HSV to check brightness
                brightness = calculate_brightness(f"#{r:02x}{g:02x}{b:02x}")
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)
                # Keep pixels that aren't too dark, too light, or too desaturated
                if 0.15 < brightness < 0.9 and s > 0.3:
                    filtered_pixels.append((r, g, b))

            # If no good pixels found, use all pixels
            if not filtered_pixels:
                filtered_pixels = pixels

            # Count color frequency
            color_count = {}
            for color in filtered_pixels:
                # Group similar colors by reducing precision
                grouped_color = (color[0] // 10 * 10, color[1] // 10 * 10, color[2] // 10 * 10)
                color_count[grouped_color] = color_count.get(grouped_color, 0) + 1

            # Get most frequent color
            if color_count:
                dominant_rgb = max(color_count, key=color_count.get)
                # Ensure the color is vibrant enough for UI use
                r, g, b = dominant_rgb
                h, s, v = colorsys.rgb_to_hsv(r/255.0, g/255.0, b/255.0)

                # Boost saturation and adjust brightness for better UI visibility
                s = min(1.0, s * 1.3)  # Increase saturation
                if v < 0.4:
                    v = 0.5  # Brighten dark colors
                elif v > 0.8:
                    v = 0.7  # Darken very bright colors

                # Convert back to RGB
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                return QColor(int(r * 255), int(g * 255), int(b * 255))

        except Exception as e:
            print(f"Error extracting color: {e}")

        # Fallback to default green
        return QColor('#1DB954')

    def display_album_art(self, file_path):
        """Display album art from file, using cache if available"""
        # Check cache first
        if file_path in self.album_art_cache:
            self.set_album_art(self.album_art_cache[file_path])
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
                            return
        except Exception as e:
            print(f"[Album Art Error] {e}")
            pass

        # No album art: set dark grey pixmap
        dark_pixmap = QPixmap(220, 220)
        dark_pixmap.fill(QColor(30, 30, 30))
        self.parent.album_art_label.setPixmap(dark_pixmap)
        if hasattr(self.parent, 'mini_player') and self.parent.mini_player is not None:
            self.parent.mini_player.set_album_art(dark_pixmap)

    def set_album_art(self, image):
        """Set album art image with color extraction and background processing"""
        self.parent.album_original_image = image

        # Extract dominant color from album art if auto-color is enabled
        if self.parent.color_settings.get_auto_color_from_album():
            dominant_color = self.extract_dominant_color(image)
            
            # Set colors based on extracted color
            self.parent.color_settings.set_primary_green(dominant_color)
            # Create harmonious hover and accent colors
            hover_color = dominant_color.lighter(120)  # 20% lighter
            accent_color = dominant_color.lighter(140)  # 40% lighter
            self.parent.color_settings.set_hover_green(hover_color)
            self.parent.color_settings.set_accent_green(accent_color)

            # Update UI with new colors
            self.parent.update_colors()
            self.parent.update_green_overlay_color()
            self.parent.update_bottom_shadow()
            self.parent.update_playlist_colors()  # Update playlist colors when album art changes

        # Continue with existing album art display logic
        data = image.convert("RGB").tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)

        # Create rounded album art
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

        # Create padded album art display
        padded = QPixmap(220, 220)
        padded.fill(Qt.GlobalColor.transparent)
        painter = QPainter(padded)
        try:
            x = (220 - rounded.width()) // 2
            y = (220 - rounded.height()) // 2
            painter.drawPixmap(x, y, rounded)
        finally:
            painter.end()

        # Set album art to main display
        self.parent.album_art_label.setPixmap(padded)
        
        # Update mini player if it exists
        if hasattr(self.parent, 'mini_player') and self.parent.mini_player is not None:
            self.parent.mini_player.set_album_art(padded)

        # Create blurred background
        try:
            # Create blurred version for background
            resized_for_bg = image.resize((self.parent.width(), self.parent.height()))
            blurred_bg = resized_for_bg.filter(ImageFilter.GaussianBlur(35))
            
            # Convert to QPixmap
            bg_data = blurred_bg.convert("RGB").tobytes("raw", "RGB")
            bg_qimage = QImage(bg_data, blurred_bg.width, blurred_bg.height, QImage.Format.Format_RGB888)
            self.parent.album_blurred_pixmap = QPixmap.fromImage(bg_qimage)

            # Apply to background labels with smooth transition
            self.parent.update_blurred_background_smooth()
        except Exception as e:
            print(f"Error creating blurred background: {e}")

    def clear_cache(self):
        """Clear the album art cache"""
        self.album_art_cache.clear()

    def get_cached_art(self, file_path):
        """Get cached album art if available"""
        return self.album_art_cache.get(file_path, None)

    def cache_album_art(self, file_path, image):
        """Cache album art for future use"""
        self.album_art_cache[file_path] = image
