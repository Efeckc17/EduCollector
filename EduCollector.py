import sys
import time
import sqlite3
import requests
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QComboBox, QMessageBox, QFileDialog, QMenuBar, QAction, QDialog, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView, QPushButton, QGroupBox, QInputDialog
from PyQt5.QtGui import QFont, QTextCursor, QPixmap, QPainter, QRegion, QTextDocument
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QRect, QModelIndex
from PyQt5.QtWidgets import QTextEdit

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
        self.anim = QPropertyAnimation(self, b"geometry")
    def enterEvent(self, e):
        if self.default_geometry is None:
            self.default_geometry = self.geometry()
        self.anim.stop()
        r = self.default_geometry
        self.anim.setStartValue(r)
        self.anim.setEndValue(QRect(r.x() - 3, r.y() - 3, r.width() + 6, r.height() + 6))
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

class HistDlg(QDialog):
    searchSelected = pyqtSignal(str)
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search History")
        self.setGeometry(300, 200, 600, 400)
        self.db = db
        lay = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Topic", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.doubleClicked.connect(self.on_dbl)
        lay.addWidget(self.table)
        self.load()
    def load(self):
        conn = sqlite3.connect(self.db)
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
    def on_dbl(self, idx: QModelIndex):
        r = idx.row()
        t = self.table.item(r, 1)
        if t:
            self.searchSelected.emit(t.text())
            self.close()

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduCollector 1.1")
        self.setGeometry(100, 100, 1200, 700)
        self.db = "educollector.db"
        self.db_init()
        self.user = self.load_data()
        self.langs = {
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
        self.blocked = {
            "en": ["racism", "hate", "violence", "discrimination", "homophobia"],
            "tr": ["ırkçılık", "nefret", "şiddet", "ayrımcılık", "homofobi"],
            "fr": ["racisme", "haine", "violence", "discrimination", "homophobie"],
            "de": ["rassismus", "hass", "gewalt", "diskriminierung", "homophobie"],
            "ar": ["العنصرية", "كراهية", "عنف", "تمييز", "رهاب المثلية"]
        }
        self.cur_lang = self.user['default_language'] if self.user['default_language'] in self.langs else "English"
        self.cw = QWidget()
        self.setCentralWidget(self.cw)
        self.ml = QHBoxLayout(self.cw)
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
        self.mk_menu()
        self.pw = self.mk_profile_box()
        self.ml.addWidget(self.pw, stretch=0)
        self.cnt_w = QWidget()
        self.cnt_l = QVBoxLayout(self.cnt_w)
        self.cnt_l.setContentsMargins(20, 20, 20, 20)
        self.cnt_l.setSpacing(15)
        self.title_lbl = QLabel("EduCollector 1.1")
        self.title_lbl.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.cnt_l.addWidget(self.title_lbl)
        hl = QHBoxLayout()
        self.lang_lbl = QLabel("Select Language:")
        self.lang_lbl.setFont(QFont("Segoe UI", 11))
        self.lang_sel = QComboBox()
        self.lang_sel.setFont(QFont("Segoe UI", 10))
        self.lang_sel.addItems(self.langs.keys())
        self.lang_sel.setCurrentText(self.cur_lang)
        self.lang_sel.currentIndexChanged.connect(self.upd_lang)
        hl.addWidget(self.lang_lbl)
        hl.addWidget(self.lang_sel)
        self.cnt_l.addLayout(hl)
        self.topic_lbl = QLabel("Enter a topic to search:")
        self.topic_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.cnt_l.addWidget(self.topic_lbl)
        self.topic_inp = QLineEdit()
        self.topic_inp.setFont(QFont("Segoe UI", 10))
        self.topic_inp.setPlaceholderText("Type your topic here...")
        self.cnt_l.addWidget(self.topic_inp)
        hbl = QHBoxLayout()
        self.search_btn = AniBtn("Search")
        self.search_btn.clicked.connect(self.search)
        self.save_btn = AniBtn("Save Result")
        self.save_btn.clicked.connect(self.save_res)
        self.exit_btn = AniBtn("Exit")
        self.exit_btn.clicked.connect(self.close)
        hbl.addWidget(self.search_btn)
        hbl.addWidget(self.save_btn)
        hbl.addWidget(self.exit_btn)
        self.cnt_l.addLayout(hbl)
        self.result = ZoomTxt()
        self.result.setFont(QFont("Segoe UI", 10))
        self.result.setReadOnly(True)
        self.cnt_l.addWidget(self.result)
        self.ml.addWidget(self.cnt_w, stretch=2)
        self.upd_lbl()

    def db_init(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT DEFAULT 'User', profile_img TEXT, default_language TEXT DEFAULT 'English')")
        c.execute("CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, topic TEXT, language TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP)")
        c.execute("SELECT COUNT(*) FROM user")
        if c.fetchone()[0] == 0:
            c.execute("INSERT INTO user (name, profile_img, default_language) VALUES (?, ?, ?)", ("User", "", "English"))
            conn.commit()
        conn.close()

    def load_data(self):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("SELECT id, name, profile_img, default_language FROM user LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return {"id": row[0], "name": row[1], "profile_img": row[2] or "", "default_language": row[3] or "English"}
        return {"id": None, "name": "User", "profile_img": "", "default_language": "English"}

    def rec_search(self, t):
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        lc = self.langs[self.cur_lang]["code"]
        c.execute("INSERT INTO history (topic, language) VALUES (?, ?)", (t, lc))
        conn.commit()
        conn.close()

    def mk_profile_box(self):
        b = QGroupBox("Profile")
        b.setFont(QFont("Segoe UI", 10, QFont.Bold))
        bl = QVBoxLayout()
        bl.setContentsMargins(10, 10, 10, 10)
        bl.setSpacing(10)
        self.profile_pic = QLabel()
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.profile_pic.setFixedSize(60, 60)
        self.upd_pic()
        self.user_lbl = QLabel(self.user['name'])
        self.user_lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.user_lbl.setAlignment(Qt.AlignCenter)
        self.chg_pic_btn = AniBtn("Change Picture")
        self.chg_pic_btn.setFont(QFont("Segoe UI", 9))
        self.chg_pic_btn.clicked.connect(self.chg_pic)
        self.chg_name_btn = AniBtn("Change Name")
        self.chg_name_btn.setFont(QFont("Segoe UI", 9))
        self.chg_name_btn.clicked.connect(self.chg_name)
        self.hist_btn = AniBtn("History")
        self.hist_btn.setFont(QFont("Segoe UI", 9))
        self.hist_btn.clicked.connect(self.hist)
        bl.addWidget(self.profile_pic, alignment=Qt.AlignCenter)
        bl.addWidget(self.user_lbl, alignment=Qt.AlignCenter)
        bl.addWidget(self.chg_pic_btn)
        bl.addWidget(self.chg_name_btn)
        bl.addWidget(self.hist_btn)
        bl.addStretch(1)
        b.setLayout(bl)
        return b

    def upd_pic(self):
        s = 60
        if self.user['profile_img']:
            p = QPixmap(self.user['profile_img'])
            if p.isNull():
                p = QPixmap(s, s)
                p.fill(Qt.gray)
            else:
                p = p.scaled(s, s, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        else:
            p = QPixmap(s, s)
            p.fill(Qt.gray)
        f = QPixmap(s, s)
        f.fill(Qt.transparent)
        painter = QPainter(f)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRegion(QRegion(0, 0, s, s, QRegion.Ellipse))
        painter.drawPixmap(0, 0, p)
        painter.end()
        self.profile_pic.setPixmap(f)

    def chg_pic(self):
        fp, _ = QFileDialog.getOpenFileName(self, "Select Profile Picture", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if fp:
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute("UPDATE user SET profile_img=? WHERE id=?", (fp, self.user['id']))
            conn.commit()
            conn.close()
            self.user['profile_img'] = fp
            self.upd_pic()

    def chg_name(self):
        new_name, ok = QInputDialog.getText(self, "Change User Name", "Enter new user name:", text=self.user['name'])
        if ok and new_name.strip():
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute("UPDATE user SET name=? WHERE id=?", (new_name.strip(), self.user['id']))
            conn.commit()
            conn.close()
            self.user['name'] = new_name.strip()
            self.user_lbl.setText(new_name.strip())

    def mk_menu(self):
        mb = self.menuBar()
        fmenu = mb.addMenu("File")
        ns = QAction("New Search", self)
        ns.setShortcut("Ctrl+N")
        ns.triggered.connect(self.new_search)
        fmenu.addAction(ns)
        sv = QAction("Save Result", self)
        sv.setShortcut("Ctrl+S")
        sv.triggered.connect(self.save_res)
        fmenu.addAction(sv)
        fmenu.addSeparator()
        ex = QAction("Exit", self)
        ex.setShortcut("Ctrl+Q")
        ex.triggered.connect(self.close)
        fmenu.addAction(ex)
        help_menu = mb.addMenu("Help")
        ab = QAction("About EduCollector", self)
        ab.triggered.connect(self.about)
        help_menu.addAction(ab)

    def new_search(self):
        self.topic_inp.clear()
        self.result.clear()

    def save_res(self):
        if not self.result.toPlainText():
            QMessageBox.warning(self, "Error", "No content to save!")
            return
        fp, _ = QFileDialog.getSaveFileName(self, "Save File", "", "Text Files (*.txt);;All Files (*)")
        if fp:
            with open(fp, 'w', encoding='utf-8') as f:
                f.write(self.result.toPlainText())
            QMessageBox.information(self, "Saved", "File saved successfully!")

    def hist(self):
        dlg = HistDlg(self.db, self)
        dlg.searchSelected.connect(self.hist_sel)
        dlg.exec_()

    def hist_sel(self, t):
        self.topic_inp.setText(t)
        self.search()

    def about(self):
        QMessageBox.information(self, "About EduCollector", "For help: toxi360@workmail.com")

    def upd_lang(self):
        self.cur_lang = self.lang_sel.currentText()
        conn = sqlite3.connect(self.db)
        c = conn.cursor()
        c.execute("UPDATE user SET default_language=? WHERE id=?", (self.cur_lang, self.user['id']))
        conn.commit()
        conn.close()
        self.upd_lbl()

    def upd_lbl(self):
        lbls = self.langs[self.cur_lang]["labels"]
        self.lang_lbl.setText(lbls["language_label"])
        self.topic_lbl.setText(lbls["topic_label"])
        self.search_btn.setText(lbls["search_button"])
        self.save_btn.setText(lbls["save_button"])
        self.exit_btn.setText(lbls["exit_button"])

    def search(self):
        t = self.topic_inp.text().strip()
        if not t:
            QMessageBox.warning(self, "Warning", "Please enter a topic to search!")
            return
        lc = self.langs[self.cur_lang]["code"]
        cur_b = self.blocked.get(lc, [])
        for k in cur_b:
            if k.lower() in t.lower():
                QMessageBox.warning(self, "Blocked", "This topic contains prohibited keywords.")
                return
        self.rec_search(t)
        w = self.langs[self.cur_lang]["wiki_url"]
        url = w + t.replace(" ", "_")
        try:
            r = requests.get(url)
            if r.status_code == 200:
                s = BeautifulSoup(r.text, 'html.parser')
                head = s.find('h1').text
                pars = s.find_all('p')
                res = f"<h1 style='font-size:16pt; font-weight:bold;'>{head}</h1>\n\n"
                for par in pars[:200]:
                    x = par.get_text(strip=True)
                    if x:
                        res += f"{x}\n\n"
                self.result.clear()
                self.twriter = TxtEff(res)
                self.twriter.update_text.connect(self.append_txt)
                self.twriter.start()
            else:
                self.result.setText(f"No results found for '{t}' in {self.cur_lang}.")
        except Exception as e:
            self.result.setText(f"Error fetching data: {str(e)}")

    def append_txt(self, line):
        self.result.moveCursor(QTextCursor.End)
        self.result.insertPlainText(line)

    def closeEvent(self, e):
        e.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainApp()
    w.show()
    sys.exit(app.exec_())
