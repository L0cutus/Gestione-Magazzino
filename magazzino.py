#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Gestione magazzino
# by TIME di Stefano Zamprogno
# Initial release 12/05/2009

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import os
import sys
import subprocess

from PyQt4.QtCore import PYQT_VERSION_STR, QDate, QFile
from PyQt4.QtCore import QRegExp, QString, QVariant, Qt
from PyQt4.QtCore import SIGNAL, QModelIndex, QSettings
from PyQt4.QtCore import QSize, QPoint

from PyQt4.QtGui  import QApplication, QCursor, QDateEdit
from PyQt4.QtGui  import QDialog, QMainWindow, QHBoxLayout
from PyQt4.QtGui  import QLabel, QLineEdit, QMessageBox, QPixmap
from PyQt4.QtGui  import QTabWidget, QPushButton, QRegExpValidator
from PyQt4.QtGui  import QStyleOptionViewItem, QTableView, QVBoxLayout
from PyQt4.QtGui  import QDataWidgetMapper, QTextDocument, QStyle
from PyQt4.QtGui  import QColor, QBrush, QTextOption
from PyQt4.QtGui  import QItemSelectionModel,QStandardItemModel
from PyQt4.QtGui  import QAbstractItemView, QIntValidator
from PyQt4.QtGui  import QDoubleValidator, QIcon, QFileDialog

from PyQt4.QtSql  import QSqlDatabase, QSqlQuery, QSqlRelation
from PyQt4.QtSql  import QSqlRelationalDelegate, QSqlRelationalTableModel
from PyQt4.QtSql  import QSqlTableModel

#from PyQt4.QtCore import qVersion

import magazzino_ui
import filterdialog
import aboutmaga

#~ print(qVersion())
#~ print(QT_VERSION_STR)

__version__ = '0.2.0'

# Definizione degli 'id' usati poi come colonne nelle tabelle ecc...
ID, SCAFF = 0, 1
ID, DATAINS, ABBI, ANGRO, DESC, QT, IMP, EQUIV, MMID, FATT, NOTE = range(11)

# id dei 3 tab del tabwidget
ADDTAB, FINDTAB, OPTTAB = range(3)
DATEFORMAT = "dd/MM/yyyy"

# usate per il salvataggio dei settings dell'applicazione
MAGAORG = "TIME di Stefano Z."
MAGAAPP = "Gestione Magazzino"
MAGADOMAIN = "zamprogno.it"

class ssModel(QSqlTableModel):
    def __init__(self, parent=None):
        super(ssModel, self).__init__(parent)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return QVariant()

        column = index.column()
        if role == Qt.DisplayRole:
            if column == DATAINS:
                return QVariant(QSqlTableModel.data(self,
                            index).toDate().toString(DATEFORMAT))
            if column == IMP:
                return QVariant("€ %s" %
                        QSqlTableModel.data(self, index).toString())


        if role == Qt.TextAlignmentRole:
            if column == DATAINS:
                return QVariant(int(Qt.AlignLeft|Qt.AlignVCenter))
            else:
                return QVariant(int(Qt.AlignRight|Qt.AlignVCenter))


        if role == Qt.BackgroundRole:
            if column == QT:
                if QSqlTableModel.data(self, index).toInt()[0] == 0:
                    return QVariant(QColor(Qt.red))

        # default, no specific condition found
        return QSqlTableModel.data(self, index, role)


class MSDelegate(QSqlRelationalDelegate):
    def __init__(self, parent=None):
        super(MSDelegate, self).__init__(parent)

    def createEditor(self, parent, option, index):
        if index.column() == DATAINS:
            editor = QDateEdit(parent)
            editor.setCalendarPopup(True)
            editor.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
            return editor
        elif index.column() == QT:
            editor = QLineEdit(parent)
            validator = QIntValidator(self)
            editor.setValidator(validator)
            editor.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
            return editor
        elif index.column() == IMP:
            editor = QLineEdit(parent)
            validator = QDoubleValidator(self)
            validator.setDecimals(3)
            editor.setValidator(validator)
            editor.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
            return editor
        else:
            return QSqlRelationalDelegate.createEditor(self, parent,
                                                    option, index)

    def setEditorData(self, editor, index):
        if index.column() == DATAINS:
            editor.setDisplayFormat(DATEFORMAT)
            date = index.model().data(index, Qt.DisplayRole).toDate()
            if not date:
                editor.setDate(QDate.currentDate())
            else:
                editor.setDate(date)
        else:
            QSqlRelationalDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == DATAINS:
            model.setData(index, QVariant(editor.date()))
        elif index.column() == IMP:
            model.setData(index, QVariant(editor.text().replace(',', '.')))
        else:
            QSqlRelationalDelegate.setModelData(self, editor, model, index)


