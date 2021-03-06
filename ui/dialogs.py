import sys,os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
#print (sys.version)
from OpenGL.GL import *
from OpenGL.GLU import *
#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from Qt import QtGui, QtCore, QtOpenGL

import numpy
import math
import logging
import settingsOwl
from ui import Ui_TagsDialog
from ui import Ui_SelectIndexDialog
from ui import Ui_PreferencesDialog
from ui import Ui_FileModeDialog
from ui import Ui_ExperimentDialog

try:
    import spimage
    hasSpimage = True
except:
    hasSpimage = False


class TagsDialog(QtGui.QDialog, Ui_TagsDialog):
    def __init__(self,parent,tags):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.okButton.clicked.connect(self.onOkClicked)
        self.cancelButton.clicked.connect(self.reject)
        self.addButton.clicked.connect(self.addTag)
        self.deleteButton.clicked.connect(self.deleteTag)
        # Tango Icon colors from Inkscape
        settings = QtCore.QSettings()
        self.colors = settings.value('TagColors')
        self.tagsTable.cellDoubleClicked.connect(self.onCellDoubleClicked)
        self.tagsTable.cellClicked.connect(self.onCellClicked)
        self.colorIndex = 0

        for i in range(0,len(tags)):
            self.addTag(tags[i][0],tags[i][1],tags[i][2],tags[i][3])

#        self.tagsTable.setStyleSheet("selection-background-color: white; selection-color: black;")
        self.tagsTable.setStyleSheet("QTableWidget::item:selected{ background-color: white; color: black }")

    def onOkClicked(self):
        # Check if all Tags have different names and only accept then
        list = []
        unique = True
        for i in range(0,self.tagsTable.columnCount()):
            tag = self.tagsTable.item(0,i).text()
            if(tag in list):
                unique = False
                QtGui.QMessageBox.warning(self,"Duplicate Tags","You cannot have duplicate tag names. Please change them.")
                self.tagsTable.editItem(self.tagsTable.item(0,i))
                break
            list.append(tag)
        if(unique):
            self.accept()
    def getTags(self):
        tags = []
        for i in range(0,self.tagsTable.columnCount()):
            tags.append([self.tagsTable.item(0,i).text(),
                         self.tagsTable.item(1,i).background().color(),
                         self.tagsTable.cellWidget(2,i).checkbox.checkState(),
                         int(self.tagsTable.item(3,i).text())])
        return tags
    def onCellDoubleClicked(self, row, col):
        item = self.tagsTable.item(row,col)
        if(row == 1):
            # Change color
            color = QtGui.QColorDialog.getColor(item.background().color(),self)
            if(color.isValid()):
                item.setBackground(color)            
        return

    def onCellClicked(self, row, col):    

        item = self.tagsTable.item(0,col).setSelected(True)
#        item = self.tagsTable.item(0,col).setCurrentItem(True)
#        item = self.tagsTable.setCurrentCell(0,col)
        return
        
    def addTag(self,title=None,color=None,check=QtCore.Qt.Unchecked,count=0):
        self.tagsTable.insertColumn(self.tagsTable.columnCount())

        # The Tag name
        if(title is None):
            title = "Tag "+str(self.colorIndex)
        item = QtGui.QTableWidgetItem(title)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        item.setToolTip("Double click to change name")
        self.tagsTable.setItem(0,self.tagsTable.columnCount()-1,item)

        # The Tag color
        item = QtGui.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        if(color is None):
            color = self.colors[self.colorIndex%len(self.colors)]
        self.colorIndex += 1
        item.setBackground(color)
        item.setToolTip("Double click to change color")
        self.tagsTable.setItem(1,self.tagsTable.columnCount()-1,item)

        # The Tag checkbox
        widget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout(widget);
        checkbox = QtGui.QCheckBox()
        checkbox.setCheckState(check)
        layout.addWidget(checkbox);
        layout.setAlignment(QtCore.Qt.AlignCenter);
        layout.setContentsMargins(0,0,0,0);
        widget.setLayout(layout);    
        widget.setToolTip("If enabld hide images which are not tagged")
        widget.checkbox = checkbox
        self.tagsTable.setCellWidget(2,self.tagsTable.columnCount()-1,widget)


        # The Tag count
        item = QtGui.QTableWidgetItem(str(count))
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        item.setFlags(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsSelectable)
        item.setToolTip("Numbers of images tagged")
        self.tagsTable.setItem(3,self.tagsTable.columnCount()-1,item)

    def deleteTag(self):
        self.tagsTable.removeColumn(self.tagsTable.currentColumn())

