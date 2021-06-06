#!/usr/bin/env python

from PyQt5.QtCore import QDateTime, Qt, QTimer, QUrl, QAbstractTableModel, QVariant
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateTimeEdit,
        QDial, QDialog, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit,
        QProgressBar, QPushButton, QRadioButton, QScrollBar, QSizePolicy,
        QSlider, QSpinBox, QStyleFactory, QTableWidget, QTabWidget, QTextEdit,
        QVBoxLayout, QWidget, QFormLayout, QCompleter, QMainWindow, QTableView)

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

    def add(self, name, count, zone):
        self.rows.append({
            "name": name,
            "count": count,
            "zone": zone
        })
        self.save()

    def unload(self, zone, count):
        for row in self.rows:
            if row["zone"] == zone:
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
        self.cargoListLayout.show()


class AddCargoLayout(QWidget):
    def __init__(self, db, mainLayout):
        super(AddCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout

        self.createInputForm()
        self.setLayout(self.inputForm)


    def createInputForm(self):
        self.inputForm = QFormLayout()

        namesCompleter = QCompleter(cargoNames)
        namesCompleter.setCaseSensitivity(False)
        self.nameInput =  QLineEdit()
        self.nameInput.setCompleter(namesCompleter)

        self.zoneInput =  QLineEdit()

        self.addButton = QPushButton("Добавить", self)
        self.addButton.clicked.connect(self.addCargo)

        self.cargoCountInput = QSpinBox()

        self.inputForm.addRow("Груз:", self.nameInput)
        self.inputForm.addRow("Кол-во:", self.cargoCountInput)
        self.inputForm.addRow("Зона:", self.zoneInput)
        self.inputForm.addRow(self.addButton)


    def addCargo(self):
        self.db.add(
            self.nameInput.text(),
            int(self.cargoCountInput.text()),
            self.zoneInput.text())

        self.mainLayout.show()
        self.close()


class UnloadCargoLayout(QDialog):
    def __init__(self, db, mainLayout, entries):
        super(UnloadCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout
        self.entries = entries

        self.createMap()
        self.createFindResult()
        self.setLayout(self.resultForm)


    def link(self, linkStr):
        QDesktopServices.openUrl(QUrl(linkStr))


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

            self.db.unload(entry["zone"], count)

        self.closeWidget()


class FindCargoLayout(QWidget):
    def __init__(self, db, mainLayout):
        super(FindCargoLayout, self).__init__()
        self.db = db
        self.mainLayout = mainLayout

        self.createInputForm()
        self.setLayout(self.inputForm)


    def createInputForm(self):
        self.inputForm = QFormLayout()

        namesCompleter = QCompleter(cargoNames)
        namesCompleter.setCaseSensitivity(False)
        self.nameInput =  QLineEdit()
        self.nameInput.setCompleter(namesCompleter)

        self.findButton = QPushButton("Найти", self)
        self.findButton.clicked.connect(self.findCargo)

        self.inputForm.addRow("Груз:", self.nameInput)
        self.inputForm.addRow(self.findButton)


    def findCargo(self):
        entries = []

        for row in self.db.rows:
            if row["name"] == self.nameInput.text():
                entries.append({
                    "zone" : row["zone"],
                    "count" : row["count"]
                    })

        unloadLayout = UnloadCargoLayout(self.db, self.mainLayout, entries)
        unloadLayout.exec()
        self.close()


class TableModel(QAbstractTableModel):
    def __init__(self, db):
        super(TableModel, self).__init__()
        self.db = db
        self.headers = ["Груз", "Кол-во", "Зона"]
        self.column_keys = ["name", "count", "zone"]

    def rowCount(self, parent):
        return len(self.db.rows)

    def columnCount(self, parent):
        return 3

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

        model = TableModel(db)
        self.setModel(model)


    # def createTable(self):
    #     self.table = TableModel(self)

    #     namesCompleter = QCompleter(cargoNames)
    #     namesCompleter.setCaseSensitivity(False)
    #     self.nameInput =  QLineEdit()
    #     self.nameInput.setCompleter(namesCompleter)

    #     self.findButton = QPushButton("Найти", self)
    #     self.findButton.clicked.connect(self.findCargo)

    #     self.inputForm.addRow("Груз:", self.nameInput)
    #     self.inputForm.addRow(self.findButton)



if __name__ == '__main__':

    import sys

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
