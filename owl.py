#!/usr/bin/env python
"""Implement the Viewer Class"""
# system related packages
import sys, os
#sys.path.append(os.path.dirname(os.path.realpath(__file__)))

# GUI related packages (OpenGL and Qt)
from Qt import QtGui, QtCore

# Some other helpful packages
import logging
import argparse
import time

# internal modules
from cxi.fileloader import FileLoader
from cxitree import CXINavigation
from dataprop import DataProp, paintColormapIcons
import settingsOwl
import ui.dialogs
import ui.widgets
from views.indexprojector import IndexProjector
from views.viewsplitter import ViewSplitter


# Wishes:
#
# Infinite subplots
# Double click to zoom on image (double click again zoom back to width of column).
# Also changes to 1 column view
# View only tagged ones
# More precise browse to img. At the moment we end up somewhere close to the
# image of intrest but not exactly to it.


class Owl(QtGui.QMainWindow):
    """Main Window Class

    Handles the signals and slots for most connections"""
    def __init__(self, arguments):
        QtGui.QMainWindow.__init__(self)

        # command line arguments
        self.args = arguments

        # logging
        self.logger = logging.getLogger("Viewer")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["Viewer"])

        # status bar
        self.statusBar = self.statusBar()
        self.statusBar.showMessage("Initializing...")

        # Initizialize settinga
        self.settings = QtCore.QSettings()
        self._init_settings()

        # Objects and menus
        self.indexProjector = IndexProjector()
        self.view = ViewSplitter(self, self.indexProjector)
        self._init_menus()
        self._init_shortcuts()
        self.dataProp = DataProp(self, self.indexProjector)
        self.cxiNavigation = CXINavigation(self)
        self.fileLoader = FileLoader(self)

        # GUI Splitter Layout
        self.splitter = QtGui.QSplitter(self)
        self.splitter.setContentsMargins(0, 0, 0, 0)
        self.splitter.addWidget(self.cxiNavigation)
        self.splitter.addWidget(self.view)
        self.splitter.addWidget(self.dataProp)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.setCentralWidget(self.splitter)

        # GUI geometry
        self._init_geometry()

        # Timer
        QtCore.QTimer.singleShot(0, self._after_show)

        # Connections
        self._init_connections()

        # Stylesheet
        self._setStyleSheetFromFilename()

        # Other inizializations
        self.dataProp.emitView1DProp()
        self.dataProp.emitView2DProp()

        # End of inizialization
        self.statusBar.showMessage("Initialization complete.", 1000)

    def _after_show(self):
        """In run when the event loop starts. Load the CXI file given in the command line."""
        if self.args.filename != "":
            self._openCXIFile(self.args.filename)

    def _openCXIFile(self, filename):
        """Tells the fileLoader to open the CXI file and populate the CXI tree."""
        self.filename = filename
        self.fileLoader.loadFile(filename)
        self.cxiNavigation.CXITree.buildTree(self.fileLoader)
        self.cxiNavigation.CXITree.loadData()
        self.cxiNavigation.CXITree.loadPeakList()

    def _init_geometry(self):
        """Initializes the window geometry, and restores any previously saved geometry."""
        self.resize(800, 450)
        if(self.settings.contains("geometry")):
            self.restoreGeometry(self.settings.value("geometry"))
        if(self.settings.contains("windowState")):
            self.restoreState(self.settings.value("windowState"))
        self.view.view1D.setWindowSize(float(self.settings.value("movingAverageSize")))


    def _init_settings(self):
        """Initializes owl's QSettings to default values if empty."""
        if(not self.settings.contains("scrollDirection")):
            self.settings.setValue("scrollDirection", 1)
        if(not self.settings.contains("imageCacheSize")):
            self.settings.setValue("imageCacheSize", 1024) # Default to 1 GB
        if(not self.settings.contains("phaseCacheSize")):
            self.settings.setValue("phaseCacheSize", 1024) # Default to 1 GB
        if(not self.settings.contains("maskCacheSize")):
            self.settings.setValue("maskCacheSize", 1024) # Default to 1 GB
        if(not self.settings.contains("geometryCacheSize")):
            self.settings.setValue("geometryCacheSize", 10) # Default to 10 MB
        if(not self.settings.contains("textureCacheSize")):
            self.settings.setValue("textureCacheSize", 256) # Default to 256 MB
        if(not self.settings.contains("updateTimer")):
            self.settings.setValue("updateTimer", 10000)
        if(not self.settings.contains("movingAverageSize")):
            self.settings.setValue("movingAverageSize", 10.)
        if(not self.settings.contains("PNGOutputPath")):
            self.settings.setValue("PNGOutputPath", "./")
        if(not self.settings.contains("TagColors")):
            self.settings.setValue("TagColors", [QtGui.QColor(52, 102, 164),
                                                 QtGui.QColor(245, 121, 0),
                                                 QtGui.QColor(117, 80, 123),
                                                 QtGui.QColor(115, 210, 22),
                                                 QtGui.QColor(204, 0, 0),
                                                 QtGui.QColor(193, 125, 17),
                                                 QtGui.QColor(237, 212, 0)])
        if(not self.settings.contains("modelCenterX")):
            self.settings.setValue("modelCenterX", 0)
        if(not self.settings.contains("modelCenterY")):
            self.settings.setValue("modelCenterY", 0)
        if(not self.settings.contains("modelDiameter")):
            self.settings.setValue("modelDiameter", 100)
        if(not self.settings.contains("modelIntensity")):
            self.settings.setValue("modelIntensity", 1)
        if(not self.settings.contains("modelMaskRadius")):
            self.settings.setValue("modelMaskRadius", 300)
        if(not self.settings.contains("Shortcuts")):
            shortcuts = {}
            shortcuts["Move Selection Right"] = QtGui.QKeySequence("Right").toString()
            shortcuts["Move Selection Left"] = QtGui.QKeySequence("Left").toString()
            shortcuts["Move Selection Down"] = QtGui.QKeySequence("Down").toString()
            shortcuts["Move Selection Up"] = QtGui.QKeySequence("Up").toString()
            shortcuts["Toggle 1st Tag"] = QtGui.QKeySequence("1").toString()
            shortcuts["Toggle 2nd Tag"] = QtGui.QKeySequence("2").toString()
            shortcuts["Toggle 3rd Tag"] = QtGui.QKeySequence("3").toString()
            for i in range(4, 10):
                shortcuts["Toggle "+str(i)+"th Tag"] = QtGui.QKeySequence(str(i)).toString()
            self.settings.setValue("Shortcuts", shortcuts)
        elif("Toggle 8th Tag" not in self.settings.value('Shortcuts')):
            # We're missing the new shortcuts        
            shortcuts = self.settings.value('Shortcuts')
            for i in range(8, 10):
                shortcuts["Toggle "+str(i)+"th Tag"] = QtGui.QKeySequence(str(i)).toString()
            self.settings.setValue("Shortcuts", shortcuts)
        if not self.settings.contains("fileMode"):
            self.settings.setValue("fileMode", "r")
        else:
            if not settingsOwl.swmrSupported and (self.settings.value("fileMode") == "r*"):
                self.settings.setValue("fileMode", "r")
        if(not self.settings.contains("normGamma")):
            self.settings.setValue("normGamma", "0.25")
        if(not self.settings.contains("maskAlpha")):
            self.settings.setValue("maskAlpha", "0.00")
            

    def _init_menus(self):
        """Initialize the top level menus."""
        self._init_menu_file()
        self._init_menu_edit()
        self._init_menu_go()
        self._init_menu_save()
        self._init_menu_view()
        self._init_menu_analysis()

    def _init_menu_file(self):
        """Initialize the File menu."""
        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))

        self.openFile = QtGui.QAction("Open", self)
        self.fileMenu.addAction(self.openFile)
        self.openFile.triggered.connect(self._openFileClicked)

        self.fileMode = QtGui.QAction("File mode", self)
        self.fileMenu.addAction(self.fileMode)
        self.fileMode.triggered.connect(self._fileModeClicked)

        self.saveTags = QtGui.QAction("Save Tags", self)
        self.fileMenu.addAction(self.saveTags)
        self.saveTags.triggered.connect(self._saveTagsClicked)

        self.saveModels = QtGui.QAction("Save Models", self)
        self.fileMenu.addAction(self.saveModels)
        self.saveModels.triggered.connect(self._saveModelsClicked)

        self.exportModelImage = QtGui.QAction("Export Model Image", self)
        self.exportModelImage.setToolTip("Exports an image of the selected model to an hdf5 file")
        self.fileMenu.addAction(self.exportModelImage)
        self.exportModelImage.triggered.connect(self.view.view2D.exportModelImage)

        self.savePattersons = QtGui.QAction("Save Pattersons", self)
        self.fileMenu.addAction(self.savePattersons)
        self.savePattersons.triggered.connect(self._savePattersonsClicked)

        self.quitAction = QtGui.QAction("Quit", self)
        self.fileMenu.addAction(self.quitAction)
        self.quitAction.triggered.connect(QtGui.QApplication.instance().quit)

        self.preferences = QtGui.QAction("Preferences", self)
        self.fileMenu.addAction(self.preferences)
        self.preferences.triggered.connect(self._preferencesClicked)

    def _init_menu_edit(self):
        """Initialize the Edit menu."""
        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))

        self.tagsAction = QtGui.QAction("Tags...", self)
        self.editMenu.addAction(self.tagsAction)
        self.tagsAction.triggered.connect(self._tagsClicked)

    def _init_menu_go(self):
        """Initialize the Go menu."""
        self.goMenu = self.menuBar().addMenu(self.tr("&Go"))

        act = QtGui.QAction("Previous Row", self)
        act.setShortcut(QtGui.QKeySequence.MoveToPreviousPage)
        self.goMenu.previousRow = act
        self.goMenu.addAction(act)

        act = QtGui.QAction("Next Row", self)
        act.setShortcut(QtGui.QKeySequence.MoveToNextPage)
        self.goMenu.nextRow = act
        self.goMenu.addAction(act)

    def _init_menu_save(self):
        """Initialize the Save menu."""
        self.saveMenu = self.menuBar().addMenu(self.tr("&Save"))

        act = QtGui.QAction("To PNG", self)
        act.setShortcut(QtGui.QKeySequence("Ctrl+P"))
        self.saveMenu.toPNG = act
        self.saveMenu.addAction(act)

    def _init_menu_view(self):
        """Initialize the Save menu."""
        self.viewMenu = self.menuBar().addMenu(self.tr("&View"))

        self.cxiStyleAction = QtGui.QAction("CXI Style", self)
        self.cxiStyleAction.setCheckable(True)
        self.cxiStyleAction.setChecked(False)
        self.cxiStyleAction.triggered.connect(self._toggleCXIStyleSheet)
        self.viewMenu.addAction(self.cxiStyleAction)

        self.viewMenu.addSeparator()

        act = QtGui.QAction("Full Screen", self)
        act.setShortcut(QtGui.QKeySequence("Ctrl+F"))
        act.setCheckable(True)
        act.triggered.connect(self._toggleFullScreen)
        self.viewMenu.addAction(act)

        act = QtGui.QAction("Slide Show", self)
        act.setCheckable(True)
        act.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        act.triggered.connect(self.view.view2D.toggleSlideShow)
        self.viewMenu.addAction(act)

        act = QtGui.QAction("Auto last", self)
        act.setCheckable(True)
        act.setShortcut(QtGui.QKeySequence("Ctrl+L"))
        act.triggered.connect(self.view.view2D.toggleAutoLast)
        self.viewMenu.addAction(act)

        self.viewMenu.addSeparator()

        self.viewActions = {"File Tree"          : QtGui.QAction("File Tree", self),
                            "View 1D"            : QtGui.QAction("View 1D", self),
                            "View 2D"            : QtGui.QAction("View 2D", self),
                            "Display Properties" : QtGui.QAction("Display Properties", self),
                            "Tags"               : QtGui.QAction("Tags", self),
                            "Model"              : QtGui.QAction("Model", self),
                            "Patterson"          : QtGui.QAction("Patterson", self),
                            "Pixel Peeper"       : QtGui.QAction("Pixel Peeper", self),
                            "Peak Finder"        : QtGui.QAction("Peak Finder", self),}

        viewShortcuts = {"File Tree"          : "Ctrl+T",
                         "View 1D"            : "Ctrl+1",
                         "View 2D"            : "Ctrl+2",
                         "Display Properties" : "Ctrl+D",
                         "Tags"               : "Ctrl+G",
                         "Model"              : "Ctrl+M",
                         "Patterson"          : "Ctrl+A",
                         "Pixel Peeper"       : "Ctrl+X",
                         "Peak Finder"        : "Ctrl+K",
        }

        viewNames = ["File Tree", "Display Properties", "View 1D", "View 2D", "Tags", "Model", "Patterson", "Pixel Peeper", "Peak Finder"]

        actions = {}
        for viewName in viewNames:
            if(viewName == "Tags"):
                self.viewMenu.addSeparator()
            actions[viewName] = self.viewActions[viewName]
            actions[viewName].setCheckable(True)
            actions[viewName].setShortcut(QtGui.QKeySequence(viewShortcuts[viewName]))
            if(viewName == "Tags"):
                actions[viewName].triggered.connect(self.view.view2D.toggleTagView)
            elif(viewName == "Model"):
                actions[viewName].triggered.connect(self._toggleModelView)
            elif(viewName == "Patterson"):
                actions[viewName].triggered.connect(self._togglePattersonView)
            elif(viewName == "Pixel Peeper"):
                actions[viewName].triggered.connect(self.view.view2D.togglePixelPeeper)
            elif(viewName == "Peak Finder"):
                actions[viewName].triggered.connect(self._togglePeakFinder)
            else:
                actions[viewName].triggered.connect(self._viewClicked)
            if viewName in ["View 1D", "Model", "Patterson", "Pixel Peeper", "Peak Finder"]:
                actions[viewName].setChecked(False)
            else:
                actions[viewName].setChecked(True)
            self.viewMenu.addAction(actions[viewName])

        self.viewMenu.addSeparator()

        icon_width = 64
        icon_height = 64
        colormapIcons = paintColormapIcons(icon_width, icon_height)

        self.colormapMenu = QtGui.QMenu("Colormap", self)
        self.colormapActionGroup = QtGui.QActionGroup(self)

        traditionalColormaps = ['jet', 'hot', 'gray', 'Spectral', 'coolwarm', 'gnuplot', 'gist_earth']
        self.colormapActions = {}
        for colormap in traditionalColormaps:
            a = self.colormapMenu.addAction(colormapIcons.pop(colormap), colormap)
            a.setActionGroup(self.colormapActionGroup)
            a.setCheckable(True)
            self.colormapActions[colormap] = a

        self.exoticColormapMenu = QtGui.QMenu("Exotic", self)
        for colormap in colormapIcons.keys():
            a = self.exoticColormapMenu.addAction(colormapIcons[colormap], colormap)
            a.setActionGroup(self.colormapActionGroup)
            a.setCheckable(True)
            self.colormapActions[colormap] = a

        if(self.settings.contains("colormap")):
            self.colormapActions[self.settings.value('colormap')].setChecked(True)
        else:
            self.colormapActions['jet'].setChecked(True)
        self.colormapMenu.addMenu(self.exoticColormapMenu)
        self.viewMenu.addMenu(self.colormapMenu)

        action = QtGui.QAction("Power Scale Exp...", self)
        action.triggered.connect(self.setPowerExponent)
        self.viewMenu.addAction(action)

        action = QtGui.QAction("Mask Transperency...", self)
        action.triggered.connect(self.setMaskTransperency)
        self.viewMenu.addAction(action)

    def _init_menu_analysis(self):
        """Initialize the Analysis menu."""
        self.analysisMenu = self.menuBar().addMenu(self.tr("&Analysis"))
        self.sizingAction = QtGui.QAction("Sizing", self)
        self.analysisMenu.addAction(self.sizingAction)
        self.sizingAction.triggered.connect(self.sizingClicked)

    def _init_shortcuts(self):
        """Initialize the shortcuts using owl's QSettings."""
        shortcuts = self.settings.value('Shortcuts')
        self.editMenu.toggleTag = []

        action = QtGui.QAction('Toggle 1st Tag', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 1st Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Toggle 2nd Tag', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 2nd Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Toggle 3rd Tag', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 3rd Tag']))
        self.addAction(action)
        self.editMenu.toggleTag.append(action)

        for i in range(4, 10):
            action = QtGui.QAction('Toggle '+str(i)+'th Tag', self)
            action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle '+str(i)+'th Tag']))
            self.addAction(action)
            self.editMenu.toggleTag.append(action)

        action = QtGui.QAction('Move Selection Right', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Right']))
        self.addAction(action)
        self.editMenu.moveSelectionRight = action

        action = QtGui.QAction('Move Selection Left', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Left']))
        self.addAction(action)
        self.editMenu.moveSelectionLeft = action

        action = QtGui.QAction('Move Selection Up', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Up']))
        self.addAction(action)
        self.editMenu.moveSelectionUp = action

        action = QtGui.QAction('Move Selection Down', self)
        action.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Down']))
        self.addAction(action)
        self.editMenu.moveSelectionDown = action

    def _init_connections(self):
        """Initialize all the signal slot connections."""
        self.cxiNavigation.CXITree.dataClicked.connect(self.handleDataClicked)
        #self.view.view1D.needData.connect(self.handleNeedDataY1D)
        self.view.view1D.dataItemXChanged.connect(self.handleDataX1DChanged)
        self.view.view1D.dataItemYChanged.connect(self.handleDataY1DChanged)
        #self.view.view2D.needDataImage.connect(self.handleNeedDataImage)
        self.view.view2D.dataItemChanged.connect(self.handleData2DChanged)
        self.cxiNavigation.dataBoxes["image"].button.needData.connect(self.handleNeedDataImage)
        self.cxiNavigation.dataBoxes["mask"].button.needData.connect(self.handleNeedDataMask)
        self.cxiNavigation.dataMenus["mask"].triggered.connect(self.handleMaskOutBitsChanged)
        self.cxiNavigation.dataBoxes["sort"].button.needData.connect(self.handleNeedDataSorting)
        self.cxiNavigation.dataBoxes["plot X"].button.needData.connect(self.handleNeedDataX1D)
        self.cxiNavigation.dataMenus["plot X"].triggered.connect(self.handlePlotModeTriggered)
        self.cxiNavigation.dataBoxes["plot Y"].button.needData.connect(self.handleNeedDataY1D)
        self.cxiNavigation.dataMenus["plot Y"].triggered.connect(self.handlePlotModeTriggered)
        self.cxiNavigation.dataBoxes["filter0"].button.needData.connect(self.handleNeedDataFilter)
        self.cxiNavigation.dataBoxes["Peak List"].button.needData.connect(self.handlePeakListDrop)
        self.dataProp.view1DPropChanged.connect(self.view.view1D.refreshDisplayProp)
        self.dataProp.view2DPropChanged.connect(self.view.view2D.refreshDisplayProp)
        self.view.view2D.pixelClicked.connect(self.dataProp.onPixelClicked)
        self.view.view2D.pixelClicked.connect(self.view.view1D.onPixelClicked)
        self.view.view1D.viewIndexSelected.connect(self.handleViewIndexSelected)
        self.view.view1D.viewValueSelected.connect(self.handleViewValueSelected)
        self.goMenu.nextRow.triggered.connect(self.view.view2D.nextRow)
        self.goMenu.previousRow.triggered.connect(self.view.view2D.previousRow)
        self.saveMenu.toPNG.triggered.connect(self.view.view2D.saveToPNG)
        for i in range(0, len(self.editMenu.toggleTag)):
            self.editMenu.toggleTag[i].triggered.connect(lambda checked=False, id=i: self.dataProp.toggleSelectedImageTag(id))
        self.editMenu.moveSelectionRight.triggered.connect(lambda: self.view.view2D.moveSelectionBy(1, 0))
        self.editMenu.moveSelectionLeft.triggered.connect(lambda: self.view.view2D.moveSelectionBy(-1, 0))
        self.editMenu.moveSelectionUp.triggered.connect(lambda: self.view.view2D.moveSelectionBy(0, -1))
        self.editMenu.moveSelectionDown.triggered.connect(lambda: self.view.view2D.moveSelectionBy(0, 1))
        self.fileLoader.stackSizeChanged.connect(self.onStackSizeChanged)
        self.fileLoader.fileLoaderExtended.connect(self.onFileLoaderExtended)

    def _openFileClicked(self):
        """Slot triggered when Open File is clicked."""
        fileName = QtGui.QFileDialog.getOpenFileName(self, "Open CXI File", None, "CXI Files (*.cxi)")
        # JAS: PySide (1.2.2) returns tuple, PyQt4 (4.8.6) returns unicode, which is fixed below
        if(isinstance(fileName, tuple)):
            if(fileName[0]):
                self._openCXIFile(fileName[0])
        else:
            if(fileName):
                self._openCXIFile(fileName)

    def _fileModeClicked(self):
        """Slot triggered when File Mode is clicked."""
        diag = ui.dialogs.FileModeDialog(self)
        if(diag.exec_()):
            if diag.rw.isChecked():
                self.fileLoader.setMode("r+")
            elif diag.rswmr.isChecked():
                self.fileLoader.setMode("r*")
            elif diag.r.isChecked():
                self.fileLoader.setMode("r")

    def _saveTagsClicked(self):
        """Slot triggered when Tags is clicked."""
        self.fileLoader.saveTags()

    def _saveModelsClicked(self):
        """Slot triggered when Save Models is clicked."""
        self.fileLoader.saveModels()

    def _savePattersonsClicked(self):
        """Slot triggered when Save Patterson is clicked."""
        self.fileLoader.savePattersons()

    def _setStyleSheetFromFilename(self, filename="stylesheets/default.stylesheet"):
        """Sets the stylesheet for the application."""
        styleFile = os.path.join(os.path.split(__file__)[0], filename)
        with open(styleFile, "r") as fh:
            self.setStyleSheet(fh.read())

    def _toggleCXIStyleSheet(self):
        """Toggles between an empty or the dark stylesheet."""
        if self.cxiStyleAction.isChecked():
            self._setStyleSheetFromFilename("stylesheets/dark.stylesheet")
        else:
            self._setStyleSheetFromFilename()

    def _viewClicked(self):
        """Slot triggered when a View is clicked."""
        viewName = self.sender().text()
        checked = self.viewActions[viewName].isChecked()
        viewBoxes = {"File Tree" : [self.cxiNavigation],
                     "Display Properties" : [self.dataProp],
                     "View 1D" : [self.view.view1D, self.dataProp.plotBox],
                     "View 2D" : [self.view.view2DScrollWidget, self.dataProp.displayBox,
                                  self.dataProp.imageStackBox, self.dataProp.generalBox]}
        boxes = viewBoxes[viewName]
        if(checked):
            self.statusBar.showMessage("Showing %s" % viewName, 1000)
            for box in boxes:
                box.show()
        else:
            self.statusBar.showMessage("Hiding %s" % viewName, 1000)
            for box in boxes:
                box.hide()

    def _toggleFullScreen(self):
        """Toggles full screen mode."""
        if self.windowState() & QtCore.Qt.WindowFullScreen:
            self.showNormal()
        else:
            self.showFullScreen()

    def closeEvent(self, event):
        """Function run when the application is closing."""
        if self.fileLoader.tagsChanged():
            saveTags = QtGui.QMessageBox(QtGui.QMessageBox.Question, "Save tag changes?",
                                         "Would you like to save changes to the tags?",
                                         QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard 
                                         | QtGui.QMessageBox.Cancel).exec_()            
            if(saveTags == QtGui.QMessageBox.Save):
                self.fileLoader.saveTags()
            if(saveTags == QtGui.QMessageBox.Cancel):
                return event.ignore()
        if self.fileLoader.modelsChanged():
            saveModel = QtGui.QMessageBox(QtGui.QMessageBox.Question, "Save model changes?",
                                         "Would you like to save changes to the models?",
                                         QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard 
                                         | QtGui.QMessageBox.Cancel).exec_()            
            if(saveModel == QtGui.QMessageBox.Save):
                self.fileLoader.saveModels()
            if(saveModel == QtGui.QMessageBox.Cancel):
                return event.ignore()            
        if self.fileLoader.pattersonsChanged():
            savePatterson = QtGui.QMessageBox(QtGui.QMessageBox.Question, "Save Patterson configurations??",
                                              "Would you like to save changes to the Patterson configurations?",
                                              QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard 
                                              | QtGui.QMessageBox.Cancel).exec_()            
            if(savePatterson == QtGui.QMessageBox.Save):
                self.fileLoader.savePattersons()
            if(savePatterson == QtGui.QMessageBox.Cancel):
                return event.ignore()            
                
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        self.settings.setValue("colormap", self.dataProp.view2DProp['colormapText'])
        self.settings.setValue("normScaling", self.dataProp.view2DProp['normScaling'])
        self.settings.setValue("normClamp", self.dataProp.view2DProp['normClamp'])
        self.settings.setValue("normInvert", self.dataProp.view2DProp['normInvert'])
        self.settings.setValue("normVmin", self.dataProp.view2DProp['normVmin'])
        self.settings.setValue("normVmax", self.dataProp.view2DProp['normVmax'])
        self.settings.setValue("fileMode", self.fileLoader.mode)
        QtGui.QMainWindow.closeEvent(self, event)

    def _preferencesClicked(self):
        """Slot triggered when Preferences is clicked."""
        diag = ui.dialogs.PreferencesDialog(self)
        if(diag.exec_()):
            if(diag.natural.isChecked()):
                self.settings.setValue("scrollDirection", -1)
            else:
                self.settings.setValue("scrollDirection", 1)
            v = diag.imageCacheSpin.value()
            self.settings.setValue("imageCacheSize", v)
            self.view.view2D.loaderThread.imageData.setSizeInBytes(v*1024*1024)
            v = diag.imageCacheSpin.value()
            self.settings.setValue("phaseCacheSize", v)
            self.view.view2D.loaderThread.phaseData.setSizeInBytes(v*1024*1024)
            v = diag.maskCacheSpin.value()
            self.settings.setValue("maskCacheSize", v)
            self.view.view2D.loaderThread.maskData.setSizeInBytes(v*1024*1024)
            v = diag.geometryCacheSpin.value()
            self.settings.setValue("geometryCacheSize", v)
            self.view.view2D.loaderThread.geometryData.setSizeInBytes(v*1024*1024)
            v = diag.textureCacheSpin.value()
            self.settings.setValue("textureCacheSize", v)
            self.view.view2D.imageTextures.setSizeInBytes(v*1024*1024)
            v = diag.updateTimerSpin.value()
            self.settings.setValue("updateTimer", v)
            self.fileLoader.updateTimer.setInterval(v)
            v = diag.movingAverageSizeSpin.value()
            self.settings.setValue("movingAverageSize", v)
            self.view.view1D.setWindowSize(v)
            v = diag.PNGOutputPath.text()
            self.settings.setValue("PNGOutputPath", v)
            self.view.view2D.PNGOutputPath = v

            shortcuts = self.settings.value("Shortcuts")
            for r in range(0, diag.shortcutsTable.rowCount()):
                name = diag.shortcutsTable.verticalHeaderItem(r).text()
                string = QtGui.QKeySequence.fromString(diag.shortcutsTable.item(r, 0).text(),
                                                       QtGui.QKeySequence.NativeText).toString()
                shortcuts[name] = string
            self.settings.setValue("Shortcuts", shortcuts)

            self.editMenu.moveSelectionDown.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Down']))
            self.editMenu.moveSelectionUp.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Up']))
            self.editMenu.moveSelectionLeft.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Left']))
            self.editMenu.moveSelectionRight.setShortcut(QtGui.QKeySequence.fromString(shortcuts['Move Selection Right']))

            self.editMenu.toggleTag[0].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 1st Tag']))
            self.editMenu.toggleTag[1].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 2nd Tag']))
            self.editMenu.toggleTag[2].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle 3rd Tag']))
            for i in range(3, 6):
                self.editMenu.toggleTag[i].setShortcut(QtGui.QKeySequence.fromString(shortcuts['Toggle '+str(i+1)+'th Tag']))

            self.settings.setValue("modelCenterX", diag.modelCenterX.text())
            self.settings.setValue("modelCenterY", diag.modelCenterY.text())
            self.settings.setValue("modelDiameter", diag.modelDiameter.text())
            self.settings.setValue("modelIntensity", diag.modelIntensity.text())
            self.settings.setValue("modelMaskRadius", diag.modelMaskRadius.text())

    def handleNeedDataImage(self, dataName=None):
        """Slot triggered when a CXITree button sends a needDataImage signal.

        TODO FM: why is this not part of CXITree?
        """
        if dataName == "" or dataName is None:
            self.cxiNavigation.CXITree.loadData()
            return
        dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
        if not dataItem.isPresentable:
            self.statusBar.showMessage("Data not presentable.")
            return
        if (dataItem.format == 2) or (dataItem.format == 3):
            self.cxiNavigation.dataBoxes["image"].button.setName(dataName)
            self.view.view2D.clear()
            self.view.view2D.loadStack(dataItem)
            self.statusBar.showMessage("Loaded %s" % dataItem.fullName, 1000)
        else:
            QtGui.QMessageBox.warning(self, self.tr("CXI Viewer"), self.tr("Cannot sort with a data that has more "
                                                                           "than one dimension. The selected data has "
                                                                           "%d dimensions." %(len(dataItem.shape()))))
        self.dataProp.setData(dataItem)
        group = dataName.rsplit("/", 1)[0]
        if "mask" in dataName:
            self.handleNeedDataMask()
        elif self.cxiNavigation.dataBoxes["mask"].button.text().rsplit("/", 1)[0] != group:
            if group+"/mask" in self.cxiNavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask")
            elif group+"/mask_shared" in self.cxiNavigation.CXITree.fileLoader.dataItems.keys():
                self.handleNeedDataMask(group+"/mask_shared")
        self.view.view2DScrollWidget.update()  # Depricated?

    def handleNeedDataMask(self, dataName=None):
        """Slot triggered when a CXITree button needs to apply a mask.

        TODO FM: should it really be here
        """
        if dataName == "" or dataName is None:
            self.view.view2D.setMask()
            self.cxiNavigation.dataBoxes["mask"].button.setName()
            self.statusBar.showMessage("Reset mask.", 1000)
        else:
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            maskShape = (dataItem.shape()[-2], dataItem.shape()[-1])
            imageShape = (self.view.view2D.data.shape()[-2], self.view.view2D.data.shape()[-1])
            if maskShape != imageShape:
                self.statusBar.showMessage("Mask shape missmatch. Do not load mask: %s" % dataItem.fullName, 1000)
            else:
                self.view.view2D.setMask(dataItem)
                self.cxiNavigation.dataBoxes["mask"].button.setName(dataName)
                self.statusBar.showMessage("Loaded mask: %s" % dataName, 1000)
        # needed?
        self.handleMaskOutBitsChanged()

    def handleMaskOutBitsChanged(self, action=None):
        """Slot triggered when a CXITree mask button enabled bits change.

        TODO FM: move to view2D
        """
        _ = action
        self.view.view2D.setMaskOutBits(self.cxiNavigation.dataMenus["mask"].getMaskOutBits())
        self.cxiNavigation.CXITree.fileLoader.maskOutBits = self.cxiNavigation.dataMenus["mask"].getMaskOutBits()
        #self.view.view2D.clearTextures()
        self.view.view2D.updateGL()

    def handleNeedDataFilter(self, dataName):
        """Slot triggered when a CXITree filter says it needData.

        TODO FM: move most parts to CXITree and  to view2D
        """
        senderBox = self.sender().dataBox
        # add or replace first filter
        if self.cxiNavigation.dataBoxes["filter0"] == senderBox:
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            if not dataItem.isStack:
                self.statusBar.showMessage("Data item is not a stack and therefore it can not be used as a filter.")
            else:
                nDims = len(dataItem.shape())
                if (nDims == 1) or (nDims == 2):
                    if nDims == 1:
                        targetBox = self.cxiNavigation.addFilterBox()
                        self.dataProp.addFilter(dataItem)
                        self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                        targetBox.button.setName(dataName)
                        targetBox.button.needData.connect(self.handleNeedDataFilter)
                    else:
                        selIndDialog = ui.dialogs.SelectIndexDialog(self, dataItem)
                        if(selIndDialog.exec_() == QtGui.QDialog.Accepted):
                            while dataItem.selectedIndex is None:
                                time.sleep(0.1)
                            targetBox = self.cxiNavigation.addFilterBox()
                            self.dataProp.addFilter(dataItem)
                            self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                            targetBox.button.setName(dataName)
                            targetBox.button.needData.connect(self.handleNeedDataFilter)
                else:
                    self.statusBar.showMessage("Data item has incorrect format for becoming a filter.")
        # add, replace or remove secondary filter
        else:
            i = self.cxiNavigation.dataBoxes["filters"].index(senderBox)
            if dataName == "" or dataName is None:
                self.dataProp.removeFilter(i)
                self.cxiNavigation.removeFilterBox(senderBox)
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
            else:
                targetBox = senderBox
                dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
                if not dataItem.isPresentable:
                    self.statusBar.showMessage("Data not presentable.")
                    return
                self.dataProp.refreshFilter(dataItem, i)
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                targetBox.button.setName(dataName)
                self.statusBar.showMessage("Loaded filter data: %s" % dataName, 1000)

    def handleNeedDataSorting(self, dataName):
        """Slot triggered when a CXITree sort button is used

        TODO FM: does not belong here as it only accesses children
        """
        if dataName == "" or dataName is None:
            self.cxiNavigation.dataBoxes["sort"].button.setName()
            self.dataProp.clearSorting()
            self.dataProp.setSorting()
            self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
            self.statusBar.showMessage("Reset sorting.", 1000)
        else:
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            if dataItem.format == 0 and dataItem.isStack:
                self.cxiNavigation.dataBoxes["sort"].button.setName(dataName)
                self.dataProp.refreshSorting(dataItem)
                self.dataProp.setSorting()
                self.dataProp.view2DPropChanged.emit(self.dataProp.view2DProp)
                self.view.view1D.refreshPlot()
                self.statusBar.showMessage("Loaded sorting data: %s" % dataName, 1000)
            else:
                self.statusBar.showMessage("Data has inadequate shape for sorting stack: %s" % dataName, 1000)

    def handleNeedDataX1D(self, dataName):
        """Slot triggered when a CXITree plotX button is used

        TODO FM: does not belong here as it only accesses children
        """
        if dataName == "" or dataName is None:
            self.view.view1D.setDataItemX(None)
            self.view.view1D.refreshPlot()
            self.statusBar.showMessage("Reset X data for plot." % dataName, 1000)
        else:
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            self.view.view1D.setDataItemX(dataItem)
            self.view.view1D.refreshPlot()
            #self.cxiNavigation.dataBoxes["plot X"].button.setName(dataName)
            self.statusBar.showMessage("Loaded X data for plot: %s" % dataName, 1000)

    def handleNeedDataY1D(self, dataName):
        """Slot triggered when a CXITree plotY button is used

        TODO FM: does not belong here as it only accesses children
        """
        if dataName == "" or dataName is None:
            self.view.view1D.setDataItemY(None)
            self.view.view1D.refreshPlot()
            self.view.view1D.hide()
            self.dataProp.plotBox.hide()
            self.viewActions["View 1D"].setChecked(False)
            self.statusBar.showMessage("Reset Y data for plot." % dataName, 1000)
        else:
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            nDims = len(dataItem.shape())
            if dataItem.isStack and (nDims == 3):
                selIndDialog = ui.dialogs.SelectIndexDialog(self, dataItem)
                selIndDialog.exec_()
            if not dataItem.isPresentable:
                self.statusBar.showMessage("Data not presentable.")
                return
            self.view.view1D.setDataItemY(dataItem)
            self.view.view1D.refreshPlot()
            #self.cxiNavigation.dataBoxes["plot Y"].button.setName(dataName)
            self.view.view1D.show()
            self.dataProp.plotBox.show()
            self.viewActions["View 1D"].setChecked(True)
            self.statusBar.showMessage("Loaded Y data for plot: %s" % dataName, 1000)

    def handlePeakListDrop(self, dataName):
        if(dataName == '' or dataName is None):
            self.view.view2D.setPeakGroup(None)
            return
        if(dataName in self.cxiNavigation.CXITree.fileLoader.dataItems):
            dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
            # Check if we have a peak list member
            if(dataName.endswith("/nPeaks") or dataName.endswith("/peakIntensity") or
               dataName.endswith("/peakNPixels") or dataName.endswith("/peakXPosAssembled") or
               dataName.endswith("/peakXPosRaw") or dataName.endswith("/peakYPosAssembled") or
               dataName.endswith("/peakYPosRaw")):
                groupItem = self.cxiNavigation.CXITree.fileLoader.groupItems[dataName[:dataName.rindex('/')]]
                self.cxiNavigation.dataBoxes["Peak List"].button.setName(dataName[:dataName.rindex('/')])
                self.view.view2D.setPeakGroup(groupItem)
                return
        elif(dataName in self.cxiNavigation.CXITree.fileLoader.groupItems):
            groupItem = self.cxiNavigation.CXITree.fileLoader.groupItems[dataName]
            if(groupItem.fullName+"/nPeaks" in self.cxiNavigation.CXITree.fileLoader.dataItems):
                self.cxiNavigation.dataBoxes["Peak List"].button.setName(groupItem.fullName)
                self.view.view2D.setPeakGroup(groupItem)



    def handlePlotModeTriggered(self, foovalue=None):
        """Slot triggered when a CXITree plotX menu is triggered

        TODO FM: does not belong here as it only accesses children
        """
        _ = foovalue
        self.view.view1D.setPlotMode(self.cxiNavigation.dataMenus["plot Y"].getPlotMode())
        self.view.view1D.refreshPlot()
        if self.view.view1D.dataItemY is not None:
            self.viewActions["View 1D"].setChecked(True)
            self.view.view1D.show()
            self.dataProp.plotBox.show()
        else:
            self.viewActions["View 1D"].setChecked(False)
            self.view.view1D.hide()
            self.dataProp.plotBox.hide()

    def handleDataClicked(self, dataName):
        """Slot triggered when dataProp emits view1DPropChanged

        TODO FM: move to view1D
        """
        dataItem = self.cxiNavigation.CXITree.fileLoader.dataItems[dataName]
        # Check if we have a peak list member
        if(dataName.endswith("/nPeaks") or dataName.endswith("/peakIntensity") or
           dataName.endswith("/peakNPixels") or dataName.endswith("/peakXPosAssembled") or
           dataName.endswith("/peakXPosRaw") or dataName.endswith("/peakYPosAssembled") or
           dataName.endswith("/peakYPosRaw")):
            groupItem = self.cxiNavigation.CXITree.fileLoader.groupItems[dataName[:dataName.rindex('/')]]
            self.cxiNavigation.dataBoxes["Peak List"].button.setName(dataName[:dataName.rindex('/')])
            self.view.view2D.setPeakGroup(groupItem)
            return

        if (dataItem.format == 0 and dataItem.isStack) or (dataItem.format == 1 and not dataItem.isStack):
            self.handleNeedDataY1D(dataName)
        elif dataItem.format == 2:
            if dataName[-4:] == "mask":
                self.handleNeedDataMask(dataName)
            else:
                self.handleNeedDataImage(dataName)

    def handleDataX1DChanged(self, dataItem):
        """Slot triggered when view1D emits dataItemXChanged

        TODO FM: move to cxiNavigation
        """
        n = None
        if dataItem is not None:
            if hasattr(dataItem, "fullName"):
                n = dataItem.fullName
        self.cxiNavigation.dataBoxes["plot X"].button.setName(n)

    def handleDataY1DChanged(self, dataItem):
        """Slot triggered when view1D emits dataItemYChanged

        TODO FM: move to cxiNavigation
        """
        n = None
        if dataItem is not None:
            if hasattr(dataItem, "fullName"):
                n = dataItem.fullName
        self.cxiNavigation.dataBoxes["plot Y"].button.setName(n)

    def handleData2DChanged(self, dataItemImage, dataItemMask):
        """Slot triggered when view2D emits dataItemChanged

        TODO FM: move to dataProp
        """
        if dataItemImage is None:
            self.dataProp.modelProperties.setModelItem(None)
            self.dataProp.pattersonProperties.setPattersonItem(None)
        else:
            self.dataProp.modelProperties.setModelItem(dataItemImage.modelItem)
            self.dataProp.pattersonProperties.setPattersonItem(dataItemImage.pattersonItem)
            if(dataItemImage.modelItem):
                dataItemImage.modelItem.dataItemImage = dataItemImage
                dataItemImage.modelItem.dataItemMask = dataItemMask
            if(dataItemImage.pattersonItem):
                dataItemImage.pattersonItem.dataItemImage = dataItemImage
                dataItemImage.pattersonItem.dataItemMask = dataItemMask
        dataItems = {"image":dataItemImage, "mask":dataItemMask}
        for k, item in dataItems.items():
            n = None
            if item is not None:
                if hasattr(item, "fullName"):
                    n = item.fullName
            self.cxiNavigation.dataBoxes[k].button.setName(n)

    def onStackSizeChanged(self, newStackSize=0):
        """Slot triggered fileLoader notices change in stackSize

        TODO FM: link the signal directly to the destination
        """
        self.indexProjector.onStackSizeChanged(newStackSize)
        self.view.view2D.onStackSizeChanged(newStackSize)
        self.view.view1D.onStackSizeChanged(newStackSize)
        self.dataProp.onStackSizeChanged(newStackSize)

    def handleViewValueSelected(self, value):
        """Slot triggered when a new value is selected in the View1D

        TODO JAS: link signal directly
        """
        assert type(value) == list, "value is not a list.."
        assert len(value) == 2, "list is not of length 2 (%d)" % len(value)
        self.dataProp.setXYInPlotBox(value[0], value[1])

    def handleViewIndexSelected(self, index):
        """Slot triggered when a new index is selected in the View1D

        TODO FM: link signal directly
        """
        self.view.view2D.browseToViewIndex(index)

    def _toggleModelView(self):
        """Slot triggered when modelView is toggled

        TODO FM: link signals directly
        """
        self.view.view2D.toggleModelView()
        self.dataProp.modelProperties.toggleVisible()

    def _togglePattersonView(self):
        """Slot triggered when pattersonView is toggled

        TODO FM: link signals directly
        """
        self.view.view2D.togglePattersonView()
        self.dataProp.pattersonProperties.toggleVisible()

    def _tagsClicked(self):
        """Slot triggered when Tags menu item is clicked

        TODO FM: move to view2D?
        """
        if(self.view.view2D.data):
            tagsDialog = ui.dialogs.TagsDialog(self, self.view.view2D.data.tagsItem.tags)
            if(tagsDialog.exec_() == QtGui.QDialog.Accepted):
                tags = tagsDialog.getTags()
                if(tags != self.view.view2D.data.tagsItem.tags):
                    self.view.view2D.data.tagsItem.setTags(tags)
        else:
            QtGui.QMessageBox.information(self, "Cannot set tags", "Cannot set tags if no dataset is open.")

    def sizingClicked(self):
        """Slot triggered when sizing menu item is clicked

        TODO FM: move to view2D?
        """
        if(self.view.view2D.data):
            self.sizingWidget = ui.widgets.SizingWidget(self, self.view.view2D)
            self.dataProp.vboxScroll.addWidget(self.sizingWidget)
            self.sizingWidget.sizing.sizingDone.connect(self.sizingDestroyWidget)
        else:
            QtGui.QMessageBox.information(self, "Cannot do sizing", "Cannot do sizing if no dataset is open.")

    def sizingDestroyWidget(self):
        """Slot triggered when sizing analysis is done

        TODO: BD: move to view2D?
        """
        self.sizingWidget.sizingThread.quit()
        QtCore.QThread.sleep(1)
        self.dataProp.vboxScroll.removeWidget(self.sizingWidget)
        self.sizingWidget.deleteLater()
        self.sizingWidget = None            

    def onFileLoaderExtended(self):
        """Slot triggered when fileLoader emits onFileLoaderExtended

        TODO FM: direct connection
        """
        self.cxiNavigation.CXITree.updateTree()

    def setPowerExponent(self):
        """Slot triggered when the Power Scale Exp... menu is clicked

        TODO FM: move to dataProp?
        """
        gamma = float(self.settings.value("normGamma"))
        gamma, ok = QtGui.QInputDialog.getDouble(self, "Power Scale Exponent",
                                                 "Set New Power Scale Exponent:",
                                                 gamma, -10, 10, 3)
        if(ok):
            gamma = self.settings.setValue("normGamma", gamma)
            self.dataProp.emitView2DProp()

    def setMaskTransperency(self):
        """Slot triggered when the Mask Transperency... menu is clicked

        TODO FM: move to dataProp?
        """
        alpha = float(self.settings.value("maskAlpha"))
        alpha, ok = QtGui.QInputDialog.getDouble(self, "Mask Transperency",
                                                 "Set New Mask Transperency:",
                                                 alpha, 0., 1., 3)
        if(ok):
            alpha = self.settings.setValue("maskAlpha", alpha)
            self.dataProp.emitView2DProp()

    def _togglePeakFinder(self, value):
        self.view.view2D.setPeakFinderVisible(value)
        self.cxiNavigation.setPeakFinderVisible(value)

def exceptionHandler(exceptionType, value, traceback):
    """Handle exception in debugging mode"""
    sys.__excepthook__(exceptionType, value, traceback)
    QtGui.QApplication.instance().exit()
    sys.exit(-1)

if __name__ == '__main__':

    logging.basicConfig()
    QtCore.QCoreApplication.setOrganizationName("CXIDB")
    QtCore.QCoreApplication.setOrganizationDomain("cxidb.org")
    QtCore.QCoreApplication.setApplicationName("owl")

    # FM: This should provide retina rendering on Mac, but
    # might break some pyqtgraph stuff, we should be aware
    # QtGui.QApplication.setGraphicsSystem("native")
    if hasattr(sys, 'argv'):
        app = QtGui.QApplication(sys.argv)
    else:
        app = QtGui.QApplication([])

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-d', '--debug', dest='debuggingMode', action='store_true', help='debugging mode')
    parser.add_argument('filename', nargs="?", type=str, help='CXI file to load', default="")
    args = parser.parse_args()
    
    if args.debuggingMode:
        # Set exception handler
        print "Running owl in debugging mode."
        sys.excepthook = exceptionHandler

    aw = Owl(args)
    aw.show()
    ret = app.exec_()
    aw.view.view2D.stopThreads()
    sys.exit(ret)
