#!/usr/bin/env python

from PyQt5.QtCore import QDateTime, Qt, QTimer, QUrl, QAbstractTableModel, QVariant
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFormLayout, QCompleter, QMainWindow, QTableView, QMessageBox)
import webbrowser

import os
import pickle


cargoNames = ["г/к рулоны", "х/к рулоны", "слябы", "профиль", "арматура", "г/к лист", "Нарезка", "Полимер", "Трубы"]
zoneNames = []

DUMP_PATH = "cargo.pckl"

class DateBase():
    def __init__(self):
        self.rows = []
        if os.path.exists(DUMP_PATH):
            with open(DUMP_PATH, "rb") as f:
                self.rows = pickle.load(f)

    def add(self, id, name, count, zone):
        for row in self.rows:
            if row["name"] == name and row["zone"] == zone and row["id"] == id:
                row["count"] += count
                self.save()
                return

        self.rows.append({
            "id": id, 
            "name": name,
            "count": count,
            "zone": zone
        })
        self.save()

    def unload(self, id, zone, count):
        for row in self.rows:
            if row["zone"] == zone and row["id"] == id:
                row["count"] -= count

        self.sanitize()
        self.save()

    def sanitize(self):
        self.rows = list(filter(lambda x: x["count"] > 0, self.rows))

    def save(self):
        with open(DUMP_PATH, "wb") as f:
            pickle.dump(self.rows, f)


class MainLayout(QWidget):
    def __init__(self):
        super(MainLayout, self).__init__()

        self.createMenu()
        self.setLayout(self.menu)
        self.resize(400, 100)
        self.setWindowTitle("Main title");


    def createMenu(self):
        self.menu = QFormLayout()

        self.addButton = QPushButton("Добавить", self)
        self.addButton.clicked.connect(self.showAddLayout)

        self.unloadButton = QPushButton("Выгрузить", self)
        self.unloadButton.clicked.connect(self.showFindLayout)

        self.listButton = QPushButton("Наличие", self)
        self.listButton.clicked.connect(self.showCargoListLayout)

        self.cargoCountInput = QSpinBox()

        self.menu.addRow(self.addButton)
        self.menu.addRow(self.unloadButton)
        self.menu.addRow(self.listButton)


    def setAddCargoLayout(self, addLayout):
        self.addLayout = addLayout

    def showAddLayout(self):
        self.addLayout.show()
        self.hide()

    def setFindCargoLayout(self, findLayout):
        self.findLayout = findLayout

    def showFindLayout(self):
        self.findLayout.show()
        self.hide()

    def setCargoListLayout(self, cargoListLayout):
        self.cargoListLayout = cargoListLayout

    def showCargoListLayout(self):
        self.cargoListLayout.reloadTable()
        self.cargoListLayout.show()


ZONE_ROWS_COUNT = 3

