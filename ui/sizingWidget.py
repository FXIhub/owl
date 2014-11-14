# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sizingWidget.ui'
#
# Created: Wed Oct 29 18:03:00 2014
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from Qt import QtCore, QtGui

class Ui_SizingWidget(object):
    def setupUi(self, SizingWidget):
        SizingWidget.setObjectName("SizingWidget")
        SizingWidget.resize(266, 125)
        self.gridLayout_2 = QtGui.QGridLayout(SizingWidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.setdataButton = QtGui.QPushButton(SizingWidget)
        self.setdataButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setdataButton.setObjectName("setdataButton")
        self.gridLayout.addWidget(self.setdataButton, 0, 0, 1, 1)
        self.startButton = QtGui.QPushButton(SizingWidget)
        self.startButton.setFocusPolicy(QtCore.Qt.TabFocus)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 0, 1, 1, 1)
        self.stopButton = QtGui.QPushButton(SizingWidget)
        self.stopButton.setObjectName("stopButton")
        self.gridLayout.addWidget(self.stopButton, 0, 2, 1, 1)
        self.progressBar = QtGui.QProgressBar(SizingWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 3)
        self.progressLabel = QtGui.QLabel(SizingWidget)
        self.progressLabel.setObjectName("progressLabel")
        self.gridLayout.addWidget(self.progressLabel, 2, 0, 1, 3)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(SizingWidget)
        QtCore.QMetaObject.connectSlotsByName(SizingWidget)

    def retranslateUi(self, SizingWidget):
        SizingWidget.setWindowTitle(QtGui.QApplication.translate("SizingWidget", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        SizingWidget.setTitle(QtGui.QApplication.translate("SizingWidget", "Sizing Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.setdataButton.setText(QtGui.QApplication.translate("SizingWidget", "Set Data", None, QtGui.QApplication.UnicodeUTF8))
        self.startButton.setText(QtGui.QApplication.translate("SizingWidget", "Start", None, QtGui.QApplication.UnicodeUTF8))
        self.stopButton.setText(QtGui.QApplication.translate("SizingWidget", "Stop", None, QtGui.QApplication.UnicodeUTF8))
        self.progressLabel.setText(QtGui.QApplication.translate("SizingWidget", "Ready for sizing", None, QtGui.QApplication.UnicodeUTF8))