class SelectIndexDialog(QtGui.QDialog, Ui_SelectIndexDialog):
    def __init__(self,parent,dataItem):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.dataItem = dataItem
        self.populateComboBox()
        self.buttonBox.accepted.connect(self.onOkButtonClicked)
        #self.connect(buttonBox, SIGNAL("rejected()"), self.reject)

    def populateComboBox(self):
        isTags = (self.dataItem.fullName[self.dataItem.fullName.rindex("/")+1:] == "tags")
        if not isTags:
            nDims = self.dataItem.shape()[1]
        else:
            if(self.dataItem.parent.tagsItem.tagsDirty):
                saveTags =  QtGui.QMessageBox.question(self, "Save tag changes?",
                                                       "You have unsaved changes to tags. You can only filter on saved tags. Would you like to save changes to the tags?",
                                                   QtGui.QMessageBox.Save, QtGui.QMessageBox.No)
                if(saveTags == QtGui.QMessageBox.Save):
                    self.dataItem.parent.tagsItem.saveTags()

            nDims = len(self.dataItem.attr("headings"))
        self.labels = []
        for i in range(nDims):
            self.labels.append("%i" % i)
        if isTags:
            for i,tag in zip(range(nDims),self.dataItem.tagsItem.tags):
                title = tag[0]
                self.labels[i] += " " + title
        self.comboBox.addItems(self.labels)

    def onOkButtonClicked(self):
        self.dataItem.selectedIndex = self.comboBox.currentIndex()
        self.accept()        
                

class PreferencesDialog(QtGui.QDialog, Ui_PreferencesDialog):
    def __init__(self,parent):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        settings = QtCore.QSettings()
        if(settings.value("scrollDirection") == -1):
            self.natural.setChecked(True)
            self.traditional.setChecked(False)
        else:
            self.natural.setChecked(False)
            self.traditional.setChecked(True)
        self.imageCacheSpin.setValue(int(settings.value("imageCacheSize")))
        self.maskCacheSpin.setValue(int(settings.value("maskCacheSize")))
        self.geometryCacheSpin.setValue(int(settings.value("geometryCacheSize")))
        self.textureCacheSpin.setValue(int(settings.value("textureCacheSize")))
        self.updateTimerSpin.setValue(int(settings.value("updateTimer")))
        self.movingAverageSizeSpin.setValue(float(settings.value("movingAverageSize")))
        self.PNGOutputPath.setText(settings.value("PNGOutputPath"))
        self.shortcutsTable.installEventFilter(self)
        shortcuts = settings.value("Shortcuts")
        for r in range(0,self.shortcutsTable.rowCount()):
            name = self.shortcutsTable.verticalHeaderItem(r).text()
            if(name in shortcuts.keys()):
                string =  QtGui.QKeySequence.fromString(shortcuts[name]).toString(QtGui.QKeySequence.NativeText)
                self.shortcutsTable.item(r,0).setText(string)
            
        self.modelCenterX.setText(str(settings.value("modelCenterX")))
        self.modelCenterY.setText(str(settings.value("modelCenterY")))
        self.modelDiameter.setText(str(settings.value("modelDiameter")))
        self.modelIntensity.setText(str(settings.value("modelIntensity")))
        self.modelMaskRadius.setText(str(settings.value("modelMaskRadius")))

        # Set validators
        validator = QtGui.QDoubleValidator()
        self.modelCenterX.setValidator(validator)
        self.modelCenterY.setValidator(validator)
        validator = QtGui.QDoubleValidator()
        validator.setBottom(0)
        self.modelDiameter.setValidator(validator)
        self.modelIntensity.setValidator(validator)
        self.modelMaskRadius.setValidator(validator)

    def eventFilter(self,obj,event):
        # If it's a keypress, there are selected items and the press is not just modifier keys
        if(event.type() == QtCore.QEvent.KeyPress and len(self.shortcutsTable.selectedItems()) and
           QtGui.QKeySequence(event.key()).toString() ):
            key = event.key()
            if(key == QtCore.Qt.Key_Alt or key == QtCore.Qt.Key_Meta or
               key == QtCore.Qt.Key_Control or key == QtCore.Qt.Key_Shift):
                return  QtGui.QDialog.eventFilter(self,obj, event);
            item = self.shortcutsTable.selectedItems()[0]
            result = QtGui.QKeySequence((event.modifiers() & ~QtCore.Qt.KeypadModifier) | event.key());  
            item.setText(result.toString(QtGui.QKeySequence.NativeText))
            return True
        else:
            # standard event processing
            return QtGui.QDialog.eventFilter(self,obj, event);



