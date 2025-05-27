import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile, QTextStream
from app import MainApp

def load_theme(app):
    theme_file = QFile(os.path.join(os.path.dirname(__file__), "themes", "dark.qss"))
    if theme_file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(theme_file)
        app.setStyleSheet(stream.readAll())
        theme_file.close()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    load_theme(app)
    w = MainApp()
    w.show()
    sys.exit(app.exec())
