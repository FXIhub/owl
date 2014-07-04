# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'modelProperties.ui'
#
# Created: Thu Jul  3 12:25:56 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ModelProperties(object):
    def setupUi(self, ModelProperties):
        ModelProperties.setObjectName("ModelProperties")
        ModelProperties.resize(256, 169)
        self.gridLayout = QtGui.QGridLayout(ModelProperties)
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtGui.QLabel(ModelProperties)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_2 = QtGui.QLabel(ModelProperties)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.label_3 = QtGui.QLabel(ModelProperties)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.radius = QtGui.QLineEdit(ModelProperties)
        self.radius.setObjectName("radius")
        self.gridLayout.addWidget(self.radius, 2, 1, 1, 1)
        self.label_4 = QtGui.QLabel(ModelProperties)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.scaling = QtGui.QLineEdit(ModelProperties)
        self.scaling.setObjectName("scaling")
        self.gridLayout.addWidget(self.scaling, 3, 1, 1, 1)
        self.centerX = QtGui.QLineEdit(ModelProperties)
        self.centerX.setObjectName("centerX")
        self.gridLayout.addWidget(self.centerX, 0, 1, 1, 1)
        self.centerY = QtGui.QLineEdit(ModelProperties)
        self.centerY.setObjectName("centerY")
        self.gridLayout.addWidget(self.centerY, 1, 1, 1, 1)

        self.retranslateUi(ModelProperties)
        QtCore.QMetaObject.connectSlotsByName(ModelProperties)

    def retranslateUi(self, ModelProperties):
        ModelProperties.setWindowTitle(QtGui.QApplication.translate("ModelProperties", "Model Properties", None, QtGui.QApplication.UnicodeUTF8))
        ModelProperties.setTitle(QtGui.QApplication.translate("ModelProperties", "Model Properties", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ModelProperties", "Center X:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ModelProperties", "Center Y:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ModelProperties", "Radius:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("ModelProperties", "Scaling:", None, QtGui.QApplication.UnicodeUTF8))