class MainWindow(QMainWindow, magazzino_ui.Ui_MainWindow):

    FIRST, PREV, NEXT, LAST = range(4)

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.setupUi(self)
        self.setupMenu()
        self.restoreWinSettings()

        self.editindex = None
        self.filename = None
        self.db = QSqlDatabase.addDatabase("QSQLITE")

        self.loadInitialFile()
        self.setupUiSignals()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Down:
            self.addDettRecord()
        else:
            QMainWindow.keyPressEvent(self, event)

    def creaStrutturaDB(self):
        query = QSqlQuery()
        if not ("magamaster" in self.db.tables()):
            if not query.exec_("""CREATE TABLE magamaster (
                                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                                scaff VARCHAR(10) NOT NULL)"""):
                QMessageBox.warning(self, "Magazzino",
                                QString("Creazione tabella fallita!"))
                return False

        if not ("magaslave" in self.db.tables()):
            if not query.exec_("""CREATE TABLE magaslave (
                                id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,
                                datains DATE NOT NULL,
                                abbi VARCHAR(50),
                                angro VARCHAR(50),
                                desc VARCHAR(100),
                                qt INTEGER NOT NULL DEFAULT '1',
                                imp DOUBLE NOT NULL DEFAULT '0.0',
                                equiv VARCHAR(100),
                                mmid INTEGER NOT NULL,
                                fatt VARCHAR(50),
                                note VARCHAR(200),
                                FOREIGN KEY (mmid) REFERENCES magamaster)"""):
                QMessageBox.warning(self, "Magazzino",
                                QString("Creazione tabella fallita!"))
                return False
            QMessageBox.information(self, "Magazzino",
                                QString("Database Creato!"))

        return True

    def loadFile(self, fname=None):
        if fname is None:
            return
        if self.db.isOpen():
            self.db.close()
        self.db.setDatabaseName(QString(fname))
        if not self.db.open():
            QMessageBox.warning(self, "Magazzino",
                                QString("Database Error: %1")
                                .arg(db.lastError().text()))
        else:
            if not self.creaStrutturaDB():
                return
            self.filename = unicode(fname)
            self.setWindowTitle("Gestione Magazzino - %s" % self.filename)
            self.setupModels()
            self.setupMappers()
            self.setupTables()
            #self.setupItmSignals()
            self.restoreTablesSettings()
            self.mmUpdate()


    def loadInitialFile(self):
        settings = QSettings()
        fname = unicode(settings.value("Settings/lastFile").toString())
        if fname and QFile.exists(fname):
            self.loadFile(fname)


    def openFile(self):
        dir = os.path.dirname(self.filename) \
                if self.filename is not None else "."
        fname = QFileDialog.getOpenFileName(self,
                    "Gestione Magazzino - Scegli database",
                    dir, "*.db")
        if fname:
            self.loadFile(fname)


    def newFile(self):
        dir = os.path.dirname(self.filename) \
                if self.filename is not None else "."
        fname = QFileDialog.getSaveFileName(self,
                    "Gestione Magazzino - Scegli database",
                    dir, "*.db")
        if fname:
            self.loadFile(fname)

    def setupMenu(self):
        # AboutBox
        self.connect(self.actionA_bout, SIGNAL("triggered()"),
                    self.showAboutBox)
        # FileNew
        self.connect(self.action_New_File, SIGNAL("triggered()"),
                    self.newFile)

        # FileLoad
        self.connect(self.action_Load_File, SIGNAL("triggered()"),
                    self.openFile)


    def showAboutBox(self):
        dlg = aboutmaga.AboutBox(self)
        dlg.exec_()

    def printInventory(self):
        '''
            Print Inventory
        '''
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        querygrp = QSqlQuery()
        querydett = QSqlQuery()

        querygrp.exec_("SELECT abbi,qt,imp,sum(qt*imp) "
                    "FROM magaslave GROUP BY abbi")
        querydett.prepare("SELECT datains,abbi,angro,desc,qt,imp "
                        "FROM magaslave WHERE abbi = :abbi AND qt > 0 ORDER BY datains")

        from reportlab.pdfgen.canvas import Canvas
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib.enums import TA_LEFT,TA_RIGHT,TA_CENTER
        from reportlab.platypus import Spacer, SimpleDocTemplate, Table, TableStyle, Paragraph
        from reportlab.rl_config import defaultPageSize
        from reportlab.lib import colors

        PAGE_WIDTH, PAGE_HEIGHT=defaultPageSize
        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleH = styles['Heading1']
        styleH.alignment=TA_CENTER
        Elements = []
        #add some flowables
        p=Paragraph
        ps=ParagraphStyle

        Title = unicode(self.prtTitleLineEdit.text())
        Year = unicode(self.prtDateLineEdit.text())
        Author = "Stefano Zamprogno"
        URL = "http://www.zamprogno.it/"
        email = "time@zamprogno.it"

        pageinfo = "%s / %s / %s" % (Author, email, Title)

        def myFirstPage(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColorRGB(0.50,0.50,0.50)
            canvas.setLineWidth(10)
            canvas.line(45,72,45,PAGE_HEIGHT-72)
            #canvas.setFont('Times-Bold',16)
            #canvas.drawCentredString(3*cm, 1.5*cm,Title)
            canvas.setFont('Times-Roman',9)
            canvas.drawString(3*cm, 1.5*cm, "First Page / %s" % pageinfo)
            canvas.restoreState()

        def myLaterPages(canvas, doc):
            canvas.saveState()
            canvas.setStrokeColorRGB(0.50,0.50,0.50)
            canvas.setLineWidth(5)
            canvas.line(45,72,45,PAGE_HEIGHT-72)
            canvas.setFont('Times-Roman',9)
            canvas.drawString(3*cm, 1.5*cm, "Page %d %s" % (doc.page, pageinfo))
            canvas.restoreState()

        Elements.append(Paragraph(Title, styleH))
        Elements.append(Paragraph(Year,styleN))
        Elements.append(Spacer(0.5*cm, 0.5*cm))

        tot=0
        while querygrp.next():
            tot += querygrp.value(3).toDouble()[0]
            querydett.bindValue(":abbi", QVariant(querygrp.value(0).toString()))
            querydett.exec_()
            data = [['Datains', 'Abbi', 'Angro', 'Descrizione', 'Qt', 'Imp'],]
            while querydett.next():
                data.append([   unicode(querydett.value(0).toDate().toString(
                                                    "dd/MM/yyyy")),
                                p(unicode(querydett.value(1).toString()),
                                                ps(name='Normal')),
                                p(unicode(querydett.value(2).toString()),
                                                ps(name='Normal')),
                                p(unicode(querydett.value(3).toString()),
                                                ps(name='Normal')),
                                querydett.value(4).toInt()[0],
                                unicode("%.2f" %
                                        querydett.value(5).toDouble()[0])])
            data.append([None, None, None,
                        unicode("GRUPPO '%s'" % querygrp.value(0).toString()),
                        unicode("Subtotale:"),
                        unicode("€ %.2f" % querygrp.value(3).toDouble()[0])])
            Elements.append(Table(data,repeatRows=1,
                                style=(['LINEBELOW', (3,-2), (-1,-2),
                                            1, colors.black],
                                        ['LINEBELOW', (0,0), (-1,0),
                                            1, colors.black],
                                        ['ALIGN', (1,0), (3,-1),'CENTER'],
                                        ['ALIGN', (4,0), (-1,0),'RIGHT'],
                                        ['VALIGN', (0,0), (-1,-1), 'TOP'],
                                        ['ALIGN', (4,0), (-1,-1), 'RIGHT'],
#                                        ['TEXTCOLOR', (0,0), (-1,0),
#                                                colors.red],
                                        ['BACKGROUND',(0,0),(-1,0),
                                                colors.lightgrey],
                                        ['GRID',(0,0),(-1,-1), 0.2,
                                                colors.black],
                                        ['FONT', (0, 0), (-1, 0),
                                                'Helvetica-Bold', 10],
                                        ['FONT', (3, -1), (3, -1),
                                                'Helvetica-Bold', 10])))
            Elements.append(Spacer(0.5*cm, 0.5*cm))

        Elements.append(Paragraph("<para align=right><b>TOTALE GENERALE: € %.2f</b></para>" % tot, styleN))

        doc = SimpleDocTemplate(os.path.join(os.path.dirname(__file__),
                        'mydoc.pdf'))
        doc.build(Elements,onFirstPage=myFirstPage, onLaterPages=myLaterPages)

        subprocess.Popen(['gnome-open',os.path.join(os.path.dirname(__file__),
                        'mydoc.pdf')])

    def setupMappers(self):
        '''
            Initialize all the application mappers
        '''
        self.mapper = QDataWidgetMapper(self)
        self.mapper.setModel(self.mModel)
        self.mapper.addMapping(self.scaffLineEdit, SCAFF)
        self.mapper.setSubmitPolicy(QDataWidgetMapper.ManualSubmit)
        self.mapper.toFirst()

    def setupTables(self):
        """
            Initialize all the application tablesview
        """
        self.sTableView.setModel(self.sModel)
        self.sTableView.setItemDelegate(MSDelegate(self))
        self.sTableView.setColumnHidden(ID, True)
        self.sTableView.setColumnHidden(MMID, True)
        self.sTableView.setWordWrap(True)
        self.sTableView.resizeRowsToContents()
        self.sTableView.setAlternatingRowColors(True)
        self.sItmSelModel = QItemSelectionModel(self.sModel)
        self.sTableView.setSelectionModel(self.sItmSelModel)
        self.sTableView.setSelectionBehavior(QTableView.SelectRows)
        #self.sTableView.setTabKeyNavigation(True)


        self.fTableView.setModel(self.fModel)
        self.fTableView.setColumnHidden(ID, True)
        self.fTableView.setWordWrap(True)
        self.fTableView.resizeRowsToContents()
        self.fTableView.setAlternatingRowColors(True)
        self.fItmSelModel = QItemSelectionModel(self.fModel)
        self.fTableView.setSelectionModel(self.fItmSelModel)

    def setupModels(self):
        """
            Initialize all the application models
        """
        # setup slaveModel
        self.sModel = ssModel(self)
        self.sModel.setTable(QString("magaslave"))
        self.sModel.setHeaderData(ID, Qt.Horizontal, QVariant("ID"))
        self.sModel.setHeaderData(DATAINS, Qt.Horizontal, QVariant("DataIns"))
        self.sModel.setHeaderData(ABBI, Qt.Horizontal, QVariant("Abbi"))
        self.sModel.setHeaderData(ANGRO, Qt.Horizontal, QVariant("Angro"))
        self.sModel.setHeaderData(DESC, Qt.Horizontal, QVariant("Desc"))
        self.sModel.setHeaderData(QT, Qt.Horizontal, QVariant("Qt"))
        self.sModel.setHeaderData(IMP, Qt.Horizontal, QVariant("Imp"))
        self.sModel.setHeaderData(EQUIV, Qt.Horizontal, QVariant("Equiv"))
        self.sModel.setHeaderData(MMID, Qt.Horizontal, QVariant("ScaffId"))
        self.sModel.setHeaderData(FATT, Qt.Horizontal, QVariant("Fatt"))
        self.sModel.setHeaderData(NOTE, Qt.Horizontal, QVariant("Note"))
        self.sModel.setSort(DATAINS, Qt.AscendingOrder)
        self.sModel.setEditStrategy(QSqlTableModel.OnRowChange)
        self.sModel.select()

        # setup masterModel
        self.mModel = QSqlTableModel(self)
        self.mModel.setTable(QString("magamaster"))
        self.mModel.setSort(SCAFF, Qt.AscendingOrder)
        self.mModel.setHeaderData(ID, Qt.Horizontal, QVariant("ID"))
        self.mModel.setHeaderData(SCAFF, Qt.Horizontal, QVariant("Scaff"))
        self.mModel.select()

        # setup findModel
        self.fModel = QSqlRelationalTableModel(self)
        self.fModel.setTable(QString("magaslave"))
        self.fModel.setHeaderData(ID, Qt.Horizontal, QVariant("ID"))
        self.fModel.setHeaderData(DATAINS, Qt.Horizontal, QVariant("DataIns"))
        self.fModel.setHeaderData(ABBI, Qt.Horizontal, QVariant("Abbi"))
        self.fModel.setHeaderData(ANGRO, Qt.Horizontal, QVariant("Angro"))
        self.fModel.setHeaderData(DESC, Qt.Horizontal, QVariant("Desc"))
        self.fModel.setHeaderData(QT, Qt.Horizontal, QVariant("Qt"))
        self.fModel.setHeaderData(IMP, Qt.Horizontal, QVariant("Imp"))
        self.fModel.setHeaderData(EQUIV, Qt.Horizontal, QVariant("Equiv"))
        self.fModel.setHeaderData(MMID, Qt.Horizontal, QVariant("ScaffId"))
        self.fModel.setHeaderData(FATT, Qt.Horizontal, QVariant("Fatt"))
        self.fModel.setHeaderData(NOTE, Qt.Horizontal, QVariant("Note"))
        self.fModel.setSort(MMID, Qt.AscendingOrder)
        self.fModel.setRelation(MMID, QSqlRelation("magamaster",
                                            "id", "scaff"))
        self.fModel.select()

    #~ def setupItmSignals(self):
        #~ self.connect(self.sItmSelModel, SIGNAL(
                    #~ "currentChanged(QModelIndex, QModelIndex)"),
                    #~ self.editEsc)

    def setupUiSignals(self):
        #~ self.connect(self.sTableView, SIGNAL("keyPressEvent ( QKeyEvent * event )"),
                    #~ self.kPress)
        self.connect(self.scaffLineEdit, SIGNAL("returnPressed()"),
                    lambda: self.saveRecord(MainWindow.FIRST))
        self.connect(self.findLineEdit, SIGNAL("returnPressed()"),
                    self.globalFilter)
        self.connect(self.printPushButton, SIGNAL("clicked()"),
                    self.printInventory)
        self.connect(self.createFilterPushButton, SIGNAL("clicked()"),
                    self.createFilter)
        self.connect(self.findPushButton, SIGNAL("clicked()"),
                    self.applyFilter)
        self.connect(self.gSearchPushButton, SIGNAL("clicked()"),
                    self.globalFilter)
        self.connect(self.addscaffPushButton, SIGNAL("clicked()"),
                    self.addScaffRecord)
        self.connect(self.adddettPushButton, SIGNAL("clicked()"),
                    self.addDettRecord)
        self.connect(self.deldettPushButton, SIGNAL("clicked()"),
                    self.delDettRecord)
        self.connect(self.delscaffPushButton, SIGNAL("clicked()"),
                    self.delScaffRecord)
        self.connect(self.scaffFirstPushButton, SIGNAL("clicked()"),
                    lambda: self.saveRecord(MainWindow.FIRST))
        self.connect(self.scaffPrevPushButton, SIGNAL("clicked()"),
                    lambda: self.saveRecord(MainWindow.PREV))
        self.connect(self.scaffNextPushButton, SIGNAL("clicked()"),
                    lambda: self.saveRecord(MainWindow.NEXT))
        self.connect(self.scaffLastPushButton, SIGNAL("clicked()"),
                    lambda: self.saveRecord(MainWindow.LAST))


    def globalFilter(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        txt = self.findLineEdit.text()
        qry =   ("(datains like '%s') OR "
                "(abbi like '%s') OR "
                "(angro like '%s') OR "
                "(desc like '%s') OR "
                "(equiv like '%s') OR"
                "(fatt like '%s') OR"
                "(note like '%s')") % ((txt,)*7)
        self.fModel.setFilter(qry)
        self.updateFilter()

    def updateFilter(self):
        self.fModel.select()
        self.fTableView.setColumnHidden(ID, True)

    def applyFilter(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        self.fModel.setFilter(self.findLineEdit.text())
        self.updateFilter()

    def createFilter(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        headerDef = ("datains VARCHAR(100)",
                            "abbi VARCHAR(100)",
                            "angro VARCHAR(100)",
                            "desc VARCHAR(100)",
                            "qt VARCHAR(100)",
                            "imp VARCHAR(100)",
                            "equiv VARCHAR(100)",
                            "fatt VARCHAR(100)",
                            "note VARCHAR(100)")
        dlg = filterdialog.FilterDialog(headerDef,
                        QSqlDatabase.database(), self)
        if(dlg.exec_()):
            self.findLineEdit.setText(dlg.filterDone() if dlg.filterDone() else "")
            self.applyFilter()

    #~ def editEsc(self, idxcur, idxold):
        #~ if self.editindex and self.editindex.isValid():
            #~ if idxcur.row() != self.editindex.row():
                #~ self.sModel.revertAll()
                #~ self.editindex = None

    def mmUpdate(self):
        row = self.mapper.currentIndex()
        id = self.mModel.data(self.mModel.index(row,ID)).toString()
        self.sModel.setFilter("mmid=%s" % id)
        self.sModel.select()
        self.sTableView.setColumnHidden(ID, True)
        self.sTableView.setColumnHidden(MMID, True)

    def saveRecord(self, where):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        row = self.mapper.currentIndex()
        self.mapper.submit()
        self.sModel.revertAll()
        if where == MainWindow.FIRST:
            row=0
        elif where == MainWindow.PREV:
            row = 0 if row <= 1 else row - 1
        elif where == MainWindow.NEXT:
            row += 1
            if row >= self.mModel.rowCount():
                row = self.mModel.rowCount() -1
        elif where == MainWindow.LAST:
            row = self.mModel.rowCount()- 1
        self.mapper.setCurrentIndex(row)
        self.mmUpdate()

    def addScaffRecord(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        row = self.mModel.rowCount()
        self.mapper.submit()
        self.mModel.insertRow(row)
        self.mapper.setCurrentIndex(row)
        self.scaffLineEdit.setFocus()
        self.mmUpdate()

    def addDettRecord(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        rowscaff = self.mapper.currentIndex()
        record = self.mModel.record(rowscaff)
        masterid = record.value(ID).toInt()[0]
        if masterid < 1:
            self.statusbar.showMessage(
                "Scaffale non valido o non confermato...",
                5000)
            self.scaffLineEdit.setFocus()
            return
        # aggiunge la nuova riga alla vista
        self.sModel.submitAll()
        self.sModel.select()
        row = self.sModel.rowCount()
        self.sModel.insertRow(row)
        if row > 1:
            precfatt = self.sModel.data(self.sModel.index(row-1, FATT))
        else:
            precfatt = ''
        self.sModel.setData(self.sModel.index(row, MMID),
                                                QVariant(masterid))
        self.sModel.setData(self.sModel.index(row, QT),
                                                QVariant(1))
        self.sModel.setData(self.sModel.index(row, IMP),
                                                QVariant(0.0))
        self.sModel.setData(self.sModel.index(row, FATT),
                                                QVariant(precfatt))
        self.editindex = self.sModel.index(row, DATAINS)
        self.sTableView.setCurrentIndex(self.editindex)
        self.sTableView.edit(self.editindex)

    def delDettRecord(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        selrows = self.sItmSelModel.selectedRows()
        if not selrows:
            self.statusbar.showMessage(
                "No articles selected to delete...",
                5000)
            return
        if(QMessageBox.question(self, "Cancella Articoli",
                "Vuoi cancellare: {0} articoli?".format(len(selrows)),
                QMessageBox.Yes|QMessageBox.No) ==
                QMessageBox.No):
            return
        QSqlDatabase.database().transaction()
        query = QSqlQuery()
        query.prepare("DELETE FROM magaslave WHERE id = :val")
        for i in selrows:
            if i.isValid():
                query.bindValue(":val", QVariant(i.data().toInt()[0]))
                query.exec_()
        QSqlDatabase.database().commit()
        self.sModel.revertAll()
        self.mmUpdate()

    def delScaffRecord(self):
        if not self.db.isOpen():
            self.statusbar.showMessage(
                "Database non aperto...",
                5000)
            return
        row = self.mapper.currentIndex()
        if row == -1:
            self.statusbar.showMessage(
                        "Nulla da cancellare...",
                        5000)
            return
        record = self.mModel.record(row)
        id = record.value(ID).toInt()[0]
        scaff = record.value(SCAFF).toString()
        if(QMessageBox.question(self, "Cancella Scaffale",
                    "Vuoi cancellare lo scaffale: {0} ?".format(scaff),
                    QMessageBox.Yes|QMessageBox.No) ==
                    QMessageBox.No):
            self.statusbar.showMessage(
                        "Cancellazione scaffale annullata...",
                        5000)
            return
        # cancella scaffale
        self.mModel.removeRow(row)
        self.mModel.submitAll()
        if row + 1 >= self.mModel.rowCount():
            row = self.mModel.rowCount() - 1
        self.mapper.setCurrentIndex(row)
        if self.mModel.rowCount() == 0:
            self.scaffLineEdit.setText(QString(""))

        # cancella tutti gli articoli che si riferiscono
        # allo scaffale cancellato
        self.sModel.setFilter("mmid=%s" % id)
        self.sModel.select()
        self.sModel.removeRows(0, self.sModel.rowCount())
        self.sModel.submitAll()
        self.statusbar.showMessage(
                        "Cancellazione eseguita...",
                        5000)
        self.mmUpdate()

    def restoreTablesSettings(self):
        settings = QSettings(self)
        if self.saveTableGeometryCheckBox.isChecked():
            # per la tabella slave
            for c in range(1, self.sModel.columnCount()-1):
                width = settings.value("Settings/sTableView/%s" % c,
                                        QVariant(60)).toInt()[0]
                self.sTableView.setColumnWidth(c,
                                            width if width > 0 else 60)

            # per la tabella find
            for c in range(1, self.fModel.columnCount()):
                width = settings.value("Settings/fTableView/%s" % c,
                                        QVariant(60)).toInt()[0]
                self.fTableView.setColumnWidth(c,
                                            width if width > 0 else 60)

    def restoreWinSettings(self):
        settings = QSettings()
        self.prtTitleLineEdit.setText(QString(settings.value(
                            "Settings/printTitle", QVariant(
                            "Situazione Magazzino - TIME di Stefano Zamprogno")).toString()))
        self.prtDateLineEdit.setText(QString(settings.value(
                            "Settings/printDate", QVariant(
                            "Al 31/12/2008")).toString()))
        self.saveWinPosCheckBox.setChecked(
                settings.value("Settings/saveWinPos", QVariant(True)).toBool())
        self.saveTableGeometryCheckBox.setChecked(
                settings.value("Settings/saveTableGeometry",
                QVariant(True)).toBool())
        self.restoreGeometry(
                settings.value("MainWindow/Geometry").toByteArray())

    def closeEvent(self, event):
        settings = QSettings()
        if self.filename is not None:
            settings.setValue("Settings/lastFile", QVariant(self.filename))
        settings.setValue("MainWindow/Geometry", QVariant(
                          self.saveGeometry()))
        settings.setValue("Settings/saveWinPos", QVariant(
                          self.saveWinPosCheckBox.isChecked()))
        settings.setValue("Settings/saveTableGeometry", QVariant(
                          self.saveTableGeometryCheckBox.isChecked()))
        settings.setValue("Settings/printTitle", QVariant(
                          self.prtTitleLineEdit.text()))
        settings.setValue("Settings/printDate", QVariant(
                          self.prtDateLineEdit.text()))

        if self.db.isOpen():
            # salva larghezza colonne tabella slave
            for c in range(1, self.sModel.columnCount()-1):
                width = self.sTableView.columnWidth(c)
                if width:
                    settings.setValue("Settings/sTableView/%s" % c,
                                        QVariant(width))

            # salva larghezza colonne tabella find
            for c in range(1, self.fModel.columnCount()):
                width = self.fTableView.columnWidth(c)
                if width:
                    settings.setValue("Settings/fTableView/%s" % c,
                        QVariant(width))
        self.db.close()
        del self.db

def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(MAGAORG)
    app.setOrganizationDomain(MAGADOMAIN)
    app.setApplicationName(MAGAAPP)

    form = MainWindow()
    form.show()
    form.raise_()
    app.exec_()
    del form

main()

