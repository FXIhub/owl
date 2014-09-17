# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'fileModeDialog.ui'
#
# Created: Tue Sep  9 14:44:44 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FileModeDialog(object):
    def setupUi(self, FileModeDialog):
        FileModeDialog.setObjectName("FileModeDialog")
        FileModeDialog.resize(398, 161)
        self.verticalLayoutWidget = QtGui.QWidget(FileModeDialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(30, 20, 341, 125))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.r = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.r.setObjectName("r")
        self.verticalLayout.addWidget(self.r)
        self.rswmr = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.rswmr.setObjectName("rswmr")
        self.verticalLayout.addWidget(self.rswmr)
        self.rw = QtGui.QRadioButton(self.verticalLayoutWidget)
        self.rw.setObjectName("rw")
        self.verticalLayout.addWidget(self.rw)
        self.buttonBox = QtGui.QDialogButtonBox(self.verticalLayoutWidget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(FileModeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), FileModeDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), FileModeDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(FileModeDialog)

    def retranslateUi(self, FileModeDialog):
        FileModeDialog.setWindowTitle(QtGui.QApplication.translate("FileModeDialog", "File mode", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("FileModeDialog", "File mode:", None, QtGui.QApplication.UnicodeUTF8))
        self.r.setText(QtGui.QApplication.translate("FileModeDialog", "Read", None, QtGui.QApplication.UnicodeUTF8))
        self.rswmr.setText(QtGui.QApplication.translate("FileModeDialog", "Read (Single Write Multiple Read)", None, QtGui.QApplication.UnicodeUTF8))
        self.rw.setText(QtGui.QApplication.translate("FileModeDialog", "Read-write", None, QtGui.QApplication.UnicodeUTF8))

