from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget

class RaycastPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("CentralWidget")
        self._radius = 12

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        rect = self.rect().adjusted(8, 8, -8, -8)
        path = QPainterPath()
        path.addRoundedRect(QRectF(rect), self._radius, self._radius)

        bg_top = QColor("#15181E")
        bg_bottom = QColor("#12151B")
        grad_bg = QRadialGradient(rect.center(), max(rect.width(), rect.height()) * 0.9)
        grad_bg.setColorAt(0.0, bg_top)
        grad_bg.setColorAt(0.7, bg_bottom)
        grad_bg.setColorAt(1.0, bg_bottom)

        p.fillPath(path, grad_bg)

        aurora1 = QRadialGradient(rect.topLeft(), rect.width() * 0.6)
        a1 = QColor(91, 52, 214, 38)
        aurora1.setColorAt(0.0, a1)
        aurora1.setColorAt(0.7, QColor(91, 52, 214, 6))
        aurora1.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, aurora1)

        aurora2 = QRadialGradient(rect.bottomRight(), rect.width() * 0.6)
        a2 = QColor(25, 115, 232, 34)
        aurora2.setColorAt(0.0, a2)
        aurora2.setColorAt(0.7, QColor(25, 115, 232, 6))
        aurora2.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillPath(path, aurora2)

        border = QColor(255, 255, 255, 22)
        p.setPen(border)
        p.drawPath(path)
