# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/sizingWidget.ui'
#
# Created: Thu Oct  2 22:10:31 2014
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SizingWidget(object):
    def setupUi(self, SizingWidget):
        SizingWidget.setObjectName("SizingWidget")
        SizingWidget.resize(260, 143)
        self.gridLayout_2 = QtGui.QGridLayout(SizingWidget)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.setdataButton = QtGui.QPushButton(SizingWidget)
        self.setdataButton.setObjectName("setdataButton")
        self.gridLayout.addWidget(self.setdataButton, 1, 0, 1, 1)
        self.progressBar = QtGui.QProgressBar(SizingWidget)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 4, 0, 1, 2)
        self.progressLabel = QtGui.QLabel(SizingWidget)
        self.progressLabel.setObjectName("progressLabel")
        self.gridLayout.addWidget(self.progressLabel, 5, 0, 1, 2)
        self.startButton = QtGui.QPushButton(SizingWidget)
        self.startButton.setFocusPolicy(QtCore.Qt.TabFocus)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 1, 1, 1, 1)
        self.experimentButton = QtGui.QPushButton(SizingWidget)
        self.experimentButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.experimentButton.setObjectName("experimentButton")
        self.gridLayout.addWidget(self.experimentButton, 0, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(SizingWidget)
        QtCore.QMetaObject.connectSlotsByName(SizingWidget)

    def retranslateUi(self, SizingWidget):
        SizingWidget.setWindowTitle(QtGui.QApplication.translate("SizingWidget", "GroupBox", None, QtGui.QApplication.UnicodeUTF8))
        SizingWidget.setTitle(QtGui.QApplication.translate("SizingWidget", "Sizing Analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.setdataButton.setText(QtGui.QApplication.translate("SizingWidget", "Set Data", None, QtGui.QApplication.UnicodeUTF8))
        self.progressLabel.setText(QtGui.QApplication.translate("SizingWidget", "Ready for sizing", None, QtGui.QApplication.UnicodeUTF8))
        self.startButton.setText(QtGui.QApplication.translate("SizingWidget", "Start", None, QtGui.QApplication.UnicodeUTF8))
        self.experimentButton.setText(QtGui.QApplication.translate("SizingWidget", "Experiment", None, QtGui.QApplication.UnicodeUTF8))