class AddCargoLayout(QWidget):
    def __init__(self, db, mainLayout):
        super(AddCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout

        self.createInputForm()
        self.setLayout(self.inputForm)
        self.resize(400, 100)
        self.setWindowTitle("Add cargo title");


    def createInputForm(self):
        self.inputForm = QFormLayout()

        self.idInput =  QLineEdit()

        namesCompleter = QCompleter(cargoNames)
        namesCompleter.setCaseSensitivity(False)
        self.nameInput = QLineEdit()
        self.nameInput.setCompleter(namesCompleter)

        self.addButton = QPushButton("Добавить", self)
        self.addButton.clicked.connect(self.addCargo)

        self.backButton = QPushButton("Назад", self)
        self.backButton.clicked.connect(self.goBack)

        self.inputForm.addRow("Приёмный акт:", self.idInput)
        self.inputForm.addRow("Груз:", self.nameInput)

        self.zonesInput = []
        self.cargosCountInput = []

        for i in range(ZONE_ROWS_COUNT):

            self.zonesInput.append(QLineEdit())

            self.cargosCountInput.append(QSpinBox())
            self.cargosCountInput[-1].setMaximum(100000000)


            self.inputForm.addRow(QLabel(""), QLabel(""))
            self.inputForm.addRow("Зона {}:".format(i + 1), self.zonesInput[-1])
            self.inputForm.addRow("Кол-во:", self.cargosCountInput[-1])

        self.inputForm.addRow(self.addButton)
        self.inputForm.addRow(self.backButton)


    def addCargo(self):
        for i in range(ZONE_ROWS_COUNT):
            if self.zonesInput[i].text():
                self.db.add(
                    self.idInput.text(),
                    self.nameInput.text(),
                    int(self.cargosCountInput[i].text()),
                    self.zonesInput[i].text())

        self.goBack()

    def goBack(self):
        self.mainLayout.show()
        self.close()


class UnloadCargoLayout(QDialog):
    def __init__(self, db, mainLayout, entries):
        super(UnloadCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout
        self.entries = entries

        self.resize(400, 100);
        self.createMap()
        self.createFindResult()
        self.setLayout(self.resultForm)
        self.setWindowTitle("Upload title");


    def link(self, linkStr):
        webbrowser.open_new_tab(linkStr)


    def createMap(self):
        zones = []
        for entry in self.entries:
            zones.append(entry["zone"])

        map_html = None
        with open("map_template.html") as f:
            map_html = f.read()

        map_html = map_html.replace("%zones", str(zones).replace("'", '"'))

        with open("cargo.geojson") as f:
            map_html = map_html.replace("%geojson", f.read().replace("'", '"'))

        with open("map.html", "w") as f:
            f.write(map_html)


    def createFindResult(self):
        self.resultForm = QGridLayout()

        mapLink = QLabel("Карта")
        mapLink.linkActivated.connect(self.link)

        mapLink.setText('<a href="file://{}">Карта</a>'.format(os.path.join(os.getcwdb().decode("utf-8") , "map.html")))

        self.cancleButton = QPushButton("Отмена", self)
        self.cancleButton.clicked.connect(self.closeWidget)

        self.resultForm.addWidget(mapLink)

        i = 1
        self.unloadCounts = []

        for entry in self.entries:
            zoneLabel = QLabel(entry["zone"])
            countLabel = QLabel(str(entry["count"]))

            unloadCountInput = QSpinBox()
            unloadCountInput.setMaximum(entry["count"])

            self.unloadCounts.append(unloadCountInput)

            self.resultForm.addWidget(zoneLabel, i, 0)
            self.resultForm.addWidget(countLabel, i, 1)
            self.resultForm.addWidget(unloadCountInput, i, 2)

            i += 1


        self.unloadButton = QPushButton("Выгрузить", self)
        self.unloadButton.clicked.connect(self.unload)

        self.resultForm.addWidget(self.unloadButton)
        self.resultForm.addWidget(self.cancleButton)


    def closeWidget(self):
        self.mainLayout.show()
        self.close()


    def unload(self):
        for entry, countBox in zip(self.entries, self.unloadCounts):
            count = int(countBox.text())
            if count == 0:
                continue

            self.db.unload(entry["id"], entry["zone"], count)

        self.closeWidget()


class FindCargoLayout(QWidget):
    def __init__(self, db, mainLayout):
        super(FindCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout

        self.createInputForm()
        self.setLayout(self.inputForm)
        self.setWindowTitle("Find cargo title")
        self.resize(400, 100);


    def createInputForm(self):
        self.inputForm = QFormLayout()

        self.idInput =  QLineEdit()

        self.findButton = QPushButton("Найти", self)
        self.findButton.clicked.connect(self.findCargo)

        self.backButton = QPushButton("Назад", self)
        self.backButton.clicked.connect(self.goBack)

        self.inputForm.addRow("Приёмный акт:", self.idInput)

        self.inputForm.addRow(self.findButton)
        self.inputForm.addRow(self.backButton)


    def findCargo(self):
        entries = []

        for row in self.db.rows:
            if row["id"] == self.idInput.text():
                entries.append({
                    "zone" : row["zone"],
                    "count" : row["count"],
                    "id": row["id"]
                    })

        if not entries:
            self.notFound()
            return

        unloadLayout = UnloadCargoLayout(self.db, self.mainLayout, entries)
        unloadLayout.exec()
        self.close()

    def notFound(self):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Information)
        msgBox.setText("Приёмный акт не найден")
        msgBox.setStandardButtons(QMessageBox.Ok)

        msgBox.exec()

    def goBack(self):
        self.mainLayout.show()
        self.close()


class TableModel(QAbstractTableModel):
    def __init__(self, db):
        super(TableModel, self).__init__()
        self.db = db
        self.headers = ["Приёмный акт", "Груз", "Кол-во", "Зона"]
        self.column_keys = ["id", "name", "count", "zone"]

    def rowCount(self, parent):
        return len(self.db.rows)

    def columnCount(self, parent):
        return len(self.headers)

    def data(self, index, role):
        if role != Qt.DisplayRole:
            return QVariant()
        return self.db.rows[index.row()][self.column_keys[index.column()]]

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole or orientation != Qt.Horizontal:
            return QVariant()
        return self.headers[section]


class ListCargoLayout(QTableView):
    def __init__(self, db, mainLayout):
        super(ListCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout

        self.resize(400, 200);
        self.reloadTable()
        self.setWindowTitle("List cargo title");

    def reloadTable(self):
        model = TableModel(db)
        self.setModel(model)


if __name__ == '__main__':

    import sys

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    db = DateBase()

    app = QApplication(sys.argv)

    mainLayout = MainLayout()

    addCargoLayout = AddCargoLayout(db, mainLayout)
    mainLayout.setAddCargoLayout(addCargoLayout)

    findCargoLayout = FindCargoLayout(db, mainLayout)
    mainLayout.setFindCargoLayout(findCargoLayout)

    listLayout = ListCargoLayout(db, mainLayout)
    mainLayout.setCargoListLayout(listLayout)

    mainLayout.show()

    sys.exit(app.exec_()) 
