# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'selectIndexDialog.ui'
#
# Created: Thu Jul  3 16:02:50 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from Qt import QtCore, QtGui

class Ui_SelectIndexDialog(object):
    def setupUi(self, SelectIndexDialog):
        SelectIndexDialog.setObjectName("SelectIndexDialog")
        SelectIndexDialog.resize(511, 125)
        self.verticalLayoutWidget = QtGui.QWidget(SelectIndexDialog)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(20, 10, 481, 31))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(self.verticalLayoutWidget)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.verticalLayoutWidget_2 = QtGui.QWidget(SelectIndexDialog)
        self.verticalLayoutWidget_2.setGeometry(QtCore.QRect(19, 50, 481, 26))
        self.verticalLayoutWidget_2.setObjectName("verticalLayoutWidget_2")
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.verticalLayoutWidget_2)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.comboBox = QtGui.QComboBox(self.verticalLayoutWidget_2)
        self.comboBox.setObjectName("comboBox")
        self.verticalLayout_2.addWidget(self.comboBox)
        self.verticalLayoutWidget_3 = QtGui.QWidget(SelectIndexDialog)
        self.verticalLayoutWidget_3.setGeometry(QtCore.QRect(20, 80, 481, 32))
        self.verticalLayoutWidget_3.setObjectName("verticalLayoutWidget_3")
        self.verticalLayout_3 = QtGui.QVBoxLayout(self.verticalLayoutWidget_3)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.buttonBox = QtGui.QDialogButtonBox(self.verticalLayoutWidget_3)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.verticalLayout_3.addWidget(self.buttonBox)

        self.retranslateUi(SelectIndexDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("accepted()"), SelectIndexDialog.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL("rejected()"), SelectIndexDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(SelectIndexDialog)

    def retranslateUi(self, SelectIndexDialog):
        SelectIndexDialog.setWindowTitle(QtGui.QApplication.translate("SelectIndexDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("SelectIndexDialog", "Choose the index that shall be used for filtering.", None, QtGui.QApplication.UnicodeUTF8))

