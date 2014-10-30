#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL
from operator import mul
import numpy,ctypes
import h5py
from matplotlib import colors
from matplotlib import cm
import pyqtgraph
import fit
from ui.dialogs import ExperimentDialog
import ui.displayBox
import ui.modelProperties
import ui.pattersonProperties


# Import spimage (needed for ModelProperties)
try:
    import spimage
    hasSpimage = True
except:
    print "Warning: The python package libspimage could not be found. Without libspimage, the View -> Model feature is disabled. \nAll code for viewing and fitting of the model has been moved to libspimage. You can download and install it from here: \nhttps://github.com/FilipeMaia/libspimage"
    hasSpimage = False

def sizeof_fmt(num):
    for x in ['bytes','kB','MB','GB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')

class DataProp(QtGui.QWidget):
    view2DPropChanged = QtCore.Signal(dict)
    view1DPropChanged = QtCore.Signal(dict)
    def __init__(self,parent=None,indexProjector=None):
        QtGui.QWidget.__init__(self,parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.viewer = parent
        self.indexProjector = indexProjector
        # this dict holds all current settings
        self.view2DProp = {}
        self.view1DProp = {}
        self.vbox = QtGui.QVBoxLayout()
        # stack
        self.stackSize = None

        self.settings = QtCore.QSettings()
        # scrolling
        self.vboxScroll = QtGui.QVBoxLayout()
        self.vboxScroll.setContentsMargins(0,0,11,0)
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.vboxScroll)
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.vbox.addWidget(self.scrollArea)
        # GENERAL PROPERTIES
        # properties: data
        self.generalBox = QtGui.QGroupBox("General Properties");
        self.generalBox.vbox = QtGui.QVBoxLayout()
        self.generalBox.setLayout(self.generalBox.vbox)
        self.shape = QtGui.QLabel("Shape:", parent=self)
        self.datatype = QtGui.QLabel("Data Type:", parent=self)
        self.datasize = QtGui.QLabel("Data Size:", parent=self)
        self.dataform = QtGui.QLabel("Data Form:", parent=self)

        self.generalBox.vbox.addWidget(self.shape)
        self.generalBox.vbox.addWidget(self.datatype)
        self.generalBox.vbox.addWidget(self.datasize)
        self.generalBox.vbox.addWidget(self.dataform)

        # properties: image stack
        self.imageStackBox = QtGui.QGroupBox("Image Stack");
        self.imageStackBox.vbox = QtGui.QVBoxLayout()
        self.imageStackBox.setLayout(self.imageStackBox.vbox)
        # property: image stack plots width
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Width:"))
        self.imageStackSubplots = QtGui.QSpinBox(parent=self)
        self.imageStackSubplots.setMinimum(1)