class FileModeDialog(QtGui.QDialog, Ui_FileModeDialog):
    def __init__(self,parent):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        settings = parent.settings
        mode = settings.value("fileMode")
        if mode == "r+":
            self.rw.setChecked(True)
        elif mode == "r*":
            self.rswmr.setChecked(True)
        elif mode == "r":
            self.r.setChecked(True)
        if not settingsOwl.swmrSupported:
            self.rswmr.setEnabled(False)


class ExperimentDialog(QtGui.QDialog, Ui_ExperimentDialog):
    def __init__(self,parent, modelItem):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.modelItem = modelItem
        self.materialType.addItems(spimage.DICT_atomic_composition.keys())
        params = self.modelItem.getParams(0)
        self.wavelength.setValue(params["photonWavelengthNM"])
        self.syncEnergy()
        self.distance.setValue(params["detectorDistanceMM"])
        self.pixelSize.setValue(params["detectorPixelSizeUM"])
        self.quantumEfficiency.setValue(params["detectorQuantumEfficiency"])
        self.ADUPhoton.setValue(params["detectorADUPhoton"])
        allItems = [self.materialType.itemText(i) for i in range(self.materialType.count())]
        self.materialType.setCurrentIndex(allItems.index(params["materialType"]))
        self.wavelength.editingFinished.connect(self.syncEnergy)
        self.energy.editingFinished.connect(self.syncWavelength)
        self.buttonBox.accepted.connect(self.onOkButtonClicked)
    def syncEnergy(self):
        wl = self.wavelength.value()
        h = spimage.DICT_physical_constants['h']
        c = spimage.DICT_physical_constants['c']
        qe = spimage.DICT_physical_constants['e']
        ey = h*c/wl/1.E-9/qe
        self.energy.setValue(ey)
    def syncWavelength(self):
        ey = self.energy.value()
        h = spimage.DICT_physical_constants['h']
        c = spimage.DICT_physical_constants['c']
        qe = spimage.DICT_physical_constants['e']
        wl = h*c/ey/1.E-9/qe
        self.wavelength.setValue(wl)
    def onOkButtonClicked(self):
        params = {}
        params["photonWavelengthNM"] = self.wavelength.value()
        params["photonEnergyEV"] = self.energy.value()
        params["detectorDistanceMM"] = self.distance.value()
        params["detectorPixelSizeUM"] = self.pixelSize.value()
        params["detectorQuantumEfficiency"] = self.quantumEfficiency.value()
        params["detectorADUPhoton"] = self.ADUPhoton.value()
        params["materialType"] = self.materialType.currentText()
        self.modelItem.setParams(None,params)
