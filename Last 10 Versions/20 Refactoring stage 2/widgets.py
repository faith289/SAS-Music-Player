from PyQt6.QtWidgets import QLabel, QPushButton, QListWidget, QStyledItemDelegate, QGraphicsDropShadowEffect, QAbstractScrollArea, QStyle, QStyleOptionViewItem, QWidget
from PyQt6.QtCore import QTimer, Qt, QEvent, QSize, pyqtSignal, pyqtSlot, QPointF, QRectF
from PyQt6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPainterPath, QBrush, QPixmap

class ShadowLabel(QLabel):
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        text = self.text()
        rect = self.rect()
        align = Qt.AlignmentFlag.AlignCenter
        shadow_offsets = [ (1, 1, 40), (2, 2, 30), (3, 3, 20), (4, 4, 10) ]
        for dx, dy, alpha in shadow_offsets:
            painter.setPen(QColor(0, 0, 0, alpha))
            painter.drawText(rect.translated(dx, dy), align, text)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.drawText(rect, align, text)

class ScrollingLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(parent)
        self.full_text = text
        self.offset = 0
        self.scroll_speed = 1
        self.scroll_delay = 30
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_scroll)
        self.setFont(self.font())
        self.setStyleSheet("color: white; background: transparent;")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setText(text)
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(10)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 180))
        self.setGraphicsEffect(shadow)
    def setText(self, text):
        self.full_text = text
        self.offset = 0
        self.update_scroll_state()
        self.repaint()
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scroll_state()
    def update_scroll_state(self):
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.full_text)
        if text_width > self.width():
            self.timer.start(self.scroll_delay)
        else:
            self.timer.stop()
            self.offset = 0
        self.repaint()
    def update_scroll(self):
        metrics = QFontMetrics(self.font())
        scroll_text = self.full_text + "    "
        total_width = metrics.horizontalAdvance(scroll_text)
        self.offset += self.scroll_speed
        if self.offset >= total_width:
            self.offset = 0
        self.repaint()
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setFont(self.font())
        metrics = QFontMetrics(self.font())
        text_width = metrics.horizontalAdvance(self.full_text)
        y = int((self.height() + metrics.ascent() - metrics.descent()) / 2)
        if text_width <= self.width():
            x = (self.width() - text_width) // 2
            painter.setPen(QColor(0, 0, 0, 50))
            for dx, dy in [(1, 1), (2, 2), (0, 2)]:
                painter.drawText(x + dx, y + dy, self.full_text)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(x, y, self.full_text)
        else:
            scroll_text = self.full_text + "    "
            full_scroll = scroll_text + scroll_text
            text_width = metrics.horizontalAdvance(scroll_text)
            x = -self.offset
            while x < self.width():
                painter.setPen(QColor(0, 0, 0, 50))
                for dx, dy in [(1, 1), (2, 2), (0, 2)]:
                    painter.drawText(x + dx, y + dy, full_scroll)
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(x, y, full_scroll)
                x += text_width

class ReorderablePlaylist(QListWidget):
    def __init__(self, parent=None, on_reorder_callback=None):
        super().__init__(parent)
        self.on_reorder_callback = on_reorder_callback
    def dropEvent(self, event):
        super().dropEvent(event)
        if self.on_reorder_callback:
            self.on_reorder_callback()

class GlowButton(QPushButton):
    def __init__(self, *args, glow_color=QColor(0, 255, 150, 180), **kwargs):
        super().__init__(*args, **kwargs)
        self._glow_color = glow_color
    def enterEvent(self, event):
        glow_effect = QGraphicsDropShadowEffect(self)
        glow_effect.setBlurRadius(15)
        glow_effect.setColor(self._glow_color)
        glow_effect.setOffset(0, 0)
        self.setGraphicsEffect(glow_effect)
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.setGraphicsEffect(None)
        super().leaveEvent(event)

