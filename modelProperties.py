# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'modelProperties.ui'
#
# Created: Mon Jul  7 18:36:41 2014
#      by: pyside-uic 0.2.14 running on PySide 1.1.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_ModelProperties(object):
    def setupUi(self, ModelProperties):
        ModelProperties.setObjectName("ModelProperties")
        ModelProperties.resize(256, 245)
        self.gridLayout = QtGui.QGridLayout(ModelProperties)
        self.gridLayout.setObjectName("gridLayout")
        self.label_3 = QtGui.QLabel(ModelProperties)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 2, 0, 1, 1)
        self.label = QtGui.QLabel(ModelProperties)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.label_4 = QtGui.QLabel(ModelProperties)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 3, 0, 1, 1)
        self.centerX = QtGui.QLineEdit(ModelProperties)
        self.centerX.setObjectName("centerX")
        self.gridLayout.addWidget(self.centerX, 0, 1, 1, 1)
        self.label_2 = QtGui.QLabel(ModelProperties)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)
        self.centerY = QtGui.QLineEdit(ModelProperties)
        self.centerY.setObjectName("centerY")
        self.gridLayout.addWidget(self.centerY, 1, 1, 1, 1)
        self.diameter = QtGui.QLineEdit(ModelProperties)
        self.diameter.setObjectName("diameter")
        self.gridLayout.addWidget(self.diameter, 2, 1, 1, 1)
        self.scaling = QtGui.QLineEdit(ModelProperties)
        self.scaling.setObjectName("scaling")
        self.gridLayout.addWidget(self.scaling, 3, 1, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.visibilitySlider = QtGui.QSlider(ModelProperties)
        self.visibilitySlider.setMinimum(-1)
        self.visibilitySlider.setMaximum(101)
        self.visibilitySlider.setProperty("value", 50)
        self.visibilitySlider.setOrientation(QtCore.Qt.Horizontal)
        self.visibilitySlider.setObjectName("visibilitySlider")
        self.verticalLayout.addWidget(self.visibilitySlider)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.experiment = QtGui.QPushButton(ModelProperties)
        self.experiment.setObjectName("experiment")
        self.horizontalLayout.addWidget(self.experiment)
        self.fitPushButton = QtGui.QPushButton(ModelProperties)
        self.fitPushButton.setObjectName("fitPushButton")
        self.horizontalLayout.addWidget(self.fitPushButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gridLayout.addLayout(self.verticalLayout, 4, 0, 1, 2)

        self.retranslateUi(ModelProperties)
        QtCore.QMetaObject.connectSlotsByName(ModelProperties)

    def retranslateUi(self, ModelProperties):
        ModelProperties.setWindowTitle(QtGui.QApplication.translate("ModelProperties", "Model Properties", None, QtGui.QApplication.UnicodeUTF8))
        ModelProperties.setTitle(QtGui.QApplication.translate("ModelProperties", "Model Properties", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("ModelProperties", "Diameter [nm]:", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("ModelProperties", "Center X:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_4.setText(QtGui.QApplication.translate("ModelProperties", "Intensity [mJ/µm2]:", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("ModelProperties", "Center Y:", None, QtGui.QApplication.UnicodeUTF8))
        self.experiment.setText(QtGui.QApplication.translate("ModelProperties", "Experiment...", None, QtGui.QApplication.UnicodeUTF8))
        self.fitPushButton.setText(QtGui.QApplication.translate("ModelProperties", "Fit", None, QtGui.QApplication.UnicodeUTF8))

