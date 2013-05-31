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
from datasetprop import *
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


        self.datasetProp = DatasetProp(self)
        self.CXINavigation = CXINavigation(self)
        self.splitter.addWidget(self.CXINavigation)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.datasetProp)

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
        self.datasetProp.emitDisplayProp()

        self.setStyle()

    def after_show(self):
        if(args.filename != ""):
            self.openCXIFile(args.filename)        
    def openCXIFile(self,filename):
	self.filename = filename
        self.CXINavigation.CXITree.buildTree(filename)
        self.handleNeedDatasetImage("/entry_1/data_1/data")
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
        self.CXIStyleAction.triggered.connect(self.setCXIStyle)
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
        self.CXINavigation.CXITree.datasetClicked.connect(self.handleDatasetClicked)
        self.view.view1D.needDataset.connect(self.handleNeedDatasetY1D)
        self.view.view1D.datasetXChanged.connect(self.handleDatasetX1DChanged)
        self.view.view1D.datasetYChanged.connect(self.handleDatasetY1DChanged)
        self.view.view2D.needDataset.connect(self.handleNeedDatasetImage)
        self.view.view2D.datasetChanged.connect(self.handleDataset2DChanged)
        self.CXINavigation.datasetBoxes["image"].button.needDataset.connect(self.handleNeedDatasetImage)
        self.CXINavigation.datasetBoxes["mask"].button.needDataset.connect(self.handleNeedDatasetMask)
        self.CXINavigation.datasetMenus["mask"].triggered.connect(self.handleMaskOutBitsChanged)
        self.CXINavigation.datasetBoxes["sort"].button.needDataset.connect(self.handleNeedDatasetSorting)
        self.CXINavigation.datasetBoxes["plot X"].button.needDataset.connect(self.handleNeedDatasetX1D)
        self.CXINavigation.datasetMenus["plot X"].triggered.connect(self.handlePlotModeTriggered)
        self.CXINavigation.datasetBoxes["plot Y"].button.needDataset.connect(self.handleNeedDatasetY1D)
        self.CXINavigation.datasetMenus["plot Y"].triggered.connect(self.handlePlotModeTriggered)
        self.CXINavigation.datasetBoxes["filter0"].button.needDataset.connect(self.handleNeedDatasetFilter)
        self.datasetProp.displayPropChanged.connect(self.handleDisplayPropChanged)
        self.datasetProp.pixelStackChanged.connect(self.handlePixelStackChanged)
        self.view.view2D.pixelClicked.connect(self.datasetProp.onPixelClicked)
        self.view.view2D.centralImgChanged.connect(self.datasetProp.refreshDatasetCurrent)
        self.view.view1D.viewIndexSelected.connect(self.handleViewIndexSelected)   
        self.goMenu.nextRow.triggered.connect(self.view.view2D.nextRow)
        self.goMenu.previousRow.triggered.connect(self.view.view2D.previousRow)
	self.saveMenu.toPNG.triggered.connect(self.view.view2D.saveToPNG)

	self.datasetProp.imageStackMeanButton.released.connect(lambda: self.handleNeedDatasetIntegratedImage("mean"))
	self.datasetProp.imageStackStdButton.released.connect(lambda: self.handleNeedDatasetIntegratedImage("std"))
	self.datasetProp.imageStackMinButton.released.connect(lambda: self.handleNeedDatasetIntegratedImage("min"))
	self.datasetProp.imageStackMaxButton.released.connect(lambda: self.handleNeedDatasetIntegratedImage("max"))
        self.datasetProp.plotLinesCheckBox.toggled.connect(self.view.view1D.onTogglePlotLines)
        self.datasetProp.plotPointsCheckBox.toggled.connect(self.view.view1D.onTogglePlotPoints)
        self.datasetProp.plotNBinsEdit.editingFinished.connect(self.view.view1D.onPlotNBinsEdit)
        self.datasetProp.imageStackNEdit.textChanged.connect(self.view.view2D.onImageStackNEdit)

    def openFileClicked(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,"Open CXI File", None, "CXI Files (*.cxi)");
        if(fileName[0]):
            self.openCXIFile(fileName[0])
    def setStyle(self,fn="stylesheets/default.stylesheet"):
        styleFile=os.path.join(os.path.split(__file__)[0],fn)
        with open(styleFile,"r") as fh:
            self.setStyleSheet(fh.read())
    def setCXIStyle(self):
        if self.CXIStyleAction.isChecked():
            self.setStyle("stylesheets/dark.stylesheet")
        else:
            self.setStyle()
            #self.setStyle("")
    def assembleGeometryClicked(self):
        self.geometry.assemble_detectors(self.CXINavigation.CXITreeTop.f)
    def viewClicked(self):
        viewName = self.sender().text()
        checked = self.viewActions[viewName].isChecked()
        viewBoxes = {"File Tree" : [self.CXINavigation],
                     "Display Properties" : [self.datasetProp],
                     "View 1D" : [self.view.view1D,self.datasetProp.plotBox],
                     "View 2D" : [self.view.view2D,self.datasetProp.imageBox,self.datasetProp.displayBox,self.datasetProp.imageStackBox]}
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
        settings.setValue("colormap", self.datasetProp.currDisplayProp['colormapText']) 
        settings.setValue("normScaling", self.datasetProp.currDisplayProp['normScaling'])
        settings.setValue("normGamma", self.datasetProp.currDisplayProp['normGamma'])
        settings.setValue("normClamp", self.datasetProp.currDisplayProp['normClamp'])
        settings.setValue("normVmin", self.datasetProp.currDisplayProp['normVmin'])
        settings.setValue("normVmax", self.datasetProp.currDisplayProp['normVmax'])
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
    def handleNeedDatasetImage(self,datasetName=None):
        if str(datasetName) == "":
            self.CXINavigation.CXITree.loadData1()
            return
        dataset = self.CXINavigation.CXITree.datasets[datasetName]
        format = dataset.getCXIFormat()
        if format == 2:        
            self.CXINavigation.datasetBoxes["image"].button.setName(datasetName)
            self.view.view2D.clear()
            if dataset.isCXIStack():
                self.view.view2D.loadStack(dataset)
                self.statusBar.showMessage("Loaded image stack: %s" % dataset.name,1000)
            else:
                self.view.view2D.loadImage(dataset)
                self.statusBar.showMessage("Loaded image: %s" % dataset.name,1000)
        else:
            QtGui.QMessageBox.warning(self,self.tr("CXI Viewer"),self.tr("Cannot sort with a dataset that has more than one dimension. The selected dataset has %d dimensions." %(len(dataset.shape))))
        self.datasetProp.setDataset(dataset)
        group = datasetName.rsplit("/",1)[0]
        if self.CXINavigation.datasetBoxes["mask"].button.text().rsplit("/",1)[0] != group:
            if group+"/mask" in self.CXINavigation.CXITree.datasets.keys():
                self.handleNeedDatasetMask(group+"/mask")
            elif group+"/mask_shared" in self.CXINavigation.CXITree.datasets.keys():
                self.handleNeedDatasetMask(group+"/mask_shared")
        self.view.view2DScrollWidget.update()
        self.updateData()
    def handleNeedDatasetIntegratedImage(self,integrationMode):
	self.view.view2D.integrationMode = integrationMode
	self.view.view2D.updateStackSize(True)
	self.view.view2D.clearTextures()
    def handleNeedDatasetMask(self,datasetName=None):
        if str(datasetName) == "":
            self.view.view2D.setMask()
            self.view.view2D.clearTextures()
            self.view.view2D.updateGL()
            self.CXINavigation.datasetBoxes["mask"].button.setName()
            self.statusBar.showMessage("Reset mask.",1000)
        else:
            dataset = self.CXINavigation.CXITree.datasets[datasetName]
            maskShape = dataset.getCXIImageShape()
            imageShape = self.view.view2D.data.getCXIImageShape()
            if maskShape != imageShape:
                self.statusBar.showMessage("Mask shape missmatch. Do not load mask: %s" % dataset.name,1000)
            else:
                self.view.view2D.setMask(dataset)
                self.view.view2D.clearTextures()
                self.view.view2D.updateGL()
                self.CXINavigation.datasetBoxes["mask"].button.setName(datasetName)
                self.statusBar.showMessage("Loaded mask: %s" % dataset.name,1000)
        self.handleMaskOutBitsChanged()
    def handleMaskOutBitsChanged(self,action=None):
        self.view.view2D.setMaskOutBits(self.CXINavigation.datasetMenus["mask"].getMaskOutBits())
    def handleNeedDatasetFilter(self,datasetName):
        senderBox = self.sender().datasetBox
        if self.CXINavigation.datasetBoxes["filter0"] == senderBox:
            dataset = self.CXINavigation.CXITree.datasets[datasetName]
            if dataset.getCXIFormat() == 1:
                targetBox = self.CXINavigation.addFilterBox()
                self.datasetProp.addFilter(dataset)
                self.datasetProp.displayPropChanged.emit(self.datasetProp.currDisplayProp)
                targetBox.button.setName(datasetName)
                targetBox.button.needDataset.connect(self.handleNeedDatasetFilter)
        else:
            i = self.CXINavigation.datasetBoxes["filters"].index(senderBox)
            if str(datasetName) == "":
                self.datasetProp.removeFilter(i)
                self.CXINavigation.removeFilterBox(senderBox)
                self.datasetProp.displayPropChanged.emit(self.datasetProp.currDisplayProp)
            else:
                targetBox = senderBox
                dataset = self.CXINavigation.CXITree.datasets[datasetName]
                self.datasetProp.refreshFilter(dataset,i)
                self.datasetProp.displayPropChanged.emit(self.datasetProp.currDisplayProp)
                targetBox.button.setName(datasetName)
                self.statusBar.showMessage("Loaded filter dataset: %s" % dataset.name,1000)
    def handleNeedDatasetSorting(self,datasetName):
        if str(datasetName) == "":
            self.CXINavigation.datasetBoxes["sort"].button.setName()
            self.datasetProp.clearSorting()
            self.datasetProp.setSorting()
            self.datasetProp.displayPropChanged.emit(self.datasetProp.currDisplayProp)
            self.statusBar.showMessage("Reset sorting.",1000)
        else:
            dataset = self.CXINavigation.CXITree.datasets[datasetName]
            if dataset.getCXIFormat() == 1:
                self.CXINavigation.datasetBoxes["sort"].button.setName(datasetName)
                self.datasetProp.refreshSorting(dataset)
                self.datasetProp.setSorting()
                self.datasetProp.displayPropChanged.emit(self.datasetProp.currDisplayProp)
                self.statusBar.showMessage("Loaded sorting dataset: %s" % dataset.name,1000)
            else:
                self.statusBar.showMessage("Dataset has inadequate shape for sorting stack: %s" % dataset.name,1000)
    def handleNeedDatasetX1D(self,datasetName):
        self.handleNeedDatasetPlot(datasetName,"X")
    def handleNeedDatasetY1D(self,datasetName):
        self.handleNeedDatasetPlot(datasetName,"Y")
    def handleNeedDatasetPlot(self,datasetName,axis="Y"):
        if str(datasetName) == "":
            self.view.view1D.setData(None,axis)
            self.view.view1D.refreshPlot()
            if axis == "Y":
                self.view.view1D.hide()
                self.viewActions["View 1D"].setChecked(False)
                self.datasetProp.plotBox.hide()
        else:
            dataset = self.CXINavigation.CXITree.datasets[datasetName]
            plotMode = self.CXINavigation.datasetMenus["plot Y"].getPlotMode()
            self.view.view1D.setData(dataset,axis)
            self.view.view1D.refreshPlot()
            #self.CXINavigation.datasetBoxes["plot"].button.setName(datasetName)
            self.statusBar.showMessage("Loaded plot: %s" % dataset.name,1000)
            #self.viewActions["View 1D"].setChecked(True)
            self.view.view1D.show()
            self.datasetProp.plotBox.show()
            self.viewActions["View 1D"].setChecked(True)
    def handlePixelStackChanged(self,ix,iy,N):
        self.view.view1D.show()
        self.datasetProp.plotBox.show()
        self.viewActions["View 1D"].setChecked(True)
        self.view.view1D.setStack(ix,iy,N)
        #self.CXINavigation.datasetBoxes["plot"].button.setName("%s (%i,%i)" % (datasetName,ix,iy))
        #self.statusBar.showMessage("Loaded pixel stack to plot: %s (%i,%i)" % (dataset.name,iy,ix),1000)
    def handlePlotModeTriggered(self,foovalue=None):
        self.view.view1D.setPlotMode(self.CXINavigation.datasetMenus["plot Y"].getPlotMode())
        self.view.view1D.refreshPlot()
        if self.view.view1D.dataY != None:
            self.viewActions["View 1D"].setChecked(True)
            self.view.view1D.show()
            self.datasetProp.plotBox.show()
        else:
            self.viewActions["View 1D"].setChecked(False)
            self.view.view1D.hide()
            self.datasetProp.plotBox.hide()           
    def handleDisplayPropChanged(self,prop):
        self.view.view2D.refreshDisplayProp(prop)
        self.view.view1D.refreshDisplayProp(prop)
    def handleDatasetClicked(self,datasetName):
        dataset = self.CXINavigation.CXITree.datasets[datasetName]
        format = dataset.getCXIFormat()
        if format == 1 and not dataset.isCXIText():
            self.handleNeedDatasetPlot(datasetName,"Y")
        elif format == 2:
            if datasetName[:4] == "mask":
                self.handleNeedDatasetMask(datasetName)
            else:
                self.handleNeedDatasetImage(datasetName)            
    def handleDatasetX1DChanged(self,dataset):
        n = None
        if dataset != None:
            if hasattr(dataset,"name"):
                n = dataset.name
        self.CXINavigation.datasetBoxes["plot X"].button.setName(n)
    def handleDatasetY1DChanged(self,dataset):
        n = None
        if dataset != None:
            if hasattr(dataset,"name"):
                n = dataset.name
        self.CXINavigation.datasetBoxes["plot Y"].button.setName(n)
    def handleDataset2DChanged(self,dataset):
        n = None
        if dataset != None:
            if hasattr(dataset,"name"):
                n = dataset.name
        self.CXINavigation.datasetBoxes["image"].button.setName(n)
    def handleViewIndexSelected(self,index):
        self.view.view2D.browseToViewIndex(index)
    def toggleUpdate(self):
        if self.updateTimer.isActive():
            self.updateTimer.stop()
        else:
            self.updateTimer.start()
    def updateData(self):
        self.view.view2D.updateStackSize()
        self.view.view1D.updateStackSize()

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
