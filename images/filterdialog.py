# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'filterdialog.ui'
#
# Created: Tue May 19 21:57:18 2009
#      by: PyQt4 UI code generator 4.4.4
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

class Ui_FilterDialog(object):
    def setupUi(self, FilterDialog):
        FilterDialog.setObjectName("FilterDialog")
        FilterDialog.resize(579, 380)
        self.gridLayout = QtGui.QGridLayout(FilterDialog)
        self.gridLayout.setObjectName("gridLayout")
        self.filterTableView = QtGui.QTableView(FilterDialog)
        self.filterTableView.setAutoFillBackground(True)
        self.filterTableView.setAlternatingRowColors(True)
        self.filterTableView.setObjectName("filterTableView")
        self.gridLayout.addWidget(self.filterTableView, 0, 0, 1, 3)
        spacerItem = QtGui.QSpacerItem(467, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 1, 0, 1, 1)
        self.addLinePushButton = QtGui.QPushButton(FilterDialog)
        self.addLinePushButton.setObjectName("addLinePushButton")
        self.gridLayout.addWidget(self.addLinePushButton, 1, 1, 1, 1)
        self.addFilterPushButton = QtGui.QPushButton(FilterDialog)
        self.addFilterPushButton.setObjectName("addFilterPushButton")
        self.gridLayout.addWidget(self.addFilterPushButton, 1, 2, 1, 1)

        self.retranslateUi(FilterDialog)
        QtCore.QMetaObject.connectSlotsByName(FilterDialog)

    def retranslateUi(self, FilterDialog):
        FilterDialog.setWindowTitle(QtGui.QApplication.translate("FilterDialog", "FilterDialog", None, QtGui.QApplication.UnicodeUTF8))
        self.addLinePushButton.setText(QtGui.QApplication.translate("FilterDialog", "Add&Line", None, QtGui.QApplication.UnicodeUTF8))
        self.addFilterPushButton.setText(QtGui.QApplication.translate("FilterDialog", "&CreateFilter", None, QtGui.QApplication.UnicodeUTF8))

