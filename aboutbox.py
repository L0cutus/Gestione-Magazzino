#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import sys

from PyQt4.QtCore import Qt, SIGNAL
from PyQt4.QtGui  import QApplication, QComboBox, QDialog
from PyQt4.QtGui  import QDoubleSpinBox, QGridLayout, QLabel
import ui_aboutbox

class AboutBox(QDialog, ui_aboutbox.Ui_AboutDialog):
    def __init__(self, parent=None):
        super(AboutBox, self).__init__(parent)

        self.setupUi(self)

if __name__ == "__main__":
    app=QApplication(sys.argv)
    form=AboutBox()
    form.show()
    app.exec_()
