#!/usr/bin/env python


import sys,os
sys.path.append(os.path.dirname(os.path.realpath(__file__)))
#print (sys.version)
from OpenGL.GL import *
from OpenGL.GLU import *
#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL

import numpy
import math
import settingsOwl
from geometry import *
from indexprojector import *
from dataprop import *
from dataloader import *
from cxitree import *
from view import *
from viewsplitter import ViewSplitter
import logging
import argparse
import gc
import time
import tagsDialog
import preferencesDialog
import selectIndexDialog

"""
Wishes:

Infinite subplots
Color tagged images
Double click to zoom on image (double click again zoom back to width of column). Also changes to 1 column view
View only tagged ones
Tagging with numbers
Different tags different colors
Multiple tags per image
More precise browse to img. At the moment we end up somewhere close to the image of intrest but not exactly to it.
"""

        
class Viewer(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.logger = logging.getLogger("Viewer")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["Viewer"])

        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Initializing...")
        self.init_settings()
        self.splitter = QtGui.QSplitter(self)
        self.indexProjector = IndexProjector()
        self.view = ViewSplitter(self,self.indexProjector)
        self.init_menus()

        self.fileLoader = FileLoader(self)
        self.dataProp = DataProp(self,self.indexProjector)
        self.CXINavigation = CXINavigation(self)
        self.splitter.addWidget(self.CXINavigation)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.dataProp)

        self.splitter.setStretchFactor(0,0)
        self.splitter.setStretchFactor(1,1)
        self.splitter.setStretchFactor(2,0)
        self.setCentralWidget(self.splitter)
        self.statusBar.showMessage("Initialization complete.",1000)
        
        self.geometry = Geometry();
        self.resize(800,450)
        settings = QtCore.QSettings()
        if(settings.contains("geometry")):
            self.restoreGeometry(settings.value("geometry"));
        if(settings.contains("windowState")):
            self.restoreState(settings.value("windowState"));

        QtCore.QTimer.singleShot(0,self.after_show)
        self.updateTimer = QtCore.QTimer()
        self.updateTimer.setInterval(int(settings.value("updateTimer")))
        self.updateTimer.timeout.connect(self.fileLoader.updateStackSize)

        self.view.view1D.setWindowSize(float(settings.value("movingAverageSize")))

        self.initConnections()
        self.dataProp.emitView1DProp()
        self.dataProp.emitView2DProp()
        self.setStyleSheetFromFilename()

        self.tagsChanged = False
    def after_show(self):
        if(args.filename != ""):
            self.openCXIFile(args.filename)
    def openCXIFile(self,filename):
	self.filename = filename
        self.fileLoader.loadFile(filename)
        self.CXINavigation.CXITree.buildTree(self.fileLoader)
    def init_settings(self):
        settings = QtCore.QSettings()
        if(not settings.contains("scrollDirection")):
            settings.setValue("scrollDirection", 1);
        if(not settings.contains("imageCacheSize")):
            # Default to 1 GB
            settings.setValue("imageCacheSize", 1024);
        if(not settings.contains("phaseCacheSize")):
            # Default to 1 GB
            settings.setValue("phaseCacheSize", 1024);
        if(not settings.contains("maskCacheSize")):
            # Default to 1 GB
            settings.setValue("maskCacheSize", 1024);
        if(not settings.contains("textureCacheSize")):
            # Default to 256 MB
            settings.setValue("textureCacheSize", 256);
        if(not settings.contains("updateTimer")):
            settings.setValue("updateTimer", 10000);
        if(not settings.contains("movingAverageSize")):
            settings.setValue("movingAverageSize", 10.);
        if(not settings.contains("PNGOutputPath")):
            settings.setValue("PNGOutputPath", "./");
        if(not settings.contains("MarkOutputPath")):
            settings.setValue("MarkOutputPath", "./");
        if(not settings.contains("TagColors")):
            settings.setValue("TagColors",  [QtGui.QColor(52,102,164),
                                             QtGui.QColor(245,121,0),
                                             QtGui.QColor(117,80,123),
                                             QtGui.QColor(115,210,22),
                                             QtGui.QColor(204,0,0),
                                             QtGui.QColor(193,125,17),
                                             QtGui.QColor(237,212,0)]);        

        if(not settings.contains("Shortcuts")):
            shortcuts = {}
            shortcuts["Move Selection Right"] = QtGui.QKeySequence("Right").toString()
            shortcuts["Move Selection Left"] = QtGui.QKeySequence("Left").toString()
            shortcuts["Move Selection Down"] = QtGui.QKeySequence("Down").toString()
            shortcuts["Move Selection Up"] = QtGui.QKeySequence("Up").toString()
            shortcuts["Toggle 1st Tag"] = QtGui.QKeySequence("1").toString()
            shortcuts["Toggle 2nd Tag"] = QtGui.QKeySequence("2").toString()
            shortcuts["Toggle 3rd Tag"] = QtGui.QKeySequence("3").toString()
            for i in range(4,8):
                shortcuts["Toggle "+str(i)+"th Tag"] = QtGui.QKeySequence(str(i)).toString()
            settings.setValue("Shortcuts",  shortcuts);

    def init_menus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"));
        self.openFile = QtGui.QAction("Open",self)
        self.fileMenu.addAction(self.openFile)
        self.openFile.triggered.connect(self.openFileClicked)

        self.saveTags = QtGui.QAction("Save Tags",self)
        self.fileMenu.addAction(self.saveTags)
        self.saveTags.triggered.connect(self.saveTagsClicked)

        self.quitAction = QtGui.QAction("Quit",self)
        self.fileMenu.addAction(self.quitAction)
        self.quitAction.triggered.connect(QtGui.QApplication.instance().quit)

        self.preferences = QtGui.QAction("Preferences",self)
        self.fileMenu.addAction(self.preferences)
        self.preferences.triggered.connect(self.preferencesClicked)

        #self.geometryMenu = self.menuBar().addMenu(self.tr("&Geometry"));
        #self.assembleGeometry = QtGui.QAction("Assemble",self)
        #self.geometryMenu.addAction(self.assembleGeometry)
        #self.assembleGeometry.triggered.connect(self.assembleGeometryClicked)
        
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"));
        self.tagsAction = QtGui.QAction("Tags...",self)
        self.editMenu.addAction(self.tagsAction)
        self.tagsAction.triggered.connect(self.tagsClicked)

        self.goMenu = self.menuBar().addMenu(self.tr("&Go"));
        act = QtGui.QAction("Previous Row",self)
        act.setShortcut(QtGui.QKeySequence.MoveToPreviousPage)
        self.goMenu.previousRow = act
        self.goMenu.addAction(act)
        act = QtGui.QAction("Next Row",self)
        act.setShortcut(QtGui.QKeySequence.MoveToNextPage)
        self.goMenu.nextRow = act
        self.goMenu.addAction(act)

        self.saveMenu = self.menuBar().addMenu(self.tr("&Save"));

        act = QtGui.QAction("To PNG",self)
        act.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        self.saveMenu.toPNG = act
        self.saveMenu.addAction(act)

        act = QtGui.QAction("Mark", self)
        act.setShortcut(QtGui.QKeySequence("Ctrl+M"))
        self.saveMenu.Mark = act
        self.saveMenu.addAction(act)

        self.viewMenu = self.menuBar().addMenu(self.tr("&View"));

        self.CXIStyleAction = QtGui.QAction("CXI Style",self)
        self.CXIStyleAction.setCheckable(True)
        self.CXIStyleAction.setChecked(False)
        self.CXIStyleAction.triggered.connect(self.toggleCXIStyleSheet)
        self.viewMenu.addAction(self.CXIStyleAction)

        self.viewMenu.addSeparator()

        act = QtGui.QAction("Full Screen",self)
        act.setShortcut(QtGui.QKeySequence("Ctrl+F"))
        act.setCheckable(True)

        act.triggered.connect(self.toggleFullScreen)
        self.viewMenu.addAction(act)

        act = QtGui.QAction("Slide Show",self)
        act.setCheckable(True)
        act.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        act.triggered.connect(self.view.view2D.toggleSlideShow)
        self.viewMenu.addAction(act)

        act = QtGui.QAction("Auto last",self)
        act.setCheckable(True)
        act.setShortcut(QtGui.QKeySequence("Ctrl+L"))
        act.triggered.connect(self.view.view2D.toggleAutoLast)
        self.viewMenu.addAction(act)

        act = QtGui.QAction("Auto update",self)
        act.setCheckable(True)
        act.setShortcut(QtGui.QKeySequence("Ctrl+U"))
        act.triggered.connect(self.toggleUpdate)
        self.viewMenu.addAction(act)

        self.viewMenu.addSeparator()

        self.viewActions = {"File Tree" : QtGui.QAction("File Tree",self),
                            "View 1D" : QtGui.QAction("View 1D",self),
                            "View 2D" : QtGui.QAction("View 2D",self),
                            "Display Properties" : QtGui.QAction("Display Properties",self),
                            "Tags" : QtGui.QAction("Tags",self),
                            "Model" : QtGui.QAction("Model",self)
                        }

        viewShortcuts = {"File Tree" : "Ctrl+T",
                         "View 1D" : "Ctrl+1",
                         "View 2D" : "Ctrl+2",
                         "Display Properties" : "Ctrl+D",
                         "Tags" : "Ctrl+G",
                         "Model" : "Ctrl+M"
                     }

        viewNames = ["File Tree", "Display Properties","View 1D","View 2D","Tags","Model"]
      
        actions = {}
        for viewName in viewNames:
            actions[viewName] = self.viewActions[viewName]
            actions[viewName].setCheckable(True)
            actions[viewName].setShortcut(QtGui.QKeySequence(viewShortcuts[viewName]))
            if(viewName == "Tags"):
                actions[viewName].triggered.connect(self.view.view2D.toggleTagView)
            elif(viewName == "Model"):
                actions[viewName].triggered.connect(self.view.view2D.toggleModelView)
            else:
                actions[viewName].triggered.connect(self.viewClicked)
            if viewName in ["View 1D"] or viewName == "Model":
                actions[viewName].setChecked(False)
            else:
                actions[viewName].setChecked(True)
            self.viewMenu.addAction(actions[viewName])
        
        self.viewMenu.addSeparator()

        icon_width = 64
        icon_height = 64
        colormapIcons = paintColormapIcons(icon_width,icon_height)

        self.colormapMenu = QtGui.QMenu("Colormap",self)
        self.colormapActionGroup = QtGui.QActionGroup(self)

        traditionalColormaps = ['jet','hot','gray','coolwarm','gnuplot','gist_earth']
        self.colormapActions = {}
        for colormap in traditionalColormaps:
            a = self.colormapMenu.addAction(colormapIcons.pop(colormap),colormap)
            a.setActionGroup(self.colormapActionGroup)
            a.setCheckable(True)
            self.colormapActions[colormap] = a

        self.exoticColormapMenu = QtGui.QMenu("Exotic",self)
        for colormap in colormapIcons.keys():
            a = self.exoticColormapMenu.addAction(colormapIcons[colormap],colormap)
            a.setActionGroup(self.colormapActionGroup)
            a.setCheckable(True)
            self.colormapActions[colormap] = a

        settings = QtCore.QSettings()
        if(settings.contains("colormap")):
            self.colormapActions[settings.value('colormap')].setChecked(True)
        else:
            self.colormapActions['jet'].setChecked(True)
        self.colormapMenu.addMenu(self.exoticColormapMenu)
        self.viewMenu.addMenu(self.colormapMenu)

        shortcuts = settings.value('Shortcuts')
        self.editMenu.toggleTag = []

        action = QtGui.QAction('Toggle 1st Tag',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 1st Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Toggle 2nd Tag',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 2nd Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Toggle 3rd Tag',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 3rd Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        for i in range(4,8):
            action = QtGui.QAction('Toggle '+str(i)+'th Tag',self)
            action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle '+str(i)+'th Tag']))
            self.addAction(action)
            self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Move Selection Right',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Right']))
        self.addAction(action)
        self.editMenu.moveSelectionRight = action

        action = QtGui.QAction('Move Selection Left',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Left']))
        self.addAction(action)
        self.editMenu.moveSelectionLeft = action

        action = QtGui.QAction('Move Selection Up',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Up']))
        self.addAction(action)
        self.editMenu.moveSelectionUp = action

        action = QtGui.QAction('Move Selection Down',self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Down']))
        self.addAction(action)
        self.editMenu.moveSelectionDown = action

    def initConnections(self):
        self.CXINavigation.CXITree.dataClicked.connect(self.handleDataClicked)
        #self.view.view1D.needData.connect(self.handleNeedDataY1D)
        self.view.view1D.dataItemXChanged.connect(self.handleDataX1DChanged)
        self.view.view1D.dataItemYChanged.connect(self.handleDataY1DChanged)
        #self.view.view2D.needDataImage.connect(self.handleNeedDataImage)
        self.view.view2D.dataItemChanged.connect(self.handleData2DChanged)
        self.CXINavigation.dataBoxes["image"].button.needData.connect(self.handleNeedDataImage)
        self.CXINavigation.dataBoxes["mask"].button.needData.connect(self.handleNeedDataMask)
        self.CXINavigation.dataMenus["mask"].triggered.connect(self.handleMaskOutBitsChanged)
        self.CXINavigation.dataBoxes["sort"].button.needData.connect(self.handleNeedDataSorting)
        self.CXINavigation.dataBoxes["plot X"].button.needData.connect(self.handleNeedDataX1D)
        self.CXINavigation.dataMenus["plot X"].triggered.connect(self.handlePlotModeTriggered)
        self.CXINavigation.dataBoxes["plot Y"].button.needData.connect(self.handleNeedDataY1D)
        self.CXINavigation.dataMenus["plot Y"].triggered.connect(self.handlePlotModeTriggered)
        self.CXINavigation.dataBoxes["filter0"].button.needData.connect(self.handleNeedDataFilter)
        self.dataProp.view1DPropChanged.connect(self.handleView1DPropChanged)
        self.dataProp.view2DPropChanged.connect(self.handleView2DPropChanged)
        self.view.view2D.pixelClicked.connect(self.dataProp.onPixelClicked)
        self.view.view2D.centralImgChanged.connect(self.dataProp.refreshDataCurrent)
        self.view.view1D.viewIndexSelected.connect(self.handleViewIndexSelected)
        self.goMenu.nextRow.triggered.connect(self.view.view2D.nextRow)
        self.goMenu.previousRow.triggered.connect(self.view.view2D.previousRow)
        self.saveMenu.toPNG.triggered.connect(self.view.view2D.saveToPNG)
        self.saveMenu.Mark.triggered.connect(self.view.view2D.addtoMarked)
        for i in range(0,len(self.editMenu.toggleTag)):
            self.editMenu.toggleTag[i].triggered.connect(lambda id=i: self.dataProp.toggleTag(id))
        self.editMenu.moveSelectionRight.triggered.connect(lambda: self.view.view2D.moveSelectionBy(1,0))
        self.editMenu.moveSelectionLeft.triggered.connect(lambda: self.view.view2D.moveSelectionBy(-1,0))
        self.editMenu.moveSelectionUp.triggered.connect(lambda: self.view.view2D.moveSelectionBy(0,-1))
        self.editMenu.moveSelectionDown.triggered.connect(lambda: self.view.view2D.moveSelectionBy(0,1))

	#self.dataProp.imageStackMeanButton.released.connect(lambda: self.handleNeedDataIntegratedImage("mean"))
	#self.dataProp.imageStackStdButton.released.connect(lambda: self.handleNeedDataIntegratedImage("std"))
	#self.dataProp.imageStackMinButton.released.connect(lambda: self.handleNeedDataIntegratedImage("min"))
	#self.dataProp.imageStackMaxButton.released.connect(lambda: self.handleNeedDataIntegratedImage("max"))

        self.fileLoader.stackSizeChanged.connect(self.onStackSizeChanged)

    def openFileClicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,"Open CXI File", None, "CXI Files (*.cxi)");
        if(fileName[0]):
            self.openCXIFile(fileName[0])
    def saveTagsClicked(self):
        self.fileLoader.saveTags()
    def setStyleSheetFromFilename(self,fn="stylesheets/default.stylesheet"):
        styleFile=os.path.join(os.path.split(__file__)[0],fn)
        with open(styleFile,"r") as fh:
            self.setStyleSheet(fh.read())
    def toggleCXIStyleSheet(self):
        if self.CXIStyleAction.isChecked():
            self.setStyleSheetFromFilename("stylesheets/dark.stylesheet")
        else:
            self.setStyleSheetFromFilename()
            #self.setStyle("")
    def assembleGeometryClicked(self):
        self.geometry.assemble_detectors(self.CXINavigation.CXITreeTop.f)
    def viewClicked(self):
        viewName = self.sender().text()
        checked = self.viewActions[viewName].isChecked()
        viewBoxes = {"File Tree" : [self.CXINavigation],
                     "Display Properties" : [self.dataProp],
                     "View 1D" : [self.view.view1D,self.dataProp.plotBox],
                     "View 2D" : [self.view.view2DScrollWidget,self.dataProp.imageBox,self.dataProp.displayBox,self.dataProp.imageStackBox, self.dataProp.generalBox, self.dataProp.pixelBox]
                 }
        boxes = viewBoxes[viewName]
        if(checked):
            self.statusBar.showMessage("Showing %s" % viewName,1000)
            for box in boxes:
                box.show()
        else:
            self.statusBar.showMessage("Hiding %s" % viewName,1000)
            for box in boxes:
                box.hide()
    def toggleFullScreen(self):
        if self.windowState() & QtCore.Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()
    def closeEvent(self,event):
        if(self.tagsChanged and 
           QtGui.QMessageBox.question(self,"Save tag changes?",
                                      "Would you like to save changes to the tags?",
                                      QtGui.QMessageBox.Save,QtGui.QMessageBox.Discard) == QtGui.QMessageBox.Save):
            self.fileLoader.saveTags()
        settings = QtCore.QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("colormap", self.dataProp.view2DProp['colormapText'])
        settings.setValue("normScaling", self.dataProp.view2DProp['normScaling'])
        settings.setValue("normGamma", self.dataProp.view2DProp['normGamma'])
        settings.setValue("normClamp", self.dataProp.view2DProp['normClamp'])
        settings.setValue("normVmin", self.dataProp.view2DProp['normVmin'])
        settings.setValue("normVmax", self.dataProp.view2DProp['normVmax'])
        QtGui.QMainWindow.closeEvent(self,event)
    def preferencesClicked(self):
	diag = PreferencesDialog(self)
        settings = QtCore.QSettings()
        if(diag.exec_()):
            if(diag.natural.isChecked()):
                settings.setValue("scrollDirection",-1)
            else:
                settings.setValue("scrollDirection",1)
            v = diag.imageCacheSpin.value()
            settings.setValue("imageCacheSize",v)
            self.view.view2D.loaderThread.imageData.setSizeInBytes(v*1024*1024)
            v = diag.imageCacheSpin.value()
            settings.setValue("phaseCacheSize",v)
            self.view.view2D.loaderThread.phaseData.setSizeInBytes(v*1024*1024)
            v = diag.maskCacheSpin.value()
            settings.setValue("maskCacheSize",v)
            self.view.view2D.loaderThread.maskData.setSizeInBytes(v*1024*1024)
            v = diag.textureCacheSpin.value()
            settings.setValue("textureCacheSize",v)
            self.view.view2D.imageTextures.setSizeInBytes(v*1024*1024)
            v = diag.updateTimerSpin.value()
            settings.setValue("updateTimer",v)
            self.updateTimer.setInterval(v)
            v = diag.movingAverageSizeSpin.value()
            settings.setValue("movingAverageSize",v)
            self.view.view1D.setWindowSize(v)
            v = diag.PNGOutputPath.text()
            settings.setValue("PNGOutputPath",v)
            self.view.view2D.PNGOutputPath = v
            v = diag.MarkOutputPath.text()
            settings.setValue("MarkOutputPath",v)
            self.view.view2D.MarkOutputPath = v

            shortcuts = settings.value("Shortcuts")
            for r in range(0,diag.shortcutsTable.rowCount()):
                name = diag.shortcutsTable.verticalHeaderItem(r).text()            
                string =  QtGui.QKeySequence.fromString(diag.shortcutsTable.item(r,0).text(),QtGui.QKeySequence.NativeText).toString()
                shortcuts[name] = string
            settings.setValue("Shortcuts",shortcuts)

            self.editMenu.moveSelectionDown.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Down']))
            self.editMenu.moveSelectionUp.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Up']))
            self.editMenu.moveSelectionLeft.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Left']))
            self.editMenu.moveSelectionRight.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Right']))
            
            self.editMenu.toggleTag[0].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 1st Tag']))
            self.editMenu.toggleTag[1].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 2nd Tag']))
            self.editMenu.toggleTag[2].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 3rd Tag']))
            for i in range(3,6):
                self.editMenu.toggleTag[i].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle '+str(i+1)+'th Tag']))

    def handleNeedDataImage(self,dataName=None):
        if dataName == "" or dataName == None:
            self.CXINavigation.CXITree.loadData1()
            return
        dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
        if not dataItem.isPresentable:
            self.statusBar.showMessage("Data not presentable.")
            return
        if dataItem.format == 2:
            self.CXINavigation.dataBoxes["image"].button.setName(dataName)
            self.view.view2D.clear()
            self.view.view2D.loadStack(dataItem)
            self.statusBar.showMessage("Loaded %s" % dataItem.fullName,1000)
        else:
            QtGui.QMessageBox.warning(self,self.tr("CXI Viewer"),self.tr("Cannot sort with a data that has more than one dimension. The selected data has %d dimensions." %(len(dataItem.shape()))))
        self.dataProp.setData(dataItem)
        group = dataName.rsplit("/",1)[0]
        if "mask" in dataName:
            self.handleNeedDataMask()
        elif self.CXINavigation.dataBoxes["mask"].button.text().rsplit("/",1)[0] != group:
            if group+"/mask" in self.CXINavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask")
            elif group+"/mask_shared" in self.CXINavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask_shared")
        self.view.view2DScrollWidget.update()
    def handleNeedDataIntegratedImage(self,integrationMode):
	self.view.view2D.integrationMode = integrationMode
	self.view.view2D.clearTextures()
    def handleNeedDataMask(self,dataName=None):
        if dataName == "" or dataName == None:
            self.view.view2D.setMask()
            self.view.view2D.clearTextures()
            self.view.view2D.updateGL()
            self.CXINavigation.dataBoxes["mask"].button.setName()
            self.statusBar.showMessage("Reset mask.",1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            maskShape = (dataItem.shape()[-2],dataItem.shape()[-1])
            imageShape = (self.view.view2D.data.shape()[-2],self.view.view2D.data.shape()[-1])
            if maskShape != imageShape:
                self.statusBar.showMessage("Mask shape missmatch. Do not load mask: %s" % dataItem.fullName,1000)
            else:
                self.view.view2D.setMask(dataItem)
                self.view.view2D.clearTextures()
                self.view.view2D.updateGL()
                self.CXINavigation.dataBoxes["mask"].button.setName(dataName)
                self.statusBar.showMessage("Loaded mask: %s" % dataName,1000)
        # needed?
        self.handleMaskOutBitsChanged()
    def handleMaskOutBitsChanged(self,action=None):
        self.view.view2D.setMaskOutBits(self.CXINavigation.dataMenus["mask"].getMaskOutBits())
        #self.view.view2D.clearTextures()
        self.view.view2D.updateGL()
    def handleNeedDataFilter(self,dataName):
        senderBox = self.sender().dataBox
        # add or replace first filter
        if self.CXINavigation.dataBoxes["filter0"] == senderBox:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            if not dataItem.isStack:
                self.statusBar.showMessage("Data item is not a stack and therefore it can not be used as a filter.")
            else:
                nDims = len(dataItem.shape())
                if (nDims == 1) or (nDims == 2):
                    if nDims == 1:
                        targetBox = self.CXINavigation.addFilterBox()
                        self.dataProp.addFilter(dataItem)
                        self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                        targetBox.button.setName(dataName)
                        targetBox.button.needData.connect(self.handleNeedDataFilter)
                    else:
                        selIndDialog = SelectIndexDialog(self,dataItem)
                        if(selIndDialog.exec_() == QtGui.QDialog.Accepted):
                            while dataItem.selectedIndex == None: time.sleep(0.1)
                            targetBox = self.CXINavigation.addFilterBox()
                            self.dataProp.addFilter(dataItem)
                            self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                            targetBox.button.setName(dataName)
                            targetBox.button.needData.connect(self.handleNeedDataFilter)
                else:
                    self.statusBar.showMessage("Data item has incorrect format for becoming a filter.")
        # add, replace or remove secondary filter
        else:
            i = self.CXINavigation.dataBoxes["filters"].index(senderBox)
            if dataName == "" or dataName == None:
                self.dataProp.removeFilter(i)
                self.CXINavigation.removeFilterBox(senderBox)
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
            else:
                targetBox = senderBox
                dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
                if not dataItem.isPresentable:
                    self.statusBar.showMessage("Data not presentable.")
                    return
                self.dataProp.refreshFilter(dataItem,i)
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                targetBox.button.setName(dataName)
                self.statusBar.showMessage("Loaded filter data: %s" % dataName,1000)
    def handleNeedDataSorting(self,dataName):
        if dataName == "" or dataName == None:
            self.CXINavigation.dataBoxes["sort"].button.setName()
            self.dataProp.clearSorting()
            self.dataProp.setSorting()
            self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
            self.statusBar.showMessage("Reset sorting.",1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            if dataItem.format == 0 and dataItem.isStack:
                self.CXINavigation.dataBoxes["sort"].button.setName(dataName)
                self.dataProp.refreshSorting(dataItem)
                self.dataProp.setSorting()
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                self.view.view1D.refreshPlot()
                self.statusBar.showMessage("Loaded sorting data: %s" % dataName,1000)
            else:
                self.statusBar.showMessage("Data has inadequate shape for sorting stack: %s" % dataName,1000)
    def handleNeedDataX1D(self,dataName):
        if dataName == "" or dataName == None:
            self.view.view1D.setDataItemX(None)
            self.view.view1D.refreshPlot()
            self.statusBar.showMessage("Reset X data for plot." % dataName,1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            self.view.view1D.setDataItemX(dataItem)
            self.view.view1D.refreshPlot()
            #self.CXINavigation.dataBoxes["plot X"].button.setName(dataName)
            self.statusBar.showMessage("Loaded X data for plot: %s" % dataName,1000)
    def handleNeedDataY1D(self,dataName):
        if dataName == "" or dataName == None:
            self.view.view1D.setDataItemY(None)
            self.view.view1D.refreshPlot()
            self.view.view1D.hide()
            self.dataProp.plotBox.hide()
            self.viewActions["View 1D"].setChecked(False)
            self.statusBar.showMessage("Reset Y data for plot." % dataName,1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            self.view.view1D.setDataItemY(dataItem)
            self.view.view1D.refreshPlot()
            #self.CXINavigation.dataBoxes["plot Y"].button.setName(dataName)
            self.view.view1D.show()
            self.dataProp.plotBox.show()
            self.viewActions["View 1D"].setChecked(True)
            self.statusBar.showMessage("Loaded Y data for plot: %s" % dataName,1000)
    #def handleView1DPropChanged(self,prop):
    #    self.view.view1D.show()
    #    self.dataProp.plotBox.show()
    #    self.viewActions["View 1D"].setChecked(True)
    #    self.view.view1D.setProps(prop)
        #self.CXINavigation.dataBoxes["plot"].button.setName("%s (%i,%i)" % (dataName,ix,iy))
        #self.statusBar.showMessage("Loaded pixel stack to plot: %s (%i,%i)" % (data.name,iy,ix),1000)
    def handlePlotModeTriggered(self,foovalue=None):
        self.view.view1D.setPlotMode(self.CXINavigation.dataMenus["plot Y"].getPlotMode())
        self.view.view1D.refreshPlot()
        if self.view.view1D.dataItemY != None:
            self.viewActions["View 1D"].setChecked(True)
            self.view.view1D.show()
            self.dataProp.plotBox.show()
        else:
            self.viewActions["View 1D"].setChecked(False)
            self.view.view1D.hide()
            self.dataProp.plotBox.hide()
    def handleView2DPropChanged(self,prop):
        self.view.view2D.refreshDisplayProp(prop)
    def handleView1DPropChanged(self,prop):
        self.view.view1D.refreshDisplayProp(prop)
    def handleDataClicked(self,dataName):
        dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
        if (dataItem.format == 0 and dataItem.isStack) or (dataItem.format == 1 and not dataItem.isStack):
            self.handleNeedDataY1D(dataName)
        elif dataItem.format == 2:
            if dataName[-4:] == "mask":
                self.handleNeedDataMask(dataName)
            else:
                self.handleNeedDataImage(dataName)
    def handleDataX1DChanged(self,dataItem):
        n = None
        if dataItem != None:
            if hasattr(dataItem,"fullName"):
                n = dataItem.fullName
        self.CXINavigation.dataBoxes["plot X"].button.setName(n)
    def handleDataY1DChanged(self,dataItem):
        n = None
        if dataItem != None:
            if hasattr(dataItem,"fullName"):
                n = dataItem.fullName
        self.CXINavigation.dataBoxes["plot Y"].button.setName(n)
    def handleData2DChanged(self,dataItemData,dataItemMask):
        dataItems = {"image":dataItemData,"mask":dataItemMask}
        for k in dataItems.keys():
            n = None
            if dataItems[k] != None:
                if hasattr(dataItems[k],"fullName"):
                    n = dataItems[k].fullName
            self.CXINavigation.dataBoxes[k].button.setName(n)
    def onStackSizeChanged(self,newStackSize=0):
        self.indexProjector.onStackSizeChanged(newStackSize)
        self.view.view2D.onStackSizeChanged(newStackSize)
        self.view.view1D.onStackSizeChanged(newStackSize)
        self.dataProp.onStackSizeChanged(newStackSize)
    def handleMask2DChanged(self,dataItem):
        n = None
        if dataItem != None:
            if hasattr(dataItem,"fullName"):
                n = dataItem.fullName
        self.CXINavigation.dataBoxes["image"].button.setName(n)
    def handleViewIndexSelected(self,index):
        self.view.view2D.browseToViewIndex(index)
    def toggleUpdate(self):
        if self.updateTimer.isActive():
            self.updateTimer.stop()
        else:
            self.updateTimer.start()
    def tagsClicked(self):
        if(self.view.view2D.data):
            tagsDialog = TagsDialog(self,self.view.view2D.data.tags);
            if(tagsDialog.exec_() == QtGui.QDialog.Accepted):
                tags = tagsDialog.getTags()
                if(tags != self.view.view2D.data.tags):
                    self.view.view2D.data.setTags(tags)
                    self.dataProp.showTags(self.view.view2D.data)
                    self.tagsChanged = True
                    
                
        else:
            QtGui.QMessageBox.information(self,"Cannot set tags","Cannot set tags if no dataset is open.");
        


class TagsDialog(QtGui.QDialog, tagsDialog.Ui_TagsDialog):
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
        if(title == None):
            title = "Tag "+str(self.colorIndex)
        item = QtGui.QTableWidgetItem(title)
        item.setTextAlignment(QtCore.Qt.AlignHCenter|QtCore.Qt.AlignVCenter)
        item.setToolTip("Double click to change name")
        self.tagsTable.setItem(0,self.tagsTable.columnCount()-1,item)

        # The Tag color
        item = QtGui.QTableWidgetItem()
        item.setFlags(QtCore.Qt.ItemIsEnabled)
        if(color == None):
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

class SelectIndexDialog(QtGui.QDialog, selectIndexDialog.Ui_SelectIndexDialog):
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
            nDims = len(self.dataItem.attr("headings"))
        self.labels = []
        for i in range(nDims):
            self.labels.append("%i" % i)
        if isTags:
            for i,tag in zip(range(nDims),self.dataItem.tags):
                title = tag[0]
                self.labels[i] += " " + title
        self.comboBox.addItems(self.labels)

    def onOkButtonClicked(self):
        self.dataItem.selectedIndex = self.comboBox.currentIndex()
        self.accept()
                

class PreferencesDialog(QtGui.QDialog, preferencesDialog.Ui_PreferencesDialog):
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
        self.textureCacheSpin.setValue(int(settings.value("textureCacheSize")))
        self.updateTimerSpin.setValue(int(settings.value("updateTimer")))
        self.movingAverageSizeSpin.setValue(float(settings.value("movingAverageSize")))
        self.PNGOutputPath.setText(settings.value("PNGOutputPath"))
        self.MarkOutputPath.setText(settings.value("MarkOutputPath"))
        self.shortcutsTable.installEventFilter(self)
        shortcuts = settings.value("Shortcuts")
        for r in range(0,self.shortcutsTable.rowCount()):
            name = self.shortcutsTable.verticalHeaderItem(r).text()
            if(name in shortcuts.keys()):
                string =  QtGui.QKeySequence.fromString(shortcuts[name]).toString(QtGui.QKeySequence.NativeText)
                self.shortcutsTable.item(r,0).setText(string)
            
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

def exceptionHandler(type, value, traceback):
    sys.__excepthook__(type,value,traceback)
    app.exit()
    sys.exit(-1)

    
logging.basicConfig()
QtCore.QCoreApplication.setOrganizationName("CXIDB");
QtCore.QCoreApplication.setOrganizationDomain("cxidb.org");
QtCore.QCoreApplication.setApplicationName("owl");
if hasattr(sys, 'argv'):
    app = QtGui.QApplication(sys.argv)
else:
    app = QtGui.QApplication([])

parser = argparse.ArgumentParser(description='')
parser.add_argument('-d','--debug',dest='debuggingMode', action='store_true',help='debugging mode')
parser.add_argument('filename',nargs="?",type=str,help='CXI file to load',default="")
args = parser.parse_args()

if args.debuggingMode:
    # Set exception handler
    print "Running owl in debugging mode."
    sys.excepthook = exceptionHandler

aw = Viewer()
aw.show()
ret = app.exec_()
aw.view.view2D.stopThreads()
sys.exit(ret)
