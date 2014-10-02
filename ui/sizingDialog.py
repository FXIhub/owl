# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sizingDialog.ui'
#
# Created: Thu Oct  2 11:15:46 2014
#      by: pyside-uic 0.2.13 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_SizingDialog(object):
    def setupUi(self, SizingDialog):
        SizingDialog.setObjectName("SizingDialog")
        SizingDialog.resize(347, 102)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(SizingDialog.sizePolicy().hasHeightForWidth())
        SizingDialog.setSizePolicy(sizePolicy)
        self.gridLayout_2 = QtGui.QGridLayout(SizingDialog)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.experimentButton = QtGui.QPushButton(SizingDialog)
        self.experimentButton.setFocusPolicy(QtCore.Qt.NoFocus)
        self.experimentButton.setObjectName("experimentButton")
        self.gridLayout.addWidget(self.experimentButton, 0, 0, 1, 1)
        self.startButton = QtGui.QPushButton(SizingDialog)
        self.startButton.setFocusPolicy(QtCore.Qt.TabFocus)
        self.startButton.setObjectName("startButton")
        self.gridLayout.addWidget(self.startButton, 0, 1, 1, 1)
        self.progressBar = QtGui.QProgressBar(SizingDialog)
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        self.gridLayout.addWidget(self.progressBar, 1, 0, 1, 2)
        self.progressLabel = QtGui.QLabel(SizingDialog)
        self.progressLabel.setObjectName("progressLabel")
        self.gridLayout.addWidget(self.progressLabel, 2, 0, 1, 2)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)

        self.retranslateUi(SizingDialog)
        QtCore.QMetaObject.connectSlotsByName(SizingDialog)

    def retranslateUi(self, SizingDialog):
        SizingDialog.setWindowTitle(QtGui.QApplication.translate("SizingDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.experimentButton.setText(QtGui.QApplication.translate("SizingDialog", "Experiment", None, QtGui.QApplication.UnicodeUTF8))
        self.startButton.setText(QtGui.QApplication.translate("SizingDialog", "Start", None, QtGui.QApplication.UnicodeUTF8))
        self.progressLabel.setText(QtGui.QApplication.translate("SizingDialog", "Ready for sizing", None, QtGui.QApplication.UnicodeUTF8))

