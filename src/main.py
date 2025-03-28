import sys
from PyQt5.QtWidgets import QApplication
from app import MainApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
