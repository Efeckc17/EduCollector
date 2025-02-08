import sys
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QTextEdit, QLabel, QComboBox, QMessageBox, QFileDialog, QMenuBar, QAction, QDialog, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QPushButton, QGroupBox, QInputDialog
from PyQt5.QtGui import QFont, QTextCursor, QPixmap, QPainter, QRegion
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QModelIndex

class WriteTextEffect(QThread):
    update_text = pyqtSignal(str)
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.text = text
    def run(self):
        for line in self.text.split('\n'):
            self.update_text.emit(line + "\n")
            time.sleep(0.05)

class AnimatedButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7b1fa2, stop:1 #512da8);
                color: #ffffff;
                border: none;
                border-radius: 5px;
                padding: 8px 14px;
            }
            QPushButton:hover {
                background-color: #9575cd;
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
        self.animation.setEndValue(QRect(rect.x() - 3, rect.y() - 3, rect.width() + 6, rect.height() + 6))
        self.animation.setDuration(150)
        self.animation.start()
        super().enterEvent(event)
    def leaveEvent(self, event):
        self.animation.stop()
        rect = self.default_geometry
        self.animation.setStartValue(self.geometry())
        self.animation.setEndValue(rect)
        self.animation.setDuration(150)
        self.animation.start()
        super().leaveEvent(event)

class HistoryDialog(QDialog):
    searchSelected = pyqtSignal(str)
    def __init__(self, db_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search History")
        self.setGeometry(300, 200, 600, 400)
        self.db_path = db_path
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Topic", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(self.on_double_click)
        layout.addWidget(self.table)
        self.load_history()
    def load_history(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, topic, created_at FROM history ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        self.table.setRowCount(0)
        for i, row in enumerate(rows):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QTableWidgetItem(row[1]))
            self.table.setItem(i, 2, QTableWidgetItem(row[2]))
    def on_double_click(self, index: QModelIndex):
        row = index.row()
        topic_item = self.table.item(row, 1)
        if topic_item:
            self.searchSelected.emit(topic_item.text())
            self.close()

class EduCollectorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduCollector 1.1")
        self.setGeometry(100, 100, 1200, 700)
        self.db_path = "educollector.db"
        self.init_database()
        self.user_data = self.load_user_data()
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
                    "save_button": "احفظ nتيجة",
                    "exit_button": "خروج"
                }
            }
        }
        self.blocked_keywords = {
            "en": ["racism", "hate", "violence", "discrimination", "homophobia"],
            "tr": ["ırkçılık", "nefret", "şiddet", "ayrımcılık", "homofobi"],
            "fr": ["racisme", "haine", "violence", "discrimination", "homophobie"],
            "de": ["rassismus", "hass", "gewalt", "diskriminierung", "homophobie"],
            "ar": ["العنصرية", "كراهية", "عنف", "تمييز", "رهاب المثلية"]
        }
        self.current_language = self.user_data['default_language'] if self.user_data['default_language'] in self.languages else "English"
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #121212, stop:1 #1b1b1b);
            }
            QLabel {
                color: #ffffff;
            }
            QLineEdit, QComboBox, QTextEdit {
                color: #ffffff;
                background-color: #2e2e2e;
                border: 1px solid #777;
                border-radius: 5px;
                padding: 6px;
            }
            QLineEdit:focus, QTextEdit:focus {
                border: 1px solid #7b1fa2;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 6px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
            QMenuBar {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QMenuBar::item {
                background-color: #2a2a2a;
                padding: 5px 10px;
            }
            QMenuBar::item:selected {
                background-color: #512da8;
            }
            QMenu {
                background-color: #2a2a2a;
                color: #ffffff;
            }
            QMenu::item:selected {
                background-color: #512da8;
            }
        """)
        self.create_menubar()
        self.profile_widget = self.create_profile_box()
        self.main_layout.addWidget(self.profile_widget, stretch=0)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(15)
        self.title_label = QLabel("EduCollector 1.1")
        self.title_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.title_label)
        lang_layout = QHBoxLayout()
        self.language_label = QLabel("Select Language:")
        self.language_label.setFont(QFont("Segoe UI", 11))
        self.language_selector = QComboBox()
        self.language_selector.setFont(QFont("Segoe UI", 10))
        self.language_selector.addItems(self.languages.keys())
        self.language_selector.setCurrentText(self.current_language)
        self.language_selector.currentIndexChanged.connect(self.update_language)
        lang_layout.addWidget(self.language_label)
        lang_layout.addWidget(self.language_selector)
        self.content_layout.addLayout(lang_layout)
        self.topic_label = QLabel("Enter a topic to search:")
        self.topic_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.content_layout.addWidget(self.topic_label)
        self.topic_input = QLineEdit()
        self.topic_input.setFont(QFont("Segoe UI", 10))
        self.topic_input.setPlaceholderText("Type your topic here...")
        self.content_layout.addWidget(self.topic_input)
        btn_layout = QHBoxLayout()
        self.search_button = AnimatedButton("Search")
        self.search_button.clicked.connect(self.search_topic)
        self.save_button = AnimatedButton("Save Result")
        self.save_button.clicked.connect(self.save_result)
        self.exit_button = AnimatedButton("Exit")
        self.exit_button.clicked.connect(self.close)
        btn_layout.addWidget(self.search_button)
        btn_layout.addWidget(self.save_button)
        btn_layout.addWidget(self.exit_button)
        self.content_layout.addLayout(btn_layout)
        self.result_area = QTextEdit()
        self.result_area.setFont(QFont("Segoe UI", 10))
        self.result_area.setReadOnly(True)
        self.content_layout.addWidget(self.result_area)
        self.main_layout.addWidget(self.content_widget, stretch=2)
        self.update_language_labels()

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT DEFAULT 'User', profile_img TEXT, default_language TEXT DEFAULT 'English')")
        c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, language TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        c.execute("SELECT COUNT(*) FROM user")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO user (name, profile_img, default_language) VALUES (?, ?, ?)", ("User", "", "English"))
            conn.commit()
        conn.close()

    def load_user_data(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT id, name, profile_img, default_language FROM user LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "profile_img": row[2] or "", "default_language": row[3] or "English"}
        return {"id": None, "name": "User", "profile_img": "", "default_language": "English"}

    def record_search(self, topic):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        lang_code = self.languages[self.current_language]["code"]
        c.execute("INSERT INTO history (topic, language) VALUES (?, ?)", (topic, lang_code))
        conn.commit()
        conn.close()

    def create_profile_box(self):
        box = QGroupBox("Profile")
        box.setFont(QFont("Segoe UI", 10, QFont.Bold))
        box_lay = QVBoxLayout()
        box_lay.setContentsMargins(10, 10, 10, 10)
        box_lay.setSpacing(10)
        self.profile_pic_label = QLabel()
        self.profile_pic_label.setAlignment(Qt.AlignCenter)
        self.profile_pic_label.setFixedSize(60, 60)
        self.update_profile_picture()
        self.user_name_label = QLabel(self.user_data['name'])
        self.user_name_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.user_name_label.setAlignment(Qt.AlignCenter)
        self.change_pic_button = AnimatedButton("Change Picture")
        self.change_pic_button.setFont(QFont("Segoe UI", 9))
        self.change_pic_button.clicked.connect(self.change_profile_picture)
        self.change_name_button = AnimatedButton("Change Name")
        self.change_name_button.setFont(QFont("Segoe UI", 9))
        self.change_name_button.clicked.connect(self.change_user_name)
        box_lay.addWidget(self.profile_pic_label, alignment=Qt.AlignCenter)
        box_lay.addWidget(self.user_name_label, alignment=Qt.AlignCenter)
        box_lay.addWidget(self.change_pic_button)
        box_lay.addWidget(self.change_name_button)
        box_lay.addStretch(1)
        box.setLayout(box_lay)
        return box

    def update_profile_picture(self):
        size = 60
        if self.user_data['profile_img']:
            pix = QPixmap(self.user_data['profile_img'])
            if pix.isNull():
                pix = QPixmap(size, size)
                pix.fill(Qt.gray)
            else:
                pix = pix.scaled(size, size, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        else:
            pix = QPixmap(size, size)
            pix.fill(Qt.gray)
        final_pix = QPixmap(size, size)
        final_pix.fill(Qt.transparent)
        p = QPainter(final_pix)
        p.setRenderHint(QPainter.Antialiasing)
        p.setClipRegion(QRegion(0, 0, size, size, QRegion.Ellipse))
        p.drawPixmap(0, 0, pix)
        p.end()
        self.profile_pic_label.setPixmap(final_pix)

    def change_profile_picture(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE user SET profile_img=? WHERE id=?", (file_path, self.user_data['id']))
            conn.commit()
            conn.close()
            self.user_data['profile_img'] = file_path
            self.update_profile_picture()

    def change_user_name(self):
        new_name, ok = QInputDialog.getText(self, "Change User Name", "Enter new user name:", text=self.user_data['name'])
        if ok and new_name.strip():
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("UPDATE user SET name=? WHERE id=?", (new_name.strip(), self.user_data['id']))
            conn.commit()
            conn.close()
            self.user_data['name'] = new_name.strip()
            self.user_name_label.setText(new_name.strip())

    def create_menubar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        new_search_action = QAction("New Search", self)
        new_search_action.setShortcut("Ctrl+N")
        new_search_action.triggered.connect(self.new_search)
        file_menu.addAction(new_search_action)
        save_action = QAction("Save Result", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_result)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        tools_menu = menubar.addMenu("Tools")
        history_action = QAction("History", self)
        history_action.triggered.connect(self.show_history)
        tools_menu.addAction(history_action)
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About EduCollector", self)
        about_action.triggered.connect(self.about_app)
        help_menu.addAction(about_action)

    def new_search(self):
        self.topic_input.clear()
        self.result_area.clear()

    def save_result(self):
        if not self.result_area.toPlainText():
            QMessageBox.warning(self, "Error", "No content to save!")
            return
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.result_area.toPlainText())
            QMessageBox.information(self, "Saved", "File saved successfully!")

    def show_history(self):
        dlg = HistoryDialog(self.db_path, self)
        dlg.searchSelected.connect(self.on_history_search_selected)
        dlg.exec_()

    def on_history_search_selected(self, topic):
        self.topic_input.setText(topic)
        self.search_topic()

    def about_app(self):
        QMessageBox.information(self, "About EduCollector", "For help: toxi360@workmail.com")

    def update_language(self):
        self.current_language = self.language_selector.currentText()
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE user SET default_language=? WHERE id=?", (self.current_language, self.user_data['id']))
        conn.commit()
        conn.close()
        self.update_language_labels()

    def update_language_labels(self):
        labels = self.languages[self.current_language]["labels"]
        self.language_label.setText(labels["language_label"])
        self.topic_label.setText(labels["topic_label"])
        self.search_button.setText(labels["search_button"])
        self.save_button.setText(labels["save_button"])
        self.exit_button.setText(labels["exit_button"])

    def search_topic(self):
        topic = self.topic_input.text().strip()
        if not topic:
            QMessageBox.warning(self, "Warning", "Please enter a topic to search!")
            return
        lang_code = self.languages[self.current_language]["code"]
        current_keywords = self.blocked_keywords.get(lang_code, [])
        for keyword in current_keywords:
            if keyword.lower() in topic.lower():
                QMessageBox.warning(self, "Blocked", "This topic contains prohibited keywords.")
                return
        self.record_search(topic)
        wiki_url = self.languages[self.current_language]["wiki_url"]
        url = wiki_url + topic.replace(" ", "_")
        try:
            r = requests.get(url)
            if r.status_code == 200:
                s = BeautifulSoup(r.text, 'html.parser')
                t = s.find('h1').text
                p = s.find_all('p')
                result = f"<h1 style='font-size:16pt; font-weight:bold;'>{t}</h1>\n\n"
                for para in p[:200]:
                    x = para.get_text(strip=True)
                    if x:
                        result += f"{x}\n\n"
                self.result_area.clear()
                self.writer = WriteTextEffect(result)
                self.writer.update_text.connect(self.append_text)
                self.writer.start()
            else:
                self.result_area.setText(f"No results found for '{topic}' in {self.current_language}.")
        except Exception as e:
            self.result_area.setText(f"Error fetching data: {str(e)}")

    def append_text(self, line):
        self.result_area.moveCursor(QTextCursor.End)
        self.result_area.insertPlainText(line)

    def closeEvent(self, event):
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = EduCollectorApp()
    w.show()
    sys.exit(app.exec_())
