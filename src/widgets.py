import sys, time
from PyQt5.QtWidgets import QTextEdit, QPushButton
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect

class ZoomTxt(QTextEdit):
    def wheelEvent(self, e):
        if e.modifiers() & Qt.ControlModifier:
            if e.angleDelta().y() > 0:
                self.zoomIn(1)
            else:
                self.zoomOut(1)
            e.accept()
        else:
            super().wheelEvent(e)

class TxtEff(QThread):
    update_text = pyqtSignal(str)
    def __init__(self, txt, parent=None):
        super().__init__(parent)
        self.txt = txt
    def run(self):
        for line in self.txt.split('\n'):
            self.update_text.emit(line + "\n")
            time.sleep(0.05)

class AniBtn(QPushButton):
    def __init__(self, txt):
        super().__init__(txt)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.setStyleSheet("QPushButton {background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7b1fa2, stop:1 #512da8); color: #ffffff; border: none; border-radius: 5px; padding: 8px 14px;} QPushButton:hover {background-color: #9575cd;}")
        self.default_geometry = None
        self.anim = QPropertyAnimation(self, b"geometry")
    def enterEvent(self, e):
        if self.default_geometry is None:
            self.default_geometry = self.geometry()
        self.anim.stop()
        r = self.default_geometry
        self.anim.setStartValue(r)
        self.anim.setEndValue(QRect(r.x()-3, r.y()-3, r.width()+6, r.height()+6))
        self.anim.setDuration(150)
        self.anim.start()
        super().enterEvent(e)
    def leaveEvent(self, e):
        self.anim.stop()
        r = self.default_geometry
        self.anim.setStartValue(self.geometry())
        self.anim.setEndValue(r)
        self.anim.setDuration(150)
        self.anim.start()
        super().leaveEvent(e)