#       self.imageStackSubplots.setMaximum(5)
        hbox.addWidget(self.imageStackSubplots)
        self.imageStackBox.vbox.addLayout(hbox)
        
        # DISPLAY PROPERTIES
        self.displayBox = DisplayBox(self)

        # sorting
        self.sortingBox = QtGui.QGroupBox("Sorting")
        self.sortingBox.vbox = QtGui.QVBoxLayout()
        self.sortingDataLabel = QtGui.QLabel("",parent=self)
        self.sortingBox.vbox.addWidget(self.sortingDataLabel)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Invert"))
        self.invertSortingCheckBox = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.invertSortingCheckBox)
        hbox.addStretch()
        self.sortingBox.vbox.addLayout(hbox)
        self.sortingBox.setLayout(self.sortingBox.vbox)
        self.clearSorting()
        # filters
        self.filterBox = QtGui.QGroupBox("Filters")
        self.filterBox.vbox = QtGui.QVBoxLayout()
        self.filterBox.setLayout(self.filterBox.vbox)
        self.filterBox.hide()
        self.activeFilters = []
        self.inactiveFilters = []

        # plot box

        self.plotBox = QtGui.QGroupBox("Plot")
        self.plotBox.vbox = QtGui.QVBoxLayout()

        validatorInt = QtGui.QIntValidator()
        validatorInt.setBottom(0)
        validatorSci = QtGui.QDoubleValidator()
        validatorSci.setDecimals(3)
        validatorSci.setNotation(QtGui.QDoubleValidator.ScientificNotation)

        self.plotNBinsEdit = QtGui.QLineEdit(self)
        self.plotNBinsEdit.setMaximumWidth(100)
        self.plotNBinsEdit.setValidator(validatorInt)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("# bins:"))
        hbox.addWidget(self.plotNBinsEdit)
        self.plotBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Lines:"))
        self.plotLinesCheckBox = QtGui.QCheckBox("",parent=self)
        self.plotLinesCheckBox.setChecked(True)
        hbox.addWidget(self.plotLinesCheckBox)
        self.plotBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Points:"))
        self.plotPointsCheckBox = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.plotPointsCheckBox)
        self.plotBox.vbox.addLayout(hbox)

        self.plotBox.setLayout(self.plotBox.vbox)
        self.plotBox.hide()

        self.modelProperties = ModelProperties(self)
        self.modelProperties.hide()

        self.pattersonProperties = PattersonProperties(self)
        self.pattersonProperties.hide()
        
        # add all widgets to main vbox
        self.vboxScroll.addWidget(self.generalBox)
        self.vboxScroll.addWidget(self.displayBox)
        self.vboxScroll.addWidget(self.imageStackBox)
        self.vboxScroll.addWidget(self.sortingBox)
        self.vboxScroll.addWidget(self.filterBox)
        self.vboxScroll.addWidget(self.plotBox)
        self.vboxScroll.addWidget(self.modelProperties)
        self.vboxScroll.addWidget(self.pattersonProperties)
        self.vboxScroll.addStretch()
        self.setLayout(self.vbox)
        # clear all properties
        self.clear()
        # connect signals
        self.imageStackSubplots.editingFinished.connect(self.emitView2DProp)
        self.displayBox.displayMax.editingFinished.connect(self.checkLimits)
        self.displayBox.displayMin.editingFinished.connect(self.checkLimits)
        self.displayBox.displayClamp.stateChanged.connect(self.emitView2DProp)
        self.displayBox.displayAutorange.stateChanged.connect(self.emitView2DProp)
        self.displayBox.displayAutorange.stateChanged.connect(self.setModMinMax)
        self.displayBox.displayScale.currentIndexChanged.connect(self.emitView2DProp)
        self.invertSortingCheckBox.toggled.connect(self.emitView2DProp)
        self.invertSortingCheckBox.toggled.connect(self.emitView1DProp)
        self.viewer.colormapActionGroup.triggered.connect(self.emitView2DProp)
        self.plotLinesCheckBox.toggled.connect(self.emitView1DProp)
        self.plotPointsCheckBox.toggled.connect(self.emitView1DProp)
        self.plotNBinsEdit.editingFinished.connect(self.emitView1DProp)
    def clear(self):
        self.clearView2DProp()
        self.clearData()
    def clearView2DProp(self):
        self.clearImageStackSubplots()
        self.clearNorm()
        self.clearColormap()
    def onCurrentImg(self):
        self.currentImg.edited = True
        self.emitView2DProp()
    # DATA
    def onStackSizeChanged(self,newStackSize):
        self.stackSize = newStackSize
        self.updateShape()
    def updateShape(self):
        if self.data is not None:
            # update shape label
            string = "Shape: "
            shape = list(self.data.shape())
            for d in shape:
                string += str(d)+"x"
            string = string[:-1]
            self.shape.setText(string)
            # update filters?
    def setData(self,data=None):
        self.data = data
        self.updateShape()
        if data is not None:
            self.datatype.setText("Data Type: %s" % (data.dtypeName))
            self.datasize.setText("Data Size: %s" % sizeof_fmt(data.dtypeItemsize*reduce(mul,data.shape())))
            if data.isStack:
                form = "%iD Data Stack" % data.format
            else:
                form = "%iD Data" % data.format
            self.dataform.setText("Data form: %s" % form)
            if data.isStack:
                self.imageStackBox.show()
            else:
                self.imageStackBox.hide()
        else:
            self.clearData()
    def refreshDataCurrent(self,img,NImg,viewIndex,NViewIndex):
        self.currentImg.setText("%i" % (img))
        self.currentImg.validator.setRange(0,NImg)
        self.currentViewIndex.setText("Central Index: %i (%i)" % (viewIndex,NViewIndex))
    def clearData(self):
        self.data = None
        self.shape.setText("Shape: ")
        self.datatype.setText("Data Type: ")
        self.datasize.setText("Data Size: ")
        self.dataform.setText("Data Form: ")
        self.imageStackBox.hide()
    # VIEW
    def onPixelClicked(self,info):
        if self.data is not None and info is not None:
            (hist,edges) = numpy.histogram(self.data.data(img=info["img"]),bins=100)
            self.displayBox.pixelClicked(hist,edges)
            # Check if we clicked on a tag
            if(info["tagClicked"] != -1):
                # Toggle tag
                self.toggleTag(info["img"],info["tagClicked"])
            self.modelProperties.showParams()
            self.pattersonProperties.showParams()
        else:
            self.imageBox.hide()
    def onHistogramClicked(self,region):
        (min,max) = region.getRegion()
        self.displayBox.displayMin.setText("%0.1f" % (min))
        self.displayBox.displayMax.setText("%0.1f" % (max))
        self.checkLimits()
        self.emitView2DProp()
    # NORM
    def setNorm(self):
        P = self.view2DProp
        P["normVmin"] = float(self.displayBox.displayMin.text())
        P["normVmax"] = float(self.displayBox.displayMax.text())
        P["autorange"] = self.displayBox.displayAutorange.isChecked()
        P["normClamp"] = self.displayBox.displayClamp.isChecked()
        if self.displayBox.displayScale.currentIndex() == 0:
            P["normScaling"] = "lin"
        elif self.displayBox.displayScale.currentIndex() == 1:
            P["normScaling"] = "log"
        else:
            P["normScaling"] = "pow"
        P["normGamma"] = float(self.settings.value('normGamma'))
        self.displayBox.intensityHistogramRegion.setRegion([float(self.displayBox.displayMin.text()),
                                                            float(self.displayBox.displayMax.text())])
    def clearNorm(self):
        settings = QtCore.QSettings()
        if(settings.contains("normVmax")):
            normVmax = float(settings.value('normVmax'))
        else:
            normVmax = 1000.
        if(settings.contains("normVmin")):
            normVmin = float(settings.value('normVmin'))
        else:
            normVmin = 10.
        if(settings.contains("normVmin")):
            autorange = bool(settings.value('autorange'))
        else:
            autorange = False
        self.displayBox.displayAutorange.setChecked(autorange)
        self.displayBox.displayMin.setText(str(normVmin))
        self.displayBox.displayMax.setText(str(normVmax))
        if(settings.contains("normClamp")):
            normClamp = bool(settings.value('normClamp'))
        else:
            normClamp = True
        self.displayBox.displayClamp.setChecked(normClamp)
        if(settings.contains("normScaling")):
            norm = settings.value("normScaling")
            if(norm == "lin"):
                self.displayBox.displayScale.setCurrentIndex(0)
            elif(norm == "log"):
                self.displayBox.displayScale.setCurrentIndex(1)
            elif(norm == "pow"):
                self.displayBox.displayScale.setCurrentIndex(2)
            else:
                sys.exit(-1)
        else:
            self.displayBox.displayScale.setCurrentIndex(1)
        self.setNorm()
    # COLORMAP
    def setColormap(self,foovalue=None):
        P = self.view2DProp
        a = self.viewer.colormapActionGroup.checkedAction()
        self.displayBox.displayColormap.setText(a.text())
        self.displayBox.displayColormap.setIcon(a.icon())
        P["colormapText"] = a.text()

    def clearColormap(self):
        self.setColormap()
    # STACK
    def setImageStackSubplots(self,foovalue=None):
        P = self.view2DProp
        P["imageStackSubplotsValue"] = self.imageStackSubplots.value()
    def clearImageStackSubplots(self):
        self.imageStackSubplots.setValue(1)
        self.setImageStackSubplots()
    # SORTING
    def setSorting(self,foo=None):
        P = self.view2DProp
        P["sortingInverted"] = self.invertSortingCheckBox.isChecked()
        P["sortingDataItem"] = self.sortingData
    def clearSorting(self):
        self.sortingData = None
        self.sortingInverted = False
        self.sortingDataLabel.setText("")
        self.sortingBox.hide()
    def refreshSorting(self,data):
        if data is not None:
            self.sortingData = data
            self.sortingBox.show()
            self.sortingDataLabel.setText(data.fullName)
        else:
            self.clearSorting()
    # FILTERS
    def addFilter(self,data):
        if self.inactiveFilters == []:
            filterWidget = FilterWidget(self,data)
            filterWidget.dataItem.selectStack()
            filterWidget.limitsChanged.connect(self.emitView2DProp)
            filterWidget.selectedIndexChanged.connect(self.emitView2DProp)
            self.filterBox.vbox.addWidget(filterWidget)
            self.activeFilters.append(filterWidget)
        else:
            self.activeFilters.append(self.inactiveFilters.pop(0))
            filterWidget = self.activeFilters[-1]
            filterWidget.dataItem.selectStack()
            filterWidget.show()
            filterWidget.refreshData(data)
        self.indexProjector.addFilter(filterWidget.dataItem)
        self.setFilters()
        self.filterBox.show()
    def removeFilter(self,index):
        filterWidget = self.activeFilters.pop(index)
        filterWidget.dataItem.deselectStack()
        self.filterBox.vbox.removeWidget(filterWidget)
        self.filterBox.vbox.addWidget(filterWidget)
        self.inactiveFilters.append(filterWidget)
        filterWidget.hide()
        filterWidget.histogram.clear()
        filterWidget.hide()
        self.setFilters()
        if self.activeFilters == []:
            self.filterBox.hide()
        self.indexProjector.removeFilter(index)
    def setFilters(self,foo=None):
        P = self.view2DProp
        D = []
        if self.activeFilters != []:
            vmins = numpy.zeros(len(self.activeFilters))
            vmaxs = numpy.zeros(len(self.activeFilters))
            for i,f in zip(range(len(self.activeFilters)),self.activeFilters):
                vmins[i] = float(f.vminLineEdit.text())
                vmaxs[i] = float(f.vmaxLineEdit.text())
            self.indexProjector.updateFilterMask(vmins,vmaxs)
            P["filterMask"] = self.indexProjector.filterMask()
            Ntot = len(P["filterMask"])
            Nsel = P["filterMask"].sum()
            p = 100*Nsel/(1.*Ntot)
        else:
            P["filterMask"] = None
            Ntot = 0
            Nsel = 0
            p = 100.
        self.filterBox.setTitle("Filters (yield: %.2f%% - %i/%i)" % (p,Nsel,Ntot))
    def refreshFilter(self,data,index):
        self.activeFilters[index].refreshData(data)
    def setPlotStyle(self):
        P = self.view1DProp
        P["lines"] = self.plotLinesCheckBox.isChecked()
        P["points"] = self.plotPointsCheckBox.isChecked()
    def setModMinMax(self):
        c =  self.displayBox.displayAutorange.isChecked() == False
        self.displayBox.displayMin.setEnabled(c)
        self.displayBox.displayMax.setEnabled(c)
    def setCurrentImg(self):
        P = self.view2DProp
        i = self.currentImg.text()
        if self.currentImg.edited == False:
            P["img"] = None
        else:
            try:
                i = int(i)
                P["img"] = i
            except:
                P["img"] = None
        self.currentImg.edited = False
    # update and emit current diplay properties
    def emitView1DProp(self):
        #self.setPixelStack()
        self.setPlotStyle()
        self.view1DPropChanged.emit(self.view1DProp)
    def emitView2DProp(self):
        self.setImageStackSubplots()
        self.setNorm()
        self.setColormap()
        self.setSorting()
        self.setFilters()
        #self.setImageStackN()
        self.view2DPropChanged.emit(self.view2DProp)
    def checkLimits(self):
        self.displayBox.displayMax.validator().setBottom(float(self.displayBox.displayMin.text()))
        self.displayBox.displayMin.validator().setTop(float(self.displayBox.displayMax.text()))
        self.emitView2DProp()
    # still needed?
    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_H:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    def toggleSelectedImageTag(self,id):
        img = self.viewer.view.view2D.selectedImage
        if(img is None):
            return
        self.toggleTag(img,id)
    def toggleTag(self,img,id):
        value = (self.data.tagsItem.tagMembers[id,img] + 1) % 2
        self.data.tagsItem.setTag(img,id,value)
        self.viewer.tagsChanged = True
        self.viewer.view.view2D.updateGL()

               

