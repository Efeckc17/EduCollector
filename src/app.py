import sys, requests
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLineEdit, QLabel, QComboBox, QMessageBox, QFileDialog, QMenuBar, QAction, QInputDialog, QApplication
from PyQt5.QtGui import QFont, QPixmap, QPainter, QRegion, QTextCursor, QDesktopServices
from PyQt5.QtCore import Qt, QUrl
from bs4 import BeautifulSoup
from dialogs import HistDlg, OfflineDlg
from widgets import ZoomTxt, TxtEff, AniBtn
import sqlite3
from database import init_db, load_user, record_search, save_article

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("EduCollector 1.2")
        self.setGeometry(100,100,1200,700)
        self.db = "educollector.db"
        init_db(self.db)
        self.user = load_user(self.db)
        self.langs = {
            "English": {"code": "en", "wiki_url": "https://en.wikipedia.org/wiki/", "labels": {"language_label": "Select Language:", "topic_label": "Enter a topic to search:", "search_button": "Search", "save_button": "Save Result", "copy_button": "Copy", "link_button": "Article Link", "exit_button": "Exit", "offline_button": "Offline Articles", "profile_title": "Profile", "chg_pic": "Change Picture", "chg_name": "Change Name", "history": "History"}},
            "Türkçe": {"code": "tr", "wiki_url": "https://tr.wikipedia.org/wiki/", "labels": {"language_label": "Dil Seçiniz:", "topic_label": "Araştırmak istediğiniz konuyu girin:", "search_button": "Araştır", "save_button": "Sonucu Kaydet", "copy_button": "Kopyala", "link_button": "Makale Linki", "exit_button": "Çıkış", "offline_button": "Offline Makale", "profile_title": "Profil", "chg_pic": "Resmi Değiştir", "chg_name": "İsmi Değiştir", "history": "Geçmiş"}},
            "Français": {"code": "fr", "wiki_url": "https://fr.wikipedia.org/wiki/", "labels": {"language_label": "Choisir la langue:", "topic_label": "Entrez un sujet à rechercher:", "search_button": "Rechercher", "save_button": "Enregistrer le résultat", "copy_button": "Copier", "link_button": "Lien de l'article", "exit_button": "Quitter", "offline_button": "Article Hors Ligne", "profile_title": "Profil", "chg_pic": "Changer d'image", "chg_name": "Changer de nom", "history": "Historique"}},
            "Deutsch": {"code": "de", "wiki_url": "https://de.wikipedia.org/wiki/", "labels": {"language_label": "Sprache auswählen:", "topic_label": "Geben Sie ein Thema zur Suche ein:", "search_button": "Suchen", "save_button": "Ergebnis speichern", "copy_button": "Kopieren", "link_button": "Artikellink", "exit_button": "Beenden", "offline_button": "Offline Artikel", "profile_title": "Profil", "chg_pic": "Bild ändern", "chg_name": "Namen ändern", "history": "Verlauf"}},
            "العربية": {"code": "ar", "wiki_url": "https://ar.wikipedia.org/wiki/", "labels": {"language_label": "اختر اللغة:", "topic_label": "أدخل موضوعًا للبحث:", "search_button": "بحث", "save_button": "احفظ النتيجة", "copy_button": "نسخ", "link_button": "رابط المقال", "exit_button": "خروج", "offline_button": "مقالات دون اتصال", "profile_title": "الملف الشخصي", "chg_pic": "تغيير الصورة", "chg_name": "تغيير الاسم", "history": "السجل"}}
        }
        self.blocked = {
            "en": ["racism", "hate", "violence", "discrimination", "homophobia"],
            "tr": ["ırkçılık", "nefret", "şiddet", "ayrımcılık", "homofobi"],
            "fr": ["racisme", "haine", "violence", "discrimination", "homophobie"],
            "de": ["rassismus", "hass", "gewalt", "diskriminierung", "homophobie"],
            "ar": ["العنصرية", "كراهية", "عنف", "تمييز", "رهاب المثلية"]
        }
        self.cur_lang = self.user['default_language'] if self.user['default_language'] in self.langs else "English"
        self.current_url = ""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.mk_menu()
        self.profile_widget = self.mk_profile_box()
        self.main_layout.addWidget(self.profile_widget, stretch=0)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20,20,20,20)
        self.content_layout.setSpacing(15)
        self.title_lbl = QLabel("EduCollector 1.2")
        self.title_lbl.setFont(QFont("Segoe UI",24,QFont.Bold))
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.title_lbl)
        hl = QHBoxLayout()
        self.lang_lbl = QLabel("Select Language:")
        self.lang_lbl.setFont(QFont("Segoe UI",11))
        self.lang_sel = QComboBox()
        self.lang_sel.setFont(QFont("Segoe UI",10))
        self.lang_sel.addItems(self.langs.keys())
        self.lang_sel.setCurrentText(self.cur_lang)
        self.lang_sel.currentIndexChanged.connect(self.upd_lang)
        hl.addWidget(self.lang_lbl)
        hl.addWidget(self.lang_sel)
        self.content_layout.addLayout(hl)
        self.topic_lbl = QLabel("Enter a topic to search:")
        self.topic_lbl.setFont(QFont("Segoe UI",12,QFont.Bold))
        self.content_layout.addWidget(self.topic_lbl)
        self.topic_inp = QLineEdit()
        self.topic_inp.setFont(QFont("Segoe UI",10))
        self.topic_inp.setPlaceholderText("Type your topic here...")
        self.content_layout.addWidget(self.topic_inp)
        btn_layout = QHBoxLayout()
        self.search_btn = AniBtn("Search")
        self.search_btn.clicked.connect(self.search)
        self.save_btn = AniBtn("Save Result")
        self.save_btn.clicked.connect(self.save_res)
        self.copy_btn = AniBtn("Copy")
        self.copy_btn.clicked.connect(self.copy_text)
        self.link_btn = AniBtn("Article Link")
        self.link_btn.clicked.connect(self.show_link)
        btn_layout.addWidget(self.search_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.copy_btn)
        btn_layout.addWidget(self.link_btn)
        self.content_layout.addLayout(btn_layout)
        self.result = ZoomTxt()
        self.result.setFont(QFont("Segoe UI",10))
        self.result.setReadOnly(True)
        self.content_layout.addWidget(self.result)
        self.main_layout.addWidget(self.content_widget, stretch=2)
        self.upd_lbl()
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
    def mk_profile_box(self):
        from PyQt5.QtWidgets import QGroupBox
        gb = QGroupBox(self.langs[self.cur_lang]["labels"]["profile_title"])
        gb.setFont(QFont("Segoe UI",10,QFont.Bold))
        layout = QVBoxLayout()
        layout.setContentsMargins(10,10,10,10)
        layout.setSpacing(10)
        self.profile_pic = QLabel()
        self.profile_pic.setAlignment(Qt.AlignCenter)
        self.profile_pic.setFixedSize(60,60)
        self.upd_pic()
        self.user_lbl = QLabel(self.user['name'])
        self.user_lbl.setFont(QFont("Segoe UI",10,QFont.Bold))
        self.user_lbl.setAlignment(Qt.AlignCenter)
        self.chg_pic_btn = AniBtn(self.langs[self.cur_lang]["labels"]["chg_pic"])
        self.chg_pic_btn.setFont(QFont("Segoe UI",9))
        self.chg_pic_btn.clicked.connect(self.chg_pic)
        self.chg_name_btn = AniBtn(self.langs[self.cur_lang]["labels"]["chg_name"])
        self.chg_name_btn.setFont(QFont("Segoe UI",9))
        self.chg_name_btn.clicked.connect(self.chg_name)
        self.hist_btn = AniBtn(self.langs[self.cur_lang]["labels"]["history"])
        self.hist_btn.setFont(QFont("Segoe UI",9))
        self.hist_btn.clicked.connect(self.hist)
        self.profile_offline_btn = AniBtn(self.langs[self.cur_lang]["labels"]["offline_button"])
        self.profile_offline_btn.setFont(QFont("Segoe UI",9))
        self.profile_offline_btn.clicked.connect(self.offline_articles)
        self.profile_exit_btn = AniBtn(self.langs[self.cur_lang]["labels"]["exit_button"])
        self.profile_exit_btn.setFont(QFont("Segoe UI",9))
        self.profile_exit_btn.clicked.connect(self.close)
        layout.addWidget(self.profile_pic, alignment=Qt.AlignCenter)
        layout.addWidget(self.user_lbl, alignment=Qt.AlignCenter)
        layout.addWidget(self.chg_pic_btn)
        layout.addWidget(self.chg_name_btn)
        layout.addWidget(self.hist_btn)
        layout.addWidget(self.profile_offline_btn)
        layout.addWidget(self.profile_exit_btn)
        layout.addStretch(1)
        gb.setLayout(layout)
        return gb
    def upd_pic(self):
        s = 60
        if self.user['profile_img']:
            p = QPixmap(self.user['profile_img'])
            if p.isNull():
                p = QPixmap(s,s)
                p.fill(Qt.gray)
            else:
                p = p.scaled(s,s,Qt.IgnoreAspectRatio,Qt.SmoothTransformation)
        else:
            p = QPixmap(s,s)
            p.fill(Qt.gray)
        f = QPixmap(s,s)
        f.fill(Qt.transparent)
        painter = QPainter(f)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setClipRegion(QRegion(0,0,s,s,QRegion.Ellipse))
        painter.drawPixmap(0,0,p)
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
        self.copy_btn.setText(lbls["copy_button"])
        self.link_btn.setText(lbls["link_button"])
        self.profile_exit_btn.setText(lbls["exit_button"])
        self.profile_offline_btn.setText(lbls["offline_button"])
        self.chg_pic_btn.setText(lbls["chg_pic"])
        self.chg_name_btn.setText(lbls["chg_name"])
        self.hist_btn.setText(lbls["history"])
        self.profile_widget.setTitle(lbls["profile_title"])
    def search(self):
        t = self.topic_inp.text().strip()
        if not t:
            QMessageBox.warning(self, "Warning", "Please enter a topic to search!")
            return
        lc = self.langs[self.cur_lang]["code"]
        for k in self.blocked.get(lc, []):
            if k.lower() in t.lower():
                QMessageBox.warning(self, "Blocked", "This topic contains prohibited keywords.")
                return
        record_search(self.db, t, lc)
        w = self.langs[self.cur_lang]["wiki_url"]
        url = w + t.replace(" ", "_")
        self.current_url = url
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
                save_article(self.db, t, res, url)
            else:
                self.result.setText(f"No results found for '{t}' in {self.cur_lang}.")
        except Exception as e:
            self.result.setText(f"Error fetching data: {str(e)}")
    def append_txt(self, line):
        self.result.moveCursor(QTextCursor.End)
        self.result.insertPlainText(line)
    def copy_text(self):
        txt = self.result.toPlainText()
        if txt:
            QApplication.clipboard().setText(txt)
            QMessageBox.information(self, "Copied", "Text copied to clipboard!")
        else:
            QMessageBox.warning(self, "Error", "No text to copy!")
    def show_link(self):
        if self.current_url:
            QDesktopServices.openUrl(QUrl(self.current_url))
        else:
            QMessageBox.warning(self, "Error", "No article link available!")
    def offline_articles(self):
        dlg = OfflineDlg(self.db, self)
        dlg.articleSelected.connect(self.load_offline_article)
        dlg.exec_()
    def load_offline_article(self, data):
        self.topic_inp.setText(data["topic"])
        self.result.clear()
        self.twriter = TxtEff(data["content"])
        self.twriter.update_text.connect(self.append_txt)
        self.twriter.start()
        self.current_url = data["url"]
    def closeEvent(self, e):
        reply = QMessageBox.question(self, "Exit", "Are you sure you want to exit?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            e.accept()
        else:
            e.ignore()