class PulsingDelegate(QStyledItemDelegate):
    def __init__(self, parent, get_current_index_func, color_settings=None):
        super().__init__(parent)
        self.pulse_value = 0
        self.increasing = True
        self.get_current_index = get_current_index_func
        self.color_settings = color_settings
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_pulse)
        self.timer.start(60)
    def update_pulse(self):
        if self.increasing:
            self.pulse_value += 8  # Faster and stronger pulse
            if self.pulse_value >= 155:
                self.increasing = False
        else:
            self.pulse_value -= 8
            if self.pulse_value <= 40:
                self.increasing = True
        parent = self.parent()
        if isinstance(parent, QAbstractScrollArea):
            viewport = parent.viewport()
            if viewport is not None and hasattr(viewport, 'update') and callable(viewport.update):
                viewport.update()  # repaint 
    def paint(self, painter, option, index):
        current_row = self.get_current_index()
        if painter is not None:
            painter.save()
            if index.row() == current_row:
                rect = option.rect
                # Softer, less intense green glow
                pulse_alpha = int(60 + self.pulse_value)  # 100–195 alpha range
                if self.color_settings:
                    base_color = self.color_settings.get_accent_green()
                    glow_color = QColor(base_color.red(), base_color.green(), base_color.blue(), min(pulse_alpha, 195))
                else:
                    glow_color = QColor(0, 255, 100, min(pulse_alpha, 195))
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                painter.setBrush(QBrush(glow_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(rect.adjusted(1, 1, -1, -1), 8, 8)
                # Draw a small play icon (triangle) on the left
                icon_size = rect.height() // 2
                icon_margin = 8
                triangle = [
                    rect.left() + icon_margin, rect.center().y() - icon_size // 2,
                    rect.left() + icon_margin, rect.center().y() + icon_size // 2,
                    rect.left() + icon_margin + icon_size, rect.center().y()
                ]
                points = [
                    QPointF(triangle[0], triangle[1]),
                    QPointF(triangle[2], triangle[3]),
                    QPointF(triangle[4], triangle[5])
                ]
                painter.setBrush(QColor(255, 255, 255))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawPolygon(*points)
                # Set text color based on background brightness
                if self.color_settings:
                    base_color = self.color_settings.get_accent_green()
                    # Use white text on dark backgrounds, black on light backgrounds
                    text_color = QColor(255, 255, 255) if base_color.lightness() < 128 else QColor(0, 0, 0)
                else:
                    text_color = QColor(0, 0, 0)
                
                painter.setPen(text_color)
                text = index.data()
                font = painter.font()
                font.setBold(True)
                painter.setFont(font)
                metrics = QFontMetrics(font)
                # Indent text to the right of the icon
                text_left = rect.left() + icon_margin + icon_size + 6
                text_rect = QRectF(text_left, rect.top(), rect.width() - (text_left - rect.left()), rect.height())
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
                painter.restore()
                # Draw a less strong selection color so the pulse is visible
                if option.state.value & 2:
                    painter.save()
                    if self.color_settings:
                        base_color = self.color_settings.get_primary_green()
                        selection_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 100)
                    else:
                        selection_color = QColor(30, 120, 80, 100)  # Lower alpha for selection
                    painter.setBrush(QBrush(selection_color))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawRoundedRect(option.rect.adjusted(2, 2, -2, -2), 6, 6)
                    painter.restore()
                return  # Don't let default painting override our text color
            painter.restore()
            # Draw a less strong selection color so the pulse is visible
            if option.state.value & 2:
                painter.save()
                if self.color_settings:
                    base_color = self.color_settings.get_primary_green()
                    selection_color = QColor(base_color.red(), base_color.green(), base_color.blue(), 100)
                else:
                    selection_color = QColor(30, 120, 80, 100)  # Lower alpha for selection
                painter.setBrush(QBrush(selection_color))
                painter.setPen(Qt.PenStyle.NoPen)
                painter.drawRoundedRect(option.rect.adjusted(2, 2, -2, -2), 6, 6)
                painter.restore()
        # Default painting
        super().paint(painter, option, index)
                
class AlbumArtWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self.setFixedSize(220, 220)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # No QGraphicsDropShadowEffect; we'll draw the shadow manually

    def setPixmap(self, pixmap: QPixmap):
        self._pixmap = pixmap
        self.update()

    def clear(self):
        self._pixmap = None
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtWidgets import QGraphicsBlurEffect, QGraphicsScene, QGraphicsPixmapItem
        from PyQt6.QtGui import QRadialGradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        # Album art size
        if self._pixmap:
            art_w = self._pixmap.width()
            art_h = self._pixmap.height()
        else:
            art_w = art_h = 180
        x = (self.width() - art_w) // 2
        y = (self.height() - art_h) // 2
        # Shadow parameters
        shadow_blur = 80
        shadow_alpha = 80
        shadow_radius = 80
        # Center the shadow ellipse just offset from the album art's bottom-right
        shadow_cx = x + art_w + shadow_radius // 2 - 10
        shadow_cy = y + art_h + shadow_radius // 2 - 10
        # 1. Draw shadow shape onto a QPixmap
        shadow_pixmap = QPixmap(self.width(), self.height())
        shadow_pixmap.fill(Qt.GlobalColor.transparent)
        shadow_painter = QPainter(shadow_pixmap)
        shadow_painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        grad_corner = QRadialGradient(shadow_cx, shadow_cy, shadow_radius)
        grad_corner.setColorAt(0.0, QColor(0, 0, 0, shadow_alpha))
        grad_corner.setColorAt(1.0, QColor(0, 0, 0, 0))
        shadow_painter.setBrush(grad_corner)
        shadow_painter.setPen(Qt.PenStyle.NoPen)
        shadow_painter.drawEllipse(shadow_cx - shadow_radius, shadow_cy - shadow_radius, shadow_radius * 2, shadow_radius * 2)
        shadow_painter.end()
        # 2. Blur the shadow pixmap
        blur_effect = QGraphicsBlurEffect()
        blur_effect.setBlurRadius(shadow_blur)
        scene = QGraphicsScene()
        item = QGraphicsPixmapItem(shadow_pixmap)
        item.setGraphicsEffect(blur_effect)
        scene.addItem(item)
        blurred_shadow = QPixmap(shadow_pixmap.size())
        blurred_shadow.fill(Qt.GlobalColor.transparent)
        blur_painter = QPainter(blurred_shadow)
        scene.render(blur_painter)
        blur_painter.end()
        # 3. Draw the blurred shadow behind the album art
        painter.drawPixmap(0, 0, blurred_shadow)
        # 4. Draw album art
        if self._pixmap:
            painter.drawPixmap(x, y, self._pixmap)
        else:
            painter.setPen(QColor(120, 120, 120))
            font = painter.font()
            font.setPointSize(12)
            painter.setFont(font)
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Album Art") 
                