def paintColormapIcons(W,H):
    a = numpy.outer(numpy.ones(shape=(H,)),numpy.linspace(0.,1.,W))
    maps=[m for m in cm.datad if not m.endswith("_r")]
    mappable = cm.ScalarMappable()
    mappable.set_norm(colors.Normalize())
    iconDict = {}
    for m in maps:
        mappable.set_cmap(m)
        temp = mappable.to_rgba(a,None,True)[:,:,:]
        a_rgb = numpy.zeros(shape=(H,W,4),dtype=numpy.uint8)
        # For some reason we have to swap indices !? Otherwise inverted colors...
        a_rgb[:,:,2] = temp[:,:,0]
        a_rgb[:,:,1] = temp[:,:,1]
        a_rgb[:,:,0] = temp[:,:,2]
        a_rgb[:,:,3] = 0xff
        img = QtGui.QImage(a_rgb,W,H,QtGui.QImage.Format_ARGB32)
        icon = QtGui.QIcon(QtGui.QPixmap.fromImage(img))
        iconDict[m] = icon
    return iconDict


class FilterWidget(QtGui.QWidget):
    limitsChanged = QtCore.Signal(float,float)
    selectedIndexChanged = QtCore.Signal(int)
    def __init__(self,parent,dataItem):
        QtGui.QWidget.__init__(self,parent)
        vbox = QtGui.QVBoxLayout()
        nameLabel = QtGui.QLabel(dataItem.fullName)
        yieldLabel = QtGui.QLabel("")
        data = dataItem.data()
        vmin = numpy.min(data)
        vmax = numpy.max(data)
        self.histogram = pyqtgraph.PlotWidget(self)
        self.histogram.hideAxis('left')
        self.histogram.hideAxis('bottom')
        self.histogram.setFixedHeight(50)
        # Make the histogram fit the available width
        self.histogram.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
        region = pyqtgraph.LinearRegionItem(values=[vmin,vmax],brush="#ffffff15")
        region.sigRegionChangeFinished.connect(self.syncLimits)
        self.histogram.addItem(region)
        self.histogram.autoRange()
        vbox.addWidget(self.histogram)
        vbox.addWidget(nameLabel)
        vbox.addWidget(yieldLabel)

        # for non-boolean filters
        hbox = QtGui.QHBoxLayout()
        self.vminLabel = QtGui.QLabel("Min.:")
        hbox.addWidget(self.vminLabel)
        self.vmaxLabel = QtGui.QLabel("Max.:")
        hbox.addWidget(self.vmaxLabel)
        vbox.addLayout(hbox)
        hbox = QtGui.QHBoxLayout()
        validator = QtGui.QDoubleValidator()
        validator.setDecimals(3)
        validator.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        self.vminLineEdit = QtGui.QLineEdit(self)
        self.vminLineEdit.setText("%.7e" % (vmin*0.999))
        self.vminLineEdit.setValidator(validator)
        hbox.addWidget(self.vminLineEdit)
        self.vmaxLineEdit = QtGui.QLineEdit(self)
        self.vmaxLineEdit.setText("%.7e" % (vmax*1.001))
        self.vmaxLineEdit.setValidator(validator)
        hbox.addWidget(self.vmaxLineEdit)
        vbox.addLayout(hbox)

        # for boolean filters
        hbox = QtGui.QHBoxLayout()
        self.invertLabel = QtGui.QLabel("Invert")
        hbox.addWidget(self.invertLabel)
        self.invertCheckBox = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.invertCheckBox)
        hbox.addStretch()
        vbox.addLayout(hbox)

        self.setNonBooleanFilter()

        # for 2-dimensional datasets
        hbox = QtGui.QHBoxLayout()
        self.indexLabel = QtGui.QLabel("Index:")
        hbox.addWidget(self.indexLabel)
        self.indexCombo = QtGui.QComboBox()
        hbox.addWidget(self.indexCombo)
        vbox.addLayout(hbox)

        self.set1DimensionalDataset()

        self.setLayout(vbox)
        self.histogram.region = region
        self.histogram.itemPlot = None
        self.nameLabel = nameLabel
        self.yieldLabel = yieldLabel
        self.vbox = vbox
        self.refreshData(dataItem)
        self.vminLineEdit.editingFinished.connect(self.emitLimitsChanged)
        self.vmaxLineEdit.editingFinished.connect(self.emitLimitsChanged)
        self.indexCombo.currentIndexChanged.connect(self.emitSelectedIndexChanged)
        self.invertCheckBox.toggled.connect(self.syncLimits)
    def setBooleanFilter(self):
        self.histogram.hide()
        self.vminLabel.hide()
        self.vmaxLabel.hide()
        self.vminLineEdit.hide()
        self.vmaxLineEdit.hide()
        self.invertLabel.show()
        self.invertCheckBox.show()
        self.isBooleanFilter = True
    def setNonBooleanFilter(self):
        self.histogram.show()
        self.vminLabel.show()
        self.vmaxLabel.show()
        self.vminLineEdit.show()
        self.vmaxLineEdit.show()
        self.invertLabel.hide()
        self.invertCheckBox.hide()
        self.isBooleanFilter = False
    def set1DimensionalDataset(self):
        self.indexLabel.hide()
        self.indexCombo.hide()
        self.numberOfDimensionsDataset = 1
    def set2DimensionalDataset(self):
        self.indexLabel.show()
        self.indexCombo.show()
        self.indexCombo.setCurrentIndex(self.dataItem.selectedIndex)
        self.numberOfDimensionsDataset = 2
    def populateIndexCombo(self):
        if not self.isTags:
            nDims = self.dataItem.shape()[1]
        else:
            nDims = len(self.dataItem.attr("headings"))
        labels = []
        for i in range(nDims):
            labels.append("%i" % i)
        if self.isTags:
            for i,tag in zip(range(nDims),self.dataItem.tagsItem.tags):
                title = tag[0]
                labels[i] += " " + title
        self.indexCombo.addItems(labels)
    def refreshData(self,dataItem):
        self.nameLabel.setText(dataItem.fullName)
        self.dataItem = dataItem
        self.data = dataItem.data1D()
        self.isTags = (self.dataItem.fullName[self.dataItem.fullName.rindex("/")+1:] == "tags")
        Ntot = self.dataItem.fileLoader.stackSize
        vmin = numpy.min(self.data)
        vmax = numpy.max(self.data)
        yieldLabelString = "Yield: %.2f%% - %i/%i" % (100.,Ntot,Ntot)
        self.yieldLabel.setText(yieldLabelString)
        (hist,edges) = numpy.histogram(self.data,bins=100)
        edges = (edges[:-1]+edges[1:])/2.0
        if self.histogram.itemPlot is not None:
            self.histogram.removeItem(self.histogram.itemPlot)
        #self.histogram.clear()
        item = self.histogram.plot(edges,hist,fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
        item.getViewBox().setMouseEnabled(x=False,y=False)
        self.histogram.itemPlot = item
        self.histogram.region.setRegion([vmin,vmax])
        self.histogram.autoRange()
        if self.dataItem.selectedIndex is None:
            self.set1DimensionalDataset()
        else:
            self.populateIndexCombo()
            self.set2DimensionalDataset()
        if self.isTags:
            self.setBooleanFilter()
        else:
            self.setNonBooleanFilter()
        self.syncLimits()
    def syncLimits(self):
        if self.isBooleanFilter:
            if self.invertCheckBox.isChecked():
                vmin = -0.5
                vmax = 0.5
            else:
                vmin = 0.5
                vmax = 1.5
        else:
            (vmin,vmax) = self.histogram.region.getRegion()
        self.vminLineEdit.setText("%.3e" % (vmin*0.999))
        self.vmaxLineEdit.setText("%.3e" % (vmax*1.001))
        self.emitLimitsChanged()
    def emitLimitsChanged(self,foo=None):
        Ntot = len(self.data)
        vmin = float(self.vminLineEdit.text())
        vmax = float(self.vmaxLineEdit.text())
        Nsel = ( (self.data<=vmax)*(self.data>=vmin) ).sum()
        label = "Yield: %.2f%% - %i/%i" % (100*Nsel/(1.*Ntot),Nsel,Ntot)
        self.yieldLabel.setText(label)
        self.limitsChanged.emit(vmin,vmax)
    def emitSelectedIndexChanged(self):
        i = self.indexCombo.currentIndex()
        self.dataItem.selectedIndex = i
        self.selectedIndexChanged.emit(i)
        #self.refreshData(self.dataItem)  #BJD: This adds new items to indexCombo, however the labels in the filterBox are not updated now. 


class ModelProperties(QtGui.QGroupBox, ui.modelProperties.Ui_ModelProperties):
    def __init__(self,parent):
        self.parent = parent
        QtGui.QGroupBox.__init__(self,parent)
        self.setupUi(self)
        self.params = {}
        self.setModelItem()
        self.centerX.valueChanged.connect(self.setParams)
        self.centerY.valueChanged.connect(self.setParams)
        self.diameter.valueChanged.connect(self.setParams)
        self.intensity.valueChanged.connect(self.setParams)
        self.maskRadius.valueChanged.connect(self.setParams)
        self.maximumShift.valueChanged.connect(self.setParams)
        self.blurRadius.valueChanged.connect(self.setParams)
        self.findCenterMethod.currentIndexChanged.connect(self.setParams)
        self.fitDiameterMethod.currentIndexChanged.connect(self.setParams)
        self.fitIntensityMethod.currentIndexChanged.connect(self.setParams)
        self.fitModelMethod.currentIndexChanged.connect(self.setParams)
        self.experiment.released.connect(self.onExperiment)
        self.findCenterPushButton.released.connect(self.FindCenter)
        self.fitDiameterPushButton.released.connect(self.FitDiameter)
        self.fitIntensityPushButton.released.connect(self.FitIntensity)
        self.fitModelPushButton.released.connect(self.FitModel)
        self.visibilitySlider.sliderMoved.connect(self.setParams)
    def setModelItem(self,modelItem=None):
        self.modelItem = modelItem
        if modelItem is None:
            paramsImg = None
        else:
            img = self.parent.viewer.view.view2D.selectedImage
            if img is None:
                paramsImg = None
                self.showParams(paramsImg)
            else:
                paramsImg = self.modelItem.getParams(img)
                self.showParams(paramsImg)
                #self.setParams()  ## This breaks reloading of a dataset. Without this, viewing the model on selected images still works...
    def showParams(self,params=None):
        img = self.parent.viewer.view.view2D.selectedImage
        if img is not None:
            self.centerX.setReadOnly(False)
            self.centerY.setReadOnly(False)
            self.diameter.setReadOnly(False)
            self.intensity.setReadOnly(False)
            self.maskRadius.setReadOnly(False)
            self.maximumShift.setReadOnly(False)
            self.blurRadius.setReadOnly(False)
            self.visibilitySlider.setEnabled(True)
        else:
            self.centerX.setReadOnly(True)
            self.centerY.setReadOnly(True)
            self.diameter.setReadOnly(True)
            self.intensity.setReadOnly(True)
            self.maskRadius.setReadOnly(True)
            self.maximumShift.setReadOnly(True)
            self.blurRadius.setReadOnly(True)
            self.visibilitySlider.setEnabled(False)           
        if self.modelItem is None:
            # BD: Is this case ever happening?
            self.centerX.setValue(0)
            self.centerY.setValue(0)
            self.diameter.setValue(0)
            self.intensity.setValue(0)
            self.maskRadius.setValue(0)
            self.maximumShift.setValue(0)
            self.blurRadius.setValue(0)
            self.visibilitySlider.setValue(50)
        else:
            params = self.modelItem.getParams(img)
            self.centerX.setValue(params["offCenterX"])
            self.centerY.setValue(params["offCenterY"])
            self.diameter.setValue(params["diameterNM"])
            self.intensity.setValue(params["intensityMJUM2"])
            self.maskRadius.setValue(params["maskRadius"])
            self.maximumShift.setValue(params["_maximumShift"])
            self.blurRadius.setValue(params["_blurRadius"])
            self.visibilitySlider.setValue(params["_visibility"]*100)
            self.findCenterMethod.setCurrentIndex(self.findCenterMethod.findText(str(params["_findCenterMethod"])))
            self.fitDiameterMethod.setCurrentIndex(self.fitDiameterMethod.findText(str(params["_fitDiameterMethod"])))
            self.fitIntensityMethod.setCurrentIndex(self.fitIntensityMethod.findText(str(params["_fitIntensityMethod"])))
            self.fitModelMethod.setCurrentIndex(self.fitModelMethod.findText(str(params["_fitModelMethod"])))
    def setParams(self):
        params = {}
        img = self.parent.viewer.view.view2D.selectedImage
        params["offCenterX"] = self.centerX.value()
        params["offCenterY"] = self.centerY.value()
        params["diameterNM"] = self.diameter.value()
        params["intensityMJUM2"] = self.intensity.value()
        params["maskRadius"] = self.maskRadius.value()
        params["_visibility"] = float(self.visibilitySlider.value()/100.)
        params["_maximumShift"] = int(self.maximumShift.value())
        params["_blurRadius"] = int(self.blurRadius.value())
        params["_findCenterMethod"] = str(self.findCenterMethod.currentText())
        params["_fitDiameterMethod"] = str(self.fitDiameterMethod.currentText())
        params["_fitIntensityMethod"] = str(self.fitIntensityMethod.currentText())
        params["_fitModelMethod"] = str(self.fitModelMethod.currentText())
        if(img is None):
            return
        self.modelItem.setParams(img,params)
        # max: needed at psusr to really refresh, works without on my mac
        #self.parent.viewer.view.view2D._paintImage(img)
        self.parent.viewer.view.view2D.updateGL()
    def onExperiment(self):
        expDialog = ExperimentDialog(self, self.modelItem)
        expDialog.exec_()
    def FindCenter(self):
        img = self.parent.viewer.view.view2D.selectedImage
        self.modelItem.find_center(img)
        self.showParams()
    def FitDiameter(self):
        img = self.parent.viewer.view.view2D.selectedImage
        self.modelItem.find_center(img)
        self.showParams()
    def FitIntensity(self):
        img = self.parent.viewer.view.view2D.selectedImage
        self.modelItem.find_center(img)
        self.showParams()
    def FitModel(self):
        img = self.parent.viewer.view.view2D.selectedImage
        self.modelItem.fit_model(img)
        self.showParams()
    def toggleVisible(self):
        self.setVisible(hasSpimage and not self.isVisible())

class PattersonProperties(QtGui.QGroupBox, ui.pattersonProperties.Ui_PattersonProperties):
    def __init__(self,parent):
        self.parent = parent
        QtGui.QGroupBox.__init__(self,parent)
        self.setupUi(self)
        self.params = {}
        self.setPattersonItem(None)
        self.imageThreshold.valueChanged.connect(self.setParams)
        self.maskSmooth.valueChanged.connect(self.setParams)
        self.maskThreshold.valueChanged.connect(self.setParams)
        self.darkfield.stateChanged.connect(self.setParams)
        self.darkfieldX.valueChanged.connect(self.setParams)
        self.darkfieldY.valueChanged.connect(self.setParams)
        self.darkfieldSigma.valueChanged.connect(self.setParams)
        self.pattersonPushButton.clicked.connect(self.calculatePatterson)
    def setPattersonItem(self,pattersonItem=None):
        self.pattersonItem = pattersonItem
        if pattersonItem is None:
            paramsImg = None
        else:
            img = self.parent.viewer.view.view2D.selectedImage
            if img is None:
                paramsImg = None
                self.showParams(paramsImg)
            else:
                paramsImg = self.pattersonItem.getParams(img)
                self.showParams(paramsImg)
                #self.setParams() ## This causes problems when datasets are reloaded (or new datasets loaded) and even without this line, the patterson params are still set properly
    def showParams(self,params=None):
        img = self.parent.viewer.view.view2D.selectedImage
        if img is not None:
            self.imageThreshold.setReadOnly(False)
            self.maskSmooth.setReadOnly(False)
            self.maskThreshold.setReadOnly(False)
            self.darkfield.setEnabled(True)
            self.darkfieldX.setReadOnly(False)
            self.darkfieldY.setReadOnly(False)
            self.darkfieldSigma.setReadOnly(False)
        else:
            self.imageThreshold.setReadOnly(True)
            self.maskSmooth.setReadOnly(True)
            self.maskThreshold.setReadOnly(True)
            self.darkfield.setEnabled(False)
            self.darkfieldX.setReadOnly(True)
            self.darkfieldY.setReadOnly(True)
            self.darkfieldSigma.setReadOnly(True)

        if self.pattersonItem is None:
            self.imageThreshold.setValue(0)
            self.maskSmooth.setValue(0)
            self.maskThreshold.setValue(0)
            self.darkfield.setChecked(0)
            self.darkfieldX.setValue(0)
            self.darkfieldY.setValue(0)
            self.darkfieldSigma.setValue(0)
        else:
            params = self.pattersonItem.getParams(img)
            self.imageThreshold.setValue(params["imageThreshold"])
            self.maskSmooth.setValue(params["maskSmooth"])
            self.maskThreshold.setValue(params["maskThreshold"])
            self.darkfield.setChecked(params["darkfield"])
            self.darkfieldX.setValue(params["darkfieldX"])
            self.darkfieldY.setValue(params["darkfieldY"])
            self.darkfieldSigma.setValue(params["darkfieldSigma"])
            if img != params["_pattersonImg"]:
                self.pattersonItem.patterson = None
                self.pattersonItem.setParams(None,{"_pattersonImg":-1})
    def setParams(self):
        params = {}
        img = self.parent.viewer.view.view2D.selectedImage
        params["imageThreshold"] = self.imageThreshold.value()
        params["maskSmooth"] = self.maskSmooth.value()
        params["maskThreshold"] = self.maskThreshold.value()
        params["darkfield"] = self.darkfield.isChecked()
        params["darkfieldX"] = self.darkfieldX.value()
        params["darkfieldY"] = self.darkfieldY.value()
        params["darkfieldSigma"] = self.darkfieldSigma.value()
        if img is None:
            return
        self.pattersonItem.setParams(img,params)
        # max: needed at psusr to really refresh, works without on my mac
        self.parent.viewer.view.view2D.updateGL()
    def calculatePatterson(self):
        img = self.parent.viewer.view.view2D.selectedImage
        if img is not None:
            self.pattersonItem.requestPatterson(img)
        # max: needed at psusr to really refresh, works without on my mac
        self.parent.viewer.view.view2D.updateGL()
    def toggleVisible(self):
        self.setVisible(not self.isVisible())

class DisplayBox(QtGui.QGroupBox, ui.displayBox.Ui_displayBox):
    def __init__(self,parent):

        QtGui.QGroupBox.__init__(self,parent)
        self.setupUi(self)
        self.parent = parent
        self.intensityHistogram.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
        self.intensityHistogram.hideAxis('left')
        self.intensityHistogram.hideAxis('bottom')
        self.intensityHistogram.setFixedHeight(50)
        region = pyqtgraph.LinearRegionItem(values=[0,1],brush="#ffffff15")
        self.intensityHistogram.addItem(region)
        self.intensityHistogram.autoRange()
        self.intensityHistogramRegion = region

        self.displayMin.setValidator(QtGui.QDoubleValidator())
        self.displayMax.setValidator(QtGui.QDoubleValidator())
        self.displayColormap.setFixedSize(QtCore.QSize(100,30))
        self.displayColormap.setMenu(self.parent.viewer.colormapMenu)
    def pixelClicked(self,hist, edges):
        self.intensityHistogram.clear()
        edges = (edges[:-1]+edges[1:])/2.0
        item = self.intensityHistogram.plot(edges,numpy.log10(hist+1),fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
        self.intensityHistogram.getPlotItem().getViewBox().setMouseEnabled(x=False,y=False)
        self.intensityHistogramRegion = pyqtgraph.LinearRegionItem(values=[float(self.displayMin.text()),float(self.displayMax.text())],brush="#ffffff15")
        self.intensityHistogramRegion.sigRegionChangeFinished.connect(self.parent.onHistogramClicked)
        self.intensityHistogram.addItem(self.intensityHistogramRegion)
        self.intensityHistogram.autoRange()
