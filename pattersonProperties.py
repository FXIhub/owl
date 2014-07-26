# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pattersonProperties.ui'
#
# Created: Tue Jul  8 17:45:09 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_PattersonProperties(object):
    def setupUi(self, PattersonProperties):
        PattersonProperties.setObjectName("PattersonProperties")
        PattersonProperties.resize(262, 116)
        self.gridLayout = QtGui.QGridLayout(PattersonProperties)
        self.gridLayout.setObjectName("gridLayout")
        self.smooth = QtGui.QDoubleSpinBox(PattersonProperties)
        self.smooth.setMinimum(-10000.0)
        self.smooth.setMaximum(10000.0)
        self.smooth.setObjectName("smooth")
        self.gridLayout.addWidget(self.smooth, 0, 1, 1, 1)
        self.label = QtGui.QLabel(PattersonProperties)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.pattersonPushButton = QtGui.QPushButton(PattersonProperties)
        self.pattersonPushButton.setObjectName("pattersonPushButton")
        self.verticalLayout.addWidget(self.pattersonPushButton)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 2)

        self.retranslateUi(PattersonProperties)
        QtCore.QMetaObject.connectSlotsByName(PattersonProperties)

    def retranslateUi(self, PattersonProperties):
        PattersonProperties.setWindowTitle(QtGui.QApplication.translate("PattersonProperties", "Patterson Properties", None, QtGui.QApplication.UnicodeUTF8))
        PattersonProperties.setTitle(QtGui.QApplication.translate("PattersonProperties", "Patterson Properties", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("PattersonProperties", "Smooth [px]:", None, QtGui.QApplication.UnicodeUTF8))
        self.pattersonPushButton.setText(QtGui.QApplication.translate("PattersonProperties", "Patterson", None, QtGui.QApplication.UnicodeUTF8))

