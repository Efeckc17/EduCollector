import sys
import time
import uuid
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLineEdit, QPushButton, QTextEdit, QLabel, QComboBox, QMessageBox, QFileDialog
)
from PyQt5.QtGui import QFont, QTextCursor
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect

class WriteTextEffect(QThread):
    update_text = pyqtSignal(str)

    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text

    def run(self):
        for line in self.text.split('\n'):
            self.update_text.emit(line + "\n")
            time.sleep(0.1)

class AnimatedButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFont(QFont("Arial", 12, QFont.Bold))
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 5px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #388E3C;
            }
        """)
        self.default_geometry = None
        self.animation = QPropertyAnimation(self, b"geometry")

    def enterEvent(self, event):
        if self.default_geometry is None:
            self.default_geometry = self.geometry()  

        self.animation.stop()
        rect = self.default_geometry
        self.animation.setStartValue(rect)
        self.animation.setEndValue(QRect(rect.x() - 5, rect.y() - 5, rect.width() + 10, rect.height() + 10))
        self.animation.setDuration(200)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.stop()
        rect = self.default_geometry  
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(rect)
        self.animation.setDuration(200)
        self.animation.start()
        super().leaveEvent(event)


class EduCollectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduCollector")
        self.setGeometry(100, 100, 1024, 768)

        self.languages = {
            "English": {
                "code": "en",
                "wiki_url": "https://en.wikipedia.org/wiki/",
                "labels": {
                    "language_label": "Select Language:",
                    "topic_label": "Enter a topic to search:",
                    "search_button": "Search",
                    "save_button": "Save Result",
                    "exit_button": "Exit"
                }
            },
            "Türkçe": {
                "code": "tr",
                "wiki_url": "https://tr.wikipedia.org/wiki/",
                "labels": {
                    "language_label": "Dil Seçiniz:",
                    "topic_label": "Araştırmak istediğiniz konuyu girin:",
                    "search_button": "Araştır",
                    "save_button": "Sonucu Kaydet",
                    "exit_button": "Çıkış"
                }
            },
            "Français": {
                "code": "fr",
                "wiki_url": "https://fr.wikipedia.org/wiki/",
                "labels": {
                    "language_label": "Choisir la langue:",
                    "topic_label": "Entrez un sujet à rechercher:",
                    "search_button": "Rechercher",
                    "save_button": "Enregistrer le résultat",
                    "exit_button": "Quitter"
                }
            },
            "Deutsch": {
                "code": "de",
                "wiki_url": "https://de.wikipedia.org/wiki/",
                "labels": {
                    "language_label": "Sprache auswählen:",
                    "topic_label": "Geben Sie ein Thema zur Suche ein:",
                    "search_button": "Suchen",
                    "save_button": "Ergebnis speichern",
                    "exit_button": "Beenden"
                }
            },
            "العربية": {
                "code": "ar",
                "wiki_url": "https://ar.wikipedia.org/wiki/",
                "labels": {
                    "language_label": "اختر اللغة:",
                    "topic_label": "أدخل موضوعًا للبحث:",
                    "search_button": "بحث",
                    "save_button": "احفظ النتيجة",
                    "exit_button": "خروج"
                }
            }
        }
        self.current_language = "English"
        self.result_text = ""
        self.blocked_keywords = {
            "en": ["racism", "hate", "violence", "discrimination", "homophobia"],
            "tr": ["ırkçılık", "nefret", "şiddet", "ayrımcılık", "homofobi"],
            "fr": ["racisme", "haine", "violence", "discrimination", "homophobie"],
            "de": ["rassismus", "hass", "gewalt", "diskriminierung", "homophobie"],
            "ar": ["العنصرية", "كراهية", "عنف", "تمييز", "رهاب المثلية"]
        }

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.setStyleSheet("""
            background-color: #2c2c2c;
            color: #f1f1f1;
        """)

        self.title_label = QLabel("EduCollector")
        self.title_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.title_label)

        self.language_layout = QHBoxLayout()
        self.language_label = QLabel("Select Language:")
        self.language_label.setFont(QFont("Arial", 12))
        self.language_selector = QComboBox()
        self.language_selector.addItems(self.languages.keys())
        self.language_selector.currentIndexChanged.connect(self.update_language)
        self.language_layout.addWidget(self.language_label)
        self.language_layout.addWidget(self.language_selector)
        self.main_layout.addLayout(self.language_layout)

        self.topic_label = QLabel("Enter a topic to search:")
        self.topic_label.setFont(QFont("Arial", 14))
        self.main_layout.addWidget(self.topic_label)

        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Type your topic here...")
        self.topic_input.setFont(QFont("Arial", 12))
        self.topic_input.setStyleSheet("""
            QLineEdit {
                background-color: #3c3c3c;
                color: #f1f1f1;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus {
                border: 2px solid #1e7d32;
            }
        """)
        self.main_layout.addWidget(self.topic_input)

        self.button_layout = QHBoxLayout()

        self.search_button = AnimatedButton("Search")
        self.search_button.clicked.connect(self.search_topic)
        self.button_layout.addWidget(self.search_button)

        self.save_button = AnimatedButton("Save Result")
        self.save_button.clicked.connect(self.save_result)
        self.button_layout.addWidget(self.save_button)

        self.exit_button = AnimatedButton("Exit")
        self.exit_button.clicked.connect(self.close)
        self.button_layout.addWidget(self.exit_button)

        self.main_layout.addLayout(self.button_layout)

        self.result_area = QTextEdit()
        self.result_area.setFont(QFont("Arial", 14))
        self.result_area.setStyleSheet("""
            QTextEdit {
                background-color: #3c3c3c;
                color: #f1f1f1;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.result_area.setReadOnly(True)
        self.main_layout.addWidget(self.result_area)
        self.update_language()

    def update_language(self):
        self.current_language = self.language_selector.currentText()
        labels = self.languages[self.current_language]["labels"]
        self.language_label.setText(labels["language_label"])
        self.topic_label.setText(labels["topic_label"])
        self.search_button.setText(labels["search_button"])
        self.save_button.setText(labels["save_button"])
        self.exit_button.setText(labels["exit_button"])

    def search_topic(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Error", "Please enter a topic to search!")
            return
        current_keywords = self.blocked_keywords.get(self.languages[self.current_language]["code"], [])
        for keyword in current_keywords:
            if keyword.lower() in topic.lower():
                QMessageBox.warning(self, "Blocked", "This topic contains prohibited keywords.")
                return
        wiki_url = self.languages[self.current_language]["wiki_url"]
        url = wiki_url + topic.replace(" ", "_")
        try:
            response = requests.get(url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('h1').text
                paragraphs = soup.find_all('p')
                result = f"<h1 style='font-size:20pt; font-weight:bold;'>{title}</h1>\n\n"
                for para in paragraphs[:200]:
                    result += f"{para.text.strip()}\n\n"
                self.result_area.clear()
                self.writer = WriteTextEffect(result)
                self.writer.update_text.connect(self.append_text)
                self.writer.start()
            else:
                self.result_area.setText(f"No results found for '{topic}' in {self.current_language}.")
        except Exception as e:
            self.result_area.setText(f"Error fetching data: {str(e)}")

    def save_result(self):
        if not self.result_area.toPlainText():
            QMessageBox.warning(self, "Error", "No content to save!")
            return
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)", options=options)
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(self.result_area.toPlainText())
            QMessageBox.information(self, "Saved", "File saved successfully!")

    def append_text(self, line):
        self.result_area.moveCursor(QTextCursor.End)
        self.result_area.insertPlainText(line)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EduCollectorApp()
    window.show()
    sys.exit(app.exec_())
