#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Filter Dialog 0.1
# by TIME di Stefano Zamprogno
# 20/05/2009
# Licence: GPL

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import sys
import os

from PyQt4.QtCore import Qt, SIGNAL, QVariant
from PyQt4.QtCore import QString, QSettings

from PyQt4.QtGui  import QApplication, QComboBox
from PyQt4.QtGui  import QDialog, QDoubleSpinBox
from PyQt4.QtGui  import QGridLayout, QLabel
from PyQt4.QtGui  import QTableView, QMessageBox

from PyQt4.QtSql  import QSqlTableModel, QSqlDatabase, QSqlQuery

import filterdialog

FILTERDLGORG = "TIME di Stefano Z."
FILTERDLGAPP = "Filter Dialog"

class FilterDialog(QDialog, filterdialog.Ui_FilterDialog):

    def __init__(self, header=None, db=None, parent=None):
        super(FilterDialog, self).__init__(parent)

        self.setupUi(self)

        self.dbi = ""
        if not db:
            filename = ":memory:"
            self.dbi = QSqlDatabase.addDatabase("QSQLITE")
            self.dbi.setDatabaseName(filename)
            self.dbi.open()

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
                self.accept)
        self.connect(self.addLinePushButton, SIGNAL("clicked()"),
                self.addLine)

        self.sModel.insertRows(0, 10)
        self.sModel.submitAll()
        self.restoreSettings()
        self.resultFilter = None

    def accept(self):
        rows = self.sModel.rowCount()
        cols = self.sModel.columnCount()
        model = self.sModel
        mlqry = dict()
        qry = None
        for r in range(rows):
            record = model.record(r)
            for c in range(1, cols):
                if record.value(c).toString():
                    if not qry:
                        qry = "("
                    elif c > 1 and qry :
                        qry = "%s AND" % qry
                    qry = "%s %s %s" % (qry, record.fieldName(c),
                                    record.value(c).toString())
            if qry :
                mlqry[r] = "%s )" % qry
                qry = ""
        for q in mlqry.keys():
            if not qry:
                qry = mlqry[q]
                continue
            qry = "%s OR %s" % (qry, mlqry[q])
        self.resultFilter = qry
        query = QSqlQuery()
        query.exec_("DROP TABLE filtertable")
        if self.dbi:
            del self.dbi
        QDialog.accept(self)

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
        query.exec_("DROP TABLE filtertable")
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
        settings = QSettings(QString(FILTERDLGORG),
                            QString(FILTERDLGAPP))
        self.restoreGeometry(
                settings.value("MainWindow/Geometry").toByteArray())

    def closeEvent(self, event):
        settings = QSettings(QString(FILTERDLGORG),
                QString(FILTERDLGAPP))
        settings.setValue("MainWindow/Geometry", QVariant(
                          self.saveGeometry()))

    def filterDone(self):
        return self.resultFilter

def main():
    app = QApplication(sys.argv)

    form = FilterDialog(("datains VARCHAR(100)",
                        "abbi VARCHAR(100)",
                        "angro VARCHAR(100)",
                        "desc VARCHAR(100)",
                        "qt VARCHAR(100)",
                        "imp VARCHAR(100)",
                        "equiv VARCHAR(100)"), None, None)
    form.show()
    app.exec_()
    print(form.filterDone())
    del form


if __name__ == "__main__":
    main()

