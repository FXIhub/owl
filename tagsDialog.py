# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'tagsDialog.ui'
#
# Created: Thu Jun 26 11:34:55 2014
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_TagsDialog(object):
    def setupUi(self, TagsDialog):
        TagsDialog.setObjectName("TagsDialog")
        TagsDialog.resize(528, 235)
        self.verticalLayout = QtGui.QVBoxLayout(TagsDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gridLayout = QtGui.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.addButton = QtGui.QPushButton(TagsDialog)
        self.addButton.setObjectName("addButton")
        self.gridLayout.addWidget(self.addButton, 2, 0, 1, 1)
        self.cancelButton = QtGui.QPushButton(TagsDialog)
        self.cancelButton.setObjectName("cancelButton")
        self.gridLayout.addWidget(self.cancelButton, 2, 3, 1, 1)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 2, 1, 1)
        self.okButton = QtGui.QPushButton(TagsDialog)
        self.okButton.setMinimumSize(QtCore.QSize(80, 0))
        self.okButton.setObjectName("okButton")
        self.gridLayout.addWidget(self.okButton, 2, 4, 1, 1)
        self.deleteButton = QtGui.QPushButton(TagsDialog)
        self.deleteButton.setObjectName("deleteButton")
        self.gridLayout.addWidget(self.deleteButton, 2, 1, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.gridLayout.addItem(spacerItem1, 1, 0, 1, 1)
        self.tagsTable = QtGui.QTableWidget(TagsDialog)
        self.tagsTable.setAutoScroll(True)
        self.tagsTable.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
        self.tagsTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectColumns)
        self.tagsTable.setRowCount(4)
        self.tagsTable.setColumnCount(0)
        self.tagsTable.setObjectName("tagsTable")
        self.tagsTable.setColumnCount(0)
        self.tagsTable.setRowCount(4)
        item = QtGui.QTableWidgetItem()
        self.tagsTable.setVerticalHeaderItem(0, item)
        item = QtGui.QTableWidgetItem()
        self.tagsTable.setVerticalHeaderItem(1, item)
        item = QtGui.QTableWidgetItem()
        self.tagsTable.setVerticalHeaderItem(2, item)
        item = QtGui.QTableWidgetItem()
        self.tagsTable.setVerticalHeaderItem(3, item)
        self.tagsTable.horizontalHeader().setVisible(True)
        self.tagsTable.horizontalHeader().setMinimumSectionSize(40)
        self.tagsTable.verticalHeader().setDefaultSectionSize(30)
        self.tagsTable.verticalHeader().setHighlightSections(False)
        self.gridLayout.addWidget(self.tagsTable, 0, 0, 1, 5)
        self.verticalLayout.addLayout(self.gridLayout)

        self.retranslateUi(TagsDialog)
        QtCore.QMetaObject.connectSlotsByName(TagsDialog)

    def retranslateUi(self, TagsDialog):
        TagsDialog.setWindowTitle(QtGui.QApplication.translate("TagsDialog", "Dialog", None, QtGui.QApplication.UnicodeUTF8))
        self.addButton.setText(QtGui.QApplication.translate("TagsDialog", "Add Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.cancelButton.setText(QtGui.QApplication.translate("TagsDialog", "Cancel", None, QtGui.QApplication.UnicodeUTF8))
        self.okButton.setText(QtGui.QApplication.translate("TagsDialog", "Ok", None, QtGui.QApplication.UnicodeUTF8))
        self.deleteButton.setText(QtGui.QApplication.translate("TagsDialog", "Delete Tag", None, QtGui.QApplication.UnicodeUTF8))
        self.tagsTable.verticalHeaderItem(0).setText(QtGui.QApplication.translate("TagsDialog", "Name     ", None, QtGui.QApplication.UnicodeUTF8))
        self.tagsTable.verticalHeaderItem(1).setText(QtGui.QApplication.translate("TagsDialog", "Color", None, QtGui.QApplication.UnicodeUTF8))
        self.tagsTable.verticalHeaderItem(2).setText(QtGui.QApplication.translate("TagsDialog", "Filter", None, QtGui.QApplication.UnicodeUTF8))
        self.tagsTable.verticalHeaderItem(3).setText(QtGui.QApplication.translate("TagsDialog", "Tagged", None, QtGui.QApplication.UnicodeUTF8))

