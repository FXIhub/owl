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
from geometry import *
from dataprop import *
from dataloader import *
from cxitree import *
from view import *
from viewsplitter import ViewSplitter
import logging
import argparse
import gc
import time


"""
Wishes:

Infinite subplots
Color tagged images
Double click to zoom on image (double click again zoom back to width of column). Also changes to 1 column view
View only tagged ones
Tagging with numbers
Different tags different colors
Multiple tags per image


"""

        
class Viewer(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Initializing...")
        self.init_settings()
        self.splitter = QtGui.QSplitter(self)        
        self.view = ViewSplitter(self)
        self.init_menus()


        self.dataProp = DataProp(self)
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
        self.updateTimer.timeout.connect(self.updateData)

        self.initConnections()
        self.dataProp.emitView1DProp()
        self.dataProp.emitView2DProp()
        self.setStyleSheetFromFilename()

    def after_show(self):
        if(args.filename != ""):
            self.openCXIFile(args.filename)        
    def openCXIFile(self,filename):
	self.filename = filename
        self.fileLoader = FileLoader(filename)
        self.CXINavigation.CXITree.buildTree(self.fileLoader)
    def init_settings(self):
        settings = QtCore.QSettings()
        if(not settings.contains("scrollDirection")):
            settings.setValue("scrollDirection", 1);  
        if(not settings.contains("imageCacheSize")):
            # Default to 1 GB
            settings.setValue("imageCacheSize", 1024);  
        if(not settings.contains("maskCacheSize")):
            # Default to 1 GB
            settings.setValue("maskCacheSize", 1024);  
        if(not settings.contains("textureCacheSize")):
            # Default to 256 MB
            settings.setValue("textureCacheSize", 256);  
        if(not settings.contains("updateTimer")):
            settings.setValue("updateTimer", 10000);
        if(not settings.contains("PNGOutputPath")):
            settings.setValue("PNGOutputPath", "./");
    def init_menus(self):
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"));
        self.openFile = QtGui.QAction("Open",self)
        self.fileMenu.addAction(self.openFile)
        self.openFile.triggered.connect(self.openFileClicked)
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
                            "Display Properties" : QtGui.QAction("Display Properties",self)}

        viewShortcuts = {"File Tree" : "Ctrl+T",
                         "View 1D" : "Ctrl+1",
                         "View 2D" : "Ctrl+2",
                         "Display Properties" : "Ctrl+D"}

        viewNames = ["File Tree", "Display Properties","View 1D","View 2D"]
      
        actions = {}
        for viewName in viewNames:
            actions[viewName] = self.viewActions[viewName]
            actions[viewName].setCheckable(True)
            actions[viewName].setShortcut(QtGui.QKeySequence(viewShortcuts[viewName]))
            actions[viewName].triggered.connect(self.viewClicked)
            if viewName in ["View 1D"]:
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

	self.dataProp.imageStackMeanButton.released.connect(lambda: self.handleNeedDataIntegratedImage("mean"))
	self.dataProp.imageStackStdButton.released.connect(lambda: self.handleNeedDataIntegratedImage("std"))
	self.dataProp.imageStackMinButton.released.connect(lambda: self.handleNeedDataIntegratedImage("min"))
	self.dataProp.imageStackMaxButton.released.connect(lambda: self.handleNeedDataIntegratedImage("max"))

    def openFileClicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,"Open CXI File", None, "CXI Files (*.cxi)");
        if(fileName[0]):
            self.openCXIFile(fileName[0])
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
                     "View 2D" : [self.view.view2D,self.dataProp.imageBox,self.dataProp.displayBox,self.dataProp.imageStackBox]}
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
            v = diag.maskCacheSpin.value()
            settings.setValue("maskCacheSize",v)
            self.view.view2D.loaderThread.maskData.setSizeInBytes(v*1024*1024)
            v = diag.textureCacheSpin.value()
            settings.setValue("textureCacheSize",v)
            self.view.view2D.imageTextures.setSizeInBytes(v*1024*1024)
            v = diag.updateTimerSpin.value()
            settings.setValue("updateTimer",v)
            self.updateTimer.setInterval(v)
            v = diag.PNGOutputPath.text()
            settings.setValue("PNGOutputPath",v)
            self.view.view2D.PNGOutputPath = v
    def handleNeedDataImage(self,dataName=None):
        if str(dataName) == "":
            self.CXINavigation.CXITree.loadData1()
            return
        dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
        if dataItem.format == 2:        
            self.CXINavigation.dataBoxes["image"].button.setName(dataName)
            self.view.view2D.clear()
            if dataItem.isStack:
                self.view.view2D.loadStack(dataItem)
                self.statusBar.showMessage("Loaded image stack: %s" % dataItem.fullName,1000)
            else:
                self.view.view2D.loadImage(dataItem)
                self.statusBar.showMessage("Loaded image: %s" % dataItem.fullName,1000)
        else:
            QtGui.QMessageBox.warning(self,self.tr("CXI Viewer"),self.tr("Cannot sort with a data that has more than one dimension. The selected data has %d dimensions." %(len(dataItem.shape()))))
        self.dataProp.setData(dataItem)
        group = dataName.rsplit("/",1)[0]
        if self.CXINavigation.dataBoxes["mask"].button.text().rsplit("/",1)[0] != group:
            if group+"/mask" in self.CXINavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask")
            elif group+"/mask_shared" in self.CXINavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask_shared")
        self.view.view2DScrollWidget.update()
        self.updateData()
    def handleNeedDataIntegratedImage(self,integrationMode):
	self.view.view2D.integrationMode = integrationMode
	self.view.view2D.updateStackSize(True)
	self.view.view2D.clearTextures()
    def handleNeedDataMask(self,dataName=None):
        if str(dataName) == "":
            self.view.view2D.setMask()
            self.view.view2D.clearTextures()
            self.view.view2D.updateGL()
            self.CXINavigation.dataBoxes["mask"].button.setName()
            self.statusBar.showMessage("Reset mask.",1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
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
        if self.CXINavigation.dataBoxes["filter0"] == senderBox:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            if dataItem.format == 1:
                targetBox = self.CXINavigation.addFilterBox()
                self.dataProp.addFilter(dataItem)
                self.dataProp.displayPropChanged.emit(self.dataProp.view2DProp)
                targetBox.button.setName(dataName)
                targetBox.button.needData.connect(self.handleNeedDataFilter)
        else:
            i = self.CXINavigation.dataBoxes["filters"].index(senderBox)
            if str(dataName) == "":
                self.dataProp.removeFilter(i)
                self.CXINavigation.removeFilterBox(senderBox)
                self.dataProp.displayPropChanged.emit(self.dataProp.view2DProp)
            else:
                targetBox = senderBox
                dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
                self.dataProp.refreshFilter(dataItem,i)
                self.dataProp.displayPropChanged.emit(self.dataProp.view2DProp)
                targetBox.button.setName(dataName)
                self.statusBar.showMessage("Loaded filter data: %s" % dataName,1000)
    def handleNeedDataSorting(self,dataName):
        if str(dataName) == "":
            self.CXINavigation.dataBoxes["sort"].button.setName()
            self.dataProp.clearSorting()
            self.dataProp.setSorting()
            self.dataProp.displayPropChanged.emit(self.dataProp.view2DProp)
            self.statusBar.showMessage("Reset sorting.",1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
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
        if str(dataName) == "":
            self.view.view1D.setDataItemX(None)
            self.view.view1D.refreshPlot()
            self.statusBar.showMessage("Reset X data for plot." % dataName,1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            self.view.view1D.setDataItemX(dataItem)
            self.view.view1D.refreshPlot()
            #self.CXINavigation.dataBoxes["plot X"].button.setName(dataName)
            self.statusBar.showMessage("Loaded X data for plot: %s" % dataName,1000)
    def handleNeedDataY1D(self,dataName):
        if str(dataName) == "":
            self.view.view1D.setDataItemY(None)
            self.view.view1D.refreshPlot()
            self.view.view1D.hide()
            self.dataProp.plotBox.hide()
            self.viewActions["View 1D"].setChecked(False)
            self.statusBar.showMessage("Reset Y data for plot." % dataName,1000)
        else:
            dataItem = self.CXINavigation.CXITree.fileLoader.dataItems[dataName]
            self.view.view1D.setDataItemY(dataItem)
            self.view.view1D.refreshPlot()
            #self.CXINavigation.dataBoxes["plot Y"].button.setName(dataName)
            self.view.view1D.show()
            self.dataProp.plotBox.show()
            self.viewActions["View 1D"].setChecked(True)
            self.statusBar.showMessage("Loaded Y data for plot: %s" % dataName,1000)
    def handleView1DPropChanged(self,prop):
        self.view.view1D.show()
        self.dataProp.plotBox.show()
        self.viewActions["View 1D"].setChecked(True)
        self.view.view1D.setProps(prop)
        #self.CXINavigation.dataBoxes["plot"].button.setName("%s (%i,%i)" % (dataName,ix,iy))
        #self.statusBar.showMessage("Loaded pixel stack to plot: %s (%i,%i)" % (data.name,iy,ix),1000)
    def handlePlotModeTriggered(self,foovalue=None):
        self.view.view1D.setPlotMode(self.CXINavigation.dataMenus["plot Y"].getPlotMode())
        self.view.view1D.refreshPlot()
        if self.view.view1D.dataY != None:
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
    def updateData(self):
        self.view.view2D.updateStackSize()
        self.view.view1D.refreshPlot()

class PreferencesDialog(QtGui.QDialog):
    def __init__(self,parent):
        QtGui.QDialog.__init__(self,parent,QtCore.Qt.WindowTitleHint)
        self.resize(300,150)

        settings = QtCore.QSettings()

        buttonBox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
        buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel)
        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)
        self.setLayout(QtGui.QVBoxLayout());
        row = 0
        grid = QtGui.QGridLayout()
        grid.addWidget(QtGui.QLabel("Scroll Direction:",self),row,0)
        self.natural = QtGui.QRadioButton("Natural (Mac)")
        self.traditional = QtGui.QRadioButton("Traditional (Pc)")
        if(settings.value("scrollDirection") == -1):
            self.natural.setChecked(True)
            self.traditional.setChecked(False)
        else:
            self.natural.setChecked(False)
            self.traditional.setChecked(True)
        grid.addWidget(self.traditional,row,1)
        row += 1
        grid.addWidget(self.natural,row,1)
        row += 1
        #    We'll need this when we add more options
        f = QtGui.QFrame(self)
        f.setFrameStyle(QtGui.QFrame.HLine | (QtGui.QFrame.Sunken))
        grid.addWidget(f,row,0,1,2);
        row += 1

        grid.addWidget(QtGui.QLabel("Image Cache (in MB):",self),row,0)
        self.imageCacheSpin = QtGui.QSpinBox()
        self.imageCacheSpin.setMaximum(1024*1024*1024)
        self.imageCacheSpin.setSingleStep(512)
        self.imageCacheSpin.setValue(int(settings.value("imageCacheSize")))
        grid.addWidget(self.imageCacheSpin,row,1)
        row += 1

        grid.addWidget(QtGui.QLabel("Mask Cache (in MB):",self),row,0)
        self.maskCacheSpin = QtGui.QSpinBox()
        self.maskCacheSpin.setMaximum(1024*1024*1024)
        self.maskCacheSpin.setSingleStep(512)
        self.maskCacheSpin.setValue(int(settings.value("maskCacheSize")))
        grid.addWidget(self.maskCacheSpin,row,1)
        row += 1

        grid.addWidget(QtGui.QLabel("Texture Cache (in MB):",self),row,0)
        self.textureCacheSpin = QtGui.QSpinBox()
        self.textureCacheSpin.setMaximum(1024*1024*1024)
        self.textureCacheSpin.setSingleStep(128)
        self.textureCacheSpin.setValue(int(settings.value("textureCacheSize")))
        grid.addWidget(self.textureCacheSpin,row,1)
        row += 1

        f = QtGui.QFrame(self)
        f.setFrameStyle(QtGui.QFrame.HLine | (QtGui.QFrame.Sunken))
        grid.addWidget(f,row,0,1,2);
        row += 1

        grid.addWidget(QtGui.QLabel("Auto update timer (in ms):",self),row,0)
        self.updateTimerSpin = QtGui.QSpinBox()
        self.updateTimerSpin.setMaximum(86400000)
        self.updateTimerSpin.setSingleStep(1000)
        self.updateTimerSpin.setValue(int(settings.value("updateTimer")))
        grid.addWidget(self.updateTimerSpin,row,1)
        row += 1

        grid.addWidget(QtGui.QLabel("PNG output path:",self),row,0)
        self.PNGOutputPath = QtGui.QLineEdit()
        self.PNGOutputPath.setText(settings.value("PNGOutputPath"))
        grid.addWidget(self.PNGOutputPath,row,1)
        row += 1

        self.layout().addLayout(grid)
        self.layout().addStretch()

        f = QtGui.QFrame(self)
        f.setFrameStyle(QtGui.QFrame.HLine | (QtGui.QFrame.Sunken)) 
        self.layout().addWidget(f)
        self.layout().addWidget(buttonBox)


def exceptionHandler(type, value, traceback):
    sys.__excepthook__(type,value,traceback)    
    app.exit()
    sys.exit(-1)

    
logging.basicConfig()

QtCore.QCoreApplication.setOrganizationName("CXIDB");
QtCore.QCoreApplication.setOrganizationDomain("cxidb.org");
QtCore.QCoreApplication.setApplicationName("CXI Viewer");
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
