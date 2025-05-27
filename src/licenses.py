from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices

def show_educollector_license():
    QDesktopServices.openUrl(QUrl("https://github.com/Efeckc17/EduCollector/blob/main/LICENSE"))

def show_pyside6_license():
    QDesktopServices.openUrl(QUrl("https://www.qt.io/licensing/open-source-lgpl-obligations")) 