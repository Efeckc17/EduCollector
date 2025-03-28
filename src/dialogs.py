import sqlite3
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView
from PyQt5.QtCore import QModelIndex, pyqtSignal

class HistDlg(QDialog):
    searchSelected = pyqtSignal(str)
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search History")
        self.setGeometry(300,200,600,400)
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
        t = self.table.item(r,1)
        if t:
            self.searchSelected.emit(t.text())
            self.close()

class OfflineDlg(QDialog):
    articleSelected = pyqtSignal(dict)
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Offline Makaleler")
        self.setGeometry(300,200,600,400)
        self.db = db
        lay = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Konu", "Tarih"])
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
        c.execute("SELECT id, topic, created_at FROM articles ORDER BY created_at DESC")
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
        id_item = self.table.item(r,0)
        if id_item:
            aid = id_item.text()
            conn = sqlite3.connect(self.db)
            c = conn.cursor()
            c.execute("SELECT topic, content, url FROM articles WHERE id=?", (aid,))
            row = c.fetchone()
            conn.close()
            if row:
                self.articleSelected.emit({"topic": row[0], "content": row[1], "url": row[2]})
                self.close()
