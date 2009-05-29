#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import sys, os
from PyQt4.QtCore import (Qt, SIGNAL, QVariant, QString, QSettings)
from PyQt4.QtGui import (QApplication, QComboBox, QDialog,
     QDoubleSpinBox, QGridLayout, QLabel, QTableView)
from PyQt4.QtSql import (QSqlTableModel, QSqlDatabase, QSqlQuery)
import filterdialog


class FilterDialog(QDialog, filterdialog.Ui_FilterDialog):

    def __init__(self, header=None, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.setupUi(self)

        # Crea database in memoria
        #filename = os.path.join(os.path.dirname(__file__), "test.db")
        filename = ":memory:"
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(filename)
        self.db.open()

        self.creaStrutturaDB(header)

        self.sModel = QSqlTableModel(self)
        self.sModel.setTable(QString("filtertable"))
        self.sModel.setEditStrategy(QSqlTableModel.OnManualSubmit)
        self.sModel.select()

        self.filterTableView.setModel(self.sModel)
        self.filterTableView.setColumnHidden(0, True)
        self.filterTableView.setAlternatingRowColors(True)

        self.connect(self.sModel, SIGNAL("primeInsert (int,QSqlRecord&)"),
                self.updRows)
        self.connect(self.addFilterPushButton, SIGNAL("clicked()"),
                self.returnFilter)
        self.connect(self.addLinePushButton, SIGNAL("clicked()"),
                self.addLine)

        self.sModel.insertRows(0, 10)
        self.sModel.submitAll()
        self.restoreSettings()

    def returnFilter(self):
        rows = self.sModel.rowCount()
        cols = self.sModel.columnCount()
        model = self.sModel
        mlqry = dict()
        qry = ""
        for r in range(rows):
            record = model.record(r)
            for c in range(1, cols):
                if record.value(c).toString() != "":
                    if qry == "":
                        qry = "("
                    elif c > 1 and qry != "":
                        qry = "%s AND " % qry
                    qry = "%s %s %s" % (qry, record.fieldName(c),
                                    record.value(c).toString())
            if qry != "":
                mlqry[r] = "%s )" % qry
                print(mlqry[r])
                qry = ""
        for q in range(len(mlqry)):
            qry = "%s OR %s" % (qry, mlqry[q])
        self.resultFilter = qry

    def addLine(self):
        row = self.sModel.rowCount()
        self.sModel.insertRows(row, 1)
        self.sModel.submitAll()

    def updRows(self, row, record):
        totcolumn = record.count()
        for i in range(1, totcolumn):
            record.setValue(i, QVariant(""))

    def creaStrutturaDB(self, header=None):
        if not header:
            sys.exit(1)
        query = QSqlQuery()
        qry = """CREATE TABLE filtertable (
                  id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL
                  """
        for column in header:
            qry += ", %s" % column
        qry += " )"

        if not query.exec_(qry):
            QMessageBox.warning(None, "FilterTable",
                        QString("Creazione tabella fallita!"))
            sys.exit(1)


    def restoreSettings(self):
        settings = QSettings(
                QString("TIME di Stefano Z."),
                QString("Filter Dialog"))
        self.restoreGeometry(
                settings.value("MainWindow/Geometry").toByteArray())

    def closeEvent(self, event):
        settings = QSettings(
                QString("TIME di Stefano Zamprogno"),
                QString("Filter Dialog"))
        settings.setValue("MainWindow/Geometry", QVariant(
                          self.saveGeometry()))

    def filterDone(self):
        return self.resultFilter

def main():
    app = QApplication(sys.argv)

    form = FilterDialog(("datains DATE",
                        "abbi VARCHAR(20)",
                        "angro VARCHAR(20)",
                        "desc VARCHAR(50)",
                        "qt INTEGER",
                        "imp FLOAT",
                        "equiv VARCHAR(50)"))
    form.show()
    app.exec_()
    del form

if __name__ == "__main__":
    main()

