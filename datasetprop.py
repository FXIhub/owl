#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL
from operator import mul
import numpy,ctypes
import h5py
from matplotlib import colors
from matplotlib import cm
import pyqtgraph

def sizeof_fmt(num):
    for x in ['bytes','kB','MB','GB']:
        if num < 1024.0:
            return "%3.1f %s" % (num, x)
        num /= 1024.0
    return "%3.1f %s" % (num, 'TB')
    

# Consistent function nomenclature:
# - currDisplayProp['propertyBla'] => class variables defining current property
# - setProperty                    => stores property specified in widgets to class variables propertyBla,propertyBlabla,...
#(- refreshProperty                => refreshes widgets that have dependencies on dataset )
# - clearProperty                  => sets property to default (+ refreshes property)
#
class DatasetProp(QtGui.QWidget):
    displayPropChanged = QtCore.Signal(dict)
    pixelStackChanged = QtCore.Signal(h5py.Dataset,int,int,int)
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.setFocusPolicy(QtCore.Qt.ClickFocus)

        self.viewer = parent
        # this dict holds all current settings
        self.currDisplayProp = {}
        self.vbox = QtGui.QVBoxLayout()
        # scrolling
        self.vboxScroll = QtGui.QVBoxLayout()
        self.scrollWidget = QtGui.QWidget()
        self.scrollWidget.setLayout(self.vboxScroll)
        self.scrollArea = QtGui.QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setFrameShape(QtGui.QFrame.NoFrame)
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        #self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.vbox.addWidget(self.scrollArea)
        # GENERAL PROPERTIES
        # properties: dataset
        self.generalBox = QtGui.QGroupBox("General Properties");
        #self.generalBox.setCheckable(True)
        #self.generalBox.isChecked(True)
        self.generalBox.vbox = QtGui.QVBoxLayout()
        self.generalBox.setLayout(self.generalBox.vbox)
        self.dimensionality = QtGui.QLabel("Dimensions:", parent=self)
        self.datatype = QtGui.QLabel("Data Type:", parent=self)
        self.datasize = QtGui.QLabel("Data Size:", parent=self)
        self.dataform = QtGui.QLabel("Data Form:", parent=self)
        self.currentViewIndex = QtGui.QLabel("Visible View Index:", parent=self)
        self.currentImg = QtGui.QLabel("Visible Image:", parent=self)
        self.generalBox.vbox.addWidget(self.dimensionality)
        self.generalBox.vbox.addWidget(self.datatype)
        self.generalBox.vbox.addWidget(self.datasize)
        self.generalBox.vbox.addWidget(self.dataform)
        self.generalBox.vbox.addWidget(self.currentImg)
        self.generalBox.vbox.addWidget(self.currentViewIndex)
        # properties: image stack
        self.imageStackBox = QtGui.QGroupBox("Image Stack Properties");
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
        # properties: selected image
        self.imageBox = QtGui.QGroupBox("Selected Image");
        self.imageBox.vbox = QtGui.QVBoxLayout()
        
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Minimum value:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageMin = widget
        self.imageBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Maximum value:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageMax = widget
        self.imageBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Sum:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageSum = widget
        self.imageBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Mean value:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageMean = widget
        self.imageBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Std. deviation:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageStd = widget
        self.imageBox.vbox.addLayout(hbox)

        self.imageBox.setLayout(self.imageBox.vbox)
        self.imageBox.hide()

        self.pixelBox = QtGui.QGroupBox("Selected Pixel");
        self.pixelBox.vbox = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Image value:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.pixelImageValue = widget
        self.pixelBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Mask value:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.pixelMaskValue = widget
        self.pixelBox.vbox.addLayout(hbox)

        self.pixelBox.setLayout(self.pixelBox.vbox)
        self.pixelBox.hide()
        # DISPLAY PROPERTIES
        self.displayBox = QtGui.QGroupBox("Display Properties");
        self.displayBox.vbox = QtGui.QVBoxLayout()
        self.intensityHistogram = pyqtgraph.PlotWidget()
        self.intensityHistogram.hideAxis('left')
        self.intensityHistogram.hideAxis('bottom')
        self.intensityHistogram.setFixedHeight(50)
        region = pyqtgraph.LinearRegionItem(values=[0,1],brush="#ffffff15")
        self.intensityHistogram.addItem(region)
        self.intensityHistogram.autoRange()
        self.intensityHistogramRegion = region

        # Make the histogram fit the available width
        self.intensityHistogram.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
        self.displayBox.vbox.addWidget(self.intensityHistogram)
        # property: NORM        
        # normVmax
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Maximum value:"))
        self.displayMax = QtGui.QDoubleSpinBox(parent=self)
        self.displayMax.setMinimum(-1000000.)
        self.displayMax.setMaximum(1000000.)
        self.displayMax.setSingleStep(1.)
        hbox.addWidget(self.displayMax)
        self.displayBox.vbox.addLayout(hbox)
        # normVmin
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Minimum value:"))
        self.displayMin = QtGui.QDoubleSpinBox(parent=self)
        self.displayMin.setMinimum(-1000000.)
        self.displayMin.setMaximum(1000000.)
        self.displayMin.setSingleStep(1.)
        hbox.addWidget(self.displayMin)
        self.displayBox.vbox.addLayout(hbox)


        # normClamp
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Clamp")
        label.setToolTip("If enabled set values outside the min/max range to min/max")
        hbox.addWidget(label)
        self.displayClamp = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.displayClamp)
        hbox.addStretch()
        self.displayColormap = QtGui.QPushButton("Colormap",parent=self)
        self.displayColormap.setFixedSize(QtCore.QSize(100,30))
        self.displayColormap.setMenu(self.viewer.colormapMenu)
        hbox.addWidget(self.displayColormap)

        self.displayBox.vbox.addLayout(hbox)
        # normText
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel("Scaling:"))
        self.displayLin = QtGui.QRadioButton("Linear")
        self.displayLog = QtGui.QRadioButton("Logarithmic")
        self.displayPow = QtGui.QRadioButton("Power")
        vbox.addWidget(self.displayLin)
        vbox.addWidget(self.displayLog)
        # normGamma
        hbox = QtGui.QHBoxLayout()
        self.displayGamma = QtGui.QDoubleSpinBox(parent=self)
        self.displayGamma.setValue(0.25);
        self.displayGamma.setSingleStep(0.25);
        hbox.addWidget(self.displayPow)
        hbox.addWidget(self.displayGamma)        
        vbox.addLayout(hbox)
        self.displayBox.vbox.addLayout(vbox)
        self.displayBox.setLayout(self.displayBox.vbox)
        # sorting
        self.sortingBox = QtGui.QGroupBox("Sorting")
        self.sortingBox.vbox = QtGui.QVBoxLayout()
        self.sortingDatasetLabel = QtGui.QLabel("",parent=self)
        self.sortingBox.vbox.addWidget(self.sortingDatasetLabel)
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
        # pixel stack
        self.pixelStackBox = QtGui.QGroupBox("Pixel stack")
        self.pixelStackBox.vbox = QtGui.QVBoxLayout()
        hbox0 = QtGui.QHBoxLayout()

        validator = QtGui.QIntValidator()
        validator.setBottom(0)
        self.pixelStackXEdit = QtGui.QLineEdit(self)
        self.pixelStackXEdit.setMaximumWidth(100)
        self.pixelStackXEdit.setValidator(validator)
        self.pixelStackYEdit = QtGui.QLineEdit(self)
        self.pixelStackYEdit.setMaximumWidth(100)
        self.pixelStackYEdit.setValidator(validator)
        self.pixelStackNEdit = QtGui.QLineEdit(self)
        self.pixelStackNEdit.setMaximumWidth(100)
        self.pixelStackNEdit.setValidator(validator)

        vbox = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("X:"))
        hbox.addWidget(self.pixelStackXEdit)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Y:"))
        hbox.addWidget(self.pixelStackYEdit)
        vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("N:"))
        hbox.addWidget(self.pixelStackNEdit)
        vbox.addLayout(hbox)

        hbox0.addLayout(vbox)

        self.pixelStackPickButton = QtGui.QPushButton("Pick",self)
        self.pixelStackPick = False
        hbox0.addWidget(self.pixelStackPickButton)
        self.pixelStackBox.vbox.addLayout(hbox0)

        self.pixelStackPlotButton = QtGui.QPushButton("Plot",self)
        self.pixelStackBox.vbox.addWidget(self.pixelStackPlotButton)
        
        self.pixelStackBox.setLayout(self.pixelStackBox.vbox)
        self.pixelStackBox.show()

###

        #self.plotBox = QtGui.QGroupBox("Plot")
        #self.plotBox.vbox = QtGui.QVBoxLayout()
        #hbox0 = QtGui.QHBoxLayout()

        #validatorInt = QtGui.QIntValidator()
        #validatorInt.setBottom(0)
        #validatorSci = QtGui.QDoubleValidator()
        #validatorSci.setDecimals(3)
        #validatorSci.setNotation(QtGui.QDoubleValidator.ScientificNotation)

        #self.plotNBinsEdit = QtGui.QLineEdit(self)
        #self.plotNBinsEdit.setMaximumWidth(100)
        #self.plotNBinsEdit.setValidator(validatorInt)

        #self.plotXMinEdit = QtGui.QLineEdit(self)
        #self.plotXMinEdit.setMaximumWidth(100)
        #self.plotXMinEdit.setValidator(validatorSci)

        #self.plotXMaxEdit = QtGui.QLineEdit(self)
        #self.plotXMaxEdit.setMaximumWidth(100)
        #self.plotXMaxEdit.setValidator(validatorSci)

        #self.plotNEdit = QtGui.QLineEdit(self)
        #self.plotNEdit.setMaximumWidth(100)
        #self.plotNEdit.setValidator(validatorSci)

        #vbox = QtGui.QVBoxLayout()

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("X:"))
        #hbox.addWidget(self.plotXEdit)
        #vbox.addLayout(hbox)

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("Y:"))
        #hbox.addWidget(self.plotYEdit)
        #vbox.addLayout(hbox)

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("N:"))
        #hbox.addWidget(self.plotNEdit)
        #vbox.addLayout(hbox)

        #hbox0.addLayout(vbox)

        #self.plotPickButton = QtGui.QPushButton("Pick",self)
        #self.plotPick = False
        #hbox0.addWidget(self.plotPickButton)
        #self.plotBox.vbox.addLayout(hbox0)

        #self.plotPlotButton = QtGui.QPushButton("Plot",self)
        #self.plotBox.vbox.addWidget(self.plotPlotButton)
        
        #self.plotBox.setLayout(self.plotBox.vbox)
        #self.plotBox.show()



###

        # add all widgets to main vbox
        self.vboxScroll.addWidget(self.generalBox)
        self.vboxScroll.addWidget(self.imageBox)        
        self.vboxScroll.addWidget(self.pixelBox)        
        self.vboxScroll.addWidget(self.imageStackBox)
        self.vboxScroll.addWidget(self.pixelStackBox)
        self.vboxScroll.addWidget(self.displayBox)
        self.vboxScroll.addWidget(self.sortingBox)
        self.vboxScroll.addWidget(self.filterBox)
        self.vboxScroll.addStretch()
        self.setLayout(self.vbox)
        # clear all properties
        self.clear()
        # connect signals
        self.imageStackSubplots.editingFinished.connect(self.emitDisplayProp)    
        self.displayMax.editingFinished.connect(self.checkLimits)
        self.displayMin.editingFinished.connect(self.checkLimits)
        self.displayClamp.stateChanged.connect(self.emitDisplayProp)
        self.displayLin.toggled.connect(self.emitDisplayProp)        
        self.displayLog.toggled.connect(self.emitDisplayProp)
        self.displayPow.toggled.connect(self.emitDisplayProp)
        self.displayGamma.editingFinished.connect(self.emitDisplayProp)
        self.invertSortingCheckBox.toggled.connect(self.emitDisplayProp)
        self.viewer.colormapActionGroup.triggered.connect(self.emitDisplayProp)
        self.pixelStackPickButton.released.connect(self.onPixelStackPickButton)
        self.pixelStackPlotButton.released.connect(self.onPixelStackPlotButton)
    def clear(self):
        self.clearDisplayProp()
        self.clearDataset()
    def clearDisplayProp(self):
        self.clearImageStackSubplots()
        self.clearNorm()
        self.clearColormap()
    # DATASET
    def setDataset(self,dataset=None,format=2):
        self.dataset = dataset
        if dataset != None:
            self.dataset = dataset
            string = "Dimensions: "
            shape = list(dataset.shape)
            if dataset.getCXIStackSize():
                shape[0] = dataset.getCXIStackSize()
            for d in shape:
                string += str(d)+"x"
            string = string[:-1]
            self.dimensionality.setText(string)
            self.datatype.setText("Data Type: %s" % (dataset.dtype.name))
            self.datasize.setText("Data Size: %s" % sizeof_fmt(dataset.dtype.itemsize*reduce(mul,dataset.shape)))
            if dataset.isCXIStack():
                form = "%iD Data Stack" % dataset.getCXIFormat()
            else:
                form = "%iD Data" % dataset.getCXIFormat()
            self.dataform.setText("Data form: %s" % form)
            if dataset.isCXIStack():
                self.imageStackBox.show()
            else:
                self.imageStackBox.hide()
        else:
            self.clearDataset()
    def refreshDatasetCurrent(self,img,NImg,viewIndex,NViewIndex):
        self.currentImg.setText("Visible Image: %i (%i)" % (img,NImg))
        self.currentViewIndex.setText("Visible Index: %i (%i)" % (viewIndex,NViewIndex))
    def clearDataset(self):
        self.dataset = None
        self.dimensionality.setText("Dimensions: ")
        self.datatype.setText("Data Type: ")
        self.datasize.setText("Data Size: ")
        self.dataform.setText("Data Form: ")
        self.imageStackBox.hide()
    # VIEW
    def onPixelClicked(self,info):
        if self.dataset != None and info != None:
            self.imageBox.setTitle("Selected Image (image: %i, index: %i)" % (int(info["viewIndex"]),int(info["img"])))
            self.imageMin.setText(str(int(info["imageMin"])))
            self.imageMax.setText(str(int(info["imageMax"])))
            self.imageSum.setText(str(int(info["imageSum"])))
            self.imageMean.setText("%.3e" % float(info["imageMean"]))
            self.imageStd.setText("%.3e" % float(info["imageStd"]))
            self.pixelBox.setTitle("Selected Pixel (x: %i, y: %i)" % (int(info["ix"]),int(info["iy"])))
            self.pixelImageValue.setText(str(int(info["imageValue"])))
            if info["maskValue"] == None:
                self.pixelMaskValue.setText("None")
            else:
                self.pixelMaskValue.setText(str(int(info["maskValue"])))
            self.imageBox.show()
            self.pixelBox.show()
            (hist,edges) = numpy.histogram(self.dataset[info["img"]],bins=100)
            self.intensityHistogram.clear()
            edges = (edges[:-1]+edges[1:])/2.0
            item = self.intensityHistogram.plot(edges,hist,fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
            self.intensityHistogram.getPlotItem().getViewBox().setMouseEnabled(x=False,y=False)
            region = pyqtgraph.LinearRegionItem(values=[self.displayMin.value(),self.displayMax.value()],brush="#ffffff15")
            region.sigRegionChangeFinished.connect(self.onHistogramClicked)
            self.intensityHistogram.addItem(region)
            self.intensityHistogram.autoRange()
            self.intensityHistogramRegion = region
            if self.pixelStackPick:
                self.pixelStackPick = False
                self.pixelStackXEdit.setText(str(int(info["ix"])))
                self.pixelStackYEdit.setText(str(int(info["iy"])))
                self.pixelStackNEdit.setText(str(len(self.dataset)))
        else:
            self.imageBox.hide()
            self.pixelBox.hide()
    def onHistogramClicked(self,region):
        (min,max) = region.getRegion()
        self.displayMin.setValue(min)
        self.displayMax.setValue(max)
        self.checkLimits()
        self.emitDisplayProp()
    # NORM
    def setNorm(self):
        P = self.currDisplayProp
        P["normVmin"] = self.displayMin.value()
        P["normVmax"] = self.displayMax.value()
        P["normClamp"] = self.displayClamp.isChecked()
        if self.displayLin.isChecked():
            P["normScaling"] = "lin"
        elif self.displayLog.isChecked():
            P["normScaling"] = "log"
        else:
            P["normScaling"] = "pow"
        P["normGamma"] = self.displayGamma.value()
        self.intensityHistogramRegion.setRegion([self.displayMin.value(),self.displayMax.value()])
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
        self.displayMin.setValue(normVmin)
        self.displayMax.setValue(normVmax)
        if(settings.contains("normClamp")):
            normClamp = bool(settings.value('normClamp'))
        else:
            normClamp = True
        self.displayClamp.setChecked(normClamp)
        if(settings.contains("normGamma")):
            self.displayGamma.setValue(float(settings.value("normGamma")))
        else:
            self.displayGamma.setValue(0.25)
        if(settings.contains("normScaling")):
            norm = settings.value("normScaling")
            if(norm == "lin"):
                self.displayLin.setChecked(True)
            elif(norm == "log"):
                self.displayLog.setChecked(True)
            elif(norm == "pow"):
                self.displayPow.setChecked(True)
            else:
                sys.exit(-1)
        else:
            self.displayLog.setChecked(True)
        self.setNorm()
    # COLORMAP
    def setColormap(self,foovalue=None):
        P = self.currDisplayProp
        a = self.viewer.colormapActionGroup.checkedAction()
        self.displayColormap.setText(a.text())        
        self.displayColormap.setIcon(a.icon())        
        P["colormapText"] = a.text()

    def clearColormap(self):
#        self.displayColormap.setCurrentIndex(0)
        self.setColormap()
    # STACK
    def setImageStackSubplots(self,foovalue=None):
        P = self.currDisplayProp
        P["imageStackSubplotsValue"] = self.imageStackSubplots.value()
    def clearImageStackSubplots(self):
        self.imageStackSubplots.setValue(1)
        self.setImageStackSubplots()
    # SORTING
    def setSorting(self,foo=None):
        P = self.currDisplayProp
        P["sortingInverted"] = self.invertSortingCheckBox.isChecked()
        P["sortingDataset"] = self.sortingDataset
    def clearSorting(self):
        self.sortingDataset = None
        self.sortingInverted = False
        self.sortingDatasetLabel.setText("")
        self.sortingBox.hide()
    def refreshSorting(self,dataset):
        if dataset != None:
            self.sortingDataset = dataset
            self.sortingBox.show()
            self.sortingDatasetLabel.setText(dataset.name)
        else:
            self.clearSorting()
    # FILTERS
    def addFilter(self,dataset):
        if self.inactiveFilters == []:
            filterWidget = FilterWidget(self,dataset)
            filterWidget.limitsChanged.connect(self.emitDisplayProp)
            self.filterBox.vbox.addWidget(filterWidget)
            self.activeFilters.append(filterWidget)
        else:
            self.activeFilters.append(self.inactiveFilters.pop(0))
            filterWidget = self.activeFilters[-1]
            filterWidget.show()
            filterWidget.refreshDataset(dataset)
        self.setFilters()
        self.filterBox.show()
    def removeFilter(self,index):
        filterWidget = self.activeFilters.pop(index)
        self.filterBox.vbox.removeWidget(filterWidget)
        self.filterBox.vbox.addWidget(filterWidget)
        self.inactiveFilters.append(filterWidget)
        filterWidget.hide()
        filterWidget.histogram.clear()
        filterWidget.hide()
        self.setFilters()
        if self.activeFilters == []:
            self.filterBox.hide()
    def setFilters(self,foo=None):
        P = self.currDisplayProp
        P["filterMask"] = None
        if self.activeFilters != []:
            for f in self.activeFilters:
                if P["filterMask"] == None:
                    P["filterMask"] = numpy.ones(len(f.dataset),dtype="bool")
                vmin = float(f.vminLineEdit.text())
                vmax= float(f.vmaxLineEdit.text())
                data = numpy.array(f.dataset,dtype="float")
                P["filterMask"] *= (data >= vmin) * (data <= vmax)
            Ntot = len(data)
            Nsel = P["filterMask"].sum()
            p = 100*Nsel/(1.*Ntot)
        else:
            Ntot = 0
            Nsel = 0
            p = 100.
        self.filterBox.setTitle("Filters (yield: %.2f%% - %i/%i)" % (p,Nsel,Ntot))
    def refreshFilter(self,dataset,index):
        self.activeFilters[index].refreshDataset(dataset)
    # pixel stack histogram
    #def setPixelStack(self):
    #    P = self.currDisplayProp
    #    x = self.pixelStackXEdit.text()
    #    y = self.pixelStackYEdit.text()
    #    if x == "" or y == "":
    #        P["pixelStackX"] = None
    #        P["pixelStackY"] = None
    #    else:
    #        P["pixelStackX"] = int(x)
    #        P["pixekStackY"] = int(y)
    def clearPixelStack(self):
        self.pixelStackXEdit.setText("")
        self.pixelStackYEdit.setText("")
        self.pixelStackNEdit.setText("")
    def onPixelStackPickButton(self):
        self.pixelStackPick = True
    def onPixelStackPlotButton(self):
        ix = int(self.pixelStackXEdit.text())
        iy = int(self.pixelStackYEdit.text())
        if self.pixelStackNEdit.text() == "" or int(self.pixelStackNEdit.text()) == len(self.dataset):
            N = 0
        else:
            N = int(self.pixelStackNEdit.text())
        self.pixelStackChanged.emit(self.dataset.name,ix,iy,N)
    # update and emit current diplay properties
    def emitDisplayProp(self,foovalue=None):
        self.setImageStackSubplots()
        self.setNorm()
        self.setColormap()
        self.setSorting()
        self.setFilters()
        self.displayPropChanged.emit(self.currDisplayProp)
    def checkLimits(self):
        self.displayMax.setMinimum(self.displayMin.value())
        self.displayMin.setMaximum(self.displayMax.value())
        self.emitDisplayProp()
    # still needed?
    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_H:
            if self.isVisible():
                self.hide()
            else:
                self.show()


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
    def __init__(self,parent,dataset):
        QtGui.QWidget.__init__(self,parent)
        vbox = QtGui.QVBoxLayout()
        nameLabel = QtGui.QLabel(dataset.name)
        yieldLabel = QtGui.QLabel("")
        vmin = numpy.min(dataset)
        vmax = numpy.max(dataset)
        histogram = pyqtgraph.PlotWidget(self)
        histogram.hideAxis('left')
        histogram.hideAxis('bottom')
        histogram.setFixedHeight(50)
        # Make the histogram fit the available width
        histogram.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Preferred)
        region = pyqtgraph.LinearRegionItem(values=[vmin,vmax],brush="#ffffff15")
        region.sigRegionChangeFinished.connect(self.syncLimits)
        histogram.addItem(region)
        histogram.autoRange()
        vbox.addWidget(histogram)
        vbox.addWidget(nameLabel)
        vbox.addWidget(yieldLabel)
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Min.:"))
        hbox.addWidget(QtGui.QLabel("Max.:"))
        vbox.addLayout(hbox)
        hbox = QtGui.QHBoxLayout()
        validator = QtGui.QDoubleValidator()
        validator.setDecimals(3)
        validator.setNotation(QtGui.QDoubleValidator.ScientificNotation)
        vminLineEdit = QtGui.QLineEdit(self)
        vminLineEdit.setText("%.3e" % (vmin*0.999))
        vminLineEdit.setValidator(validator)
        hbox.addWidget(vminLineEdit)
        vmaxLineEdit = QtGui.QLineEdit(self)
        vmaxLineEdit.setText("%.3e" % (vmax*1.001))
        vmaxLineEdit.setValidator(validator)
        hbox.addWidget(vmaxLineEdit)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        self.dataset = dataset
        self.histogram = histogram
        self.histogram.region = region
        self.histogram.itemPlot = None
        self.nameLabel = nameLabel
        self.yieldLabel = yieldLabel
        self.vminLineEdit = vminLineEdit
        self.vmaxLineEdit = vmaxLineEdit
        self.vbox = vbox
        self.refreshDataset(dataset)
        vminLineEdit.editingFinished.connect(self.emitLimitsChanged)
        vmaxLineEdit.editingFinished.connect(self.emitLimitsChanged)
    def refreshDataset(self,dataset):
        self.nameLabel.setText(dataset.name)
        Ntot = len(dataset)
        vmin = numpy.min(dataset)
        vmax = numpy.max(dataset)
        yieldLabelString = "Yield: %.2f%% - %i/%i" % (100.,Ntot,Ntot)
        self.yieldLabel.setText(yieldLabelString)
        self.dataset = dataset
        (hist,edges) = numpy.histogram(dataset,bins=100)
        edges = (edges[:-1]+edges[1:])/2.0
        if self.histogram.itemPlot != None:
            self.histogram.removeItem(self.histogram.itemPlot)
        #self.histogram.clear()
        item = self.histogram.plot(edges,hist,fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
        item.getViewBox().setMouseEnabled(x=False,y=False)
        self.histogram.itemPlot = item
        self.histogram.region.setRegion([vmin,vmax])
        self.histogram.autoRange()
    def syncLimits(self):
        (vmin,vmax) = self.histogram.region.getRegion()
        self.vminLineEdit.setText("%.3e" % (vmin*0.999))
        self.vmaxLineEdit.setText("%.3e" % (vmax*1.001))
        self.emitLimitsChanged()
    def emitLimitsChanged(self,foo=None):
        data = numpy.array(self.dataset,dtype="float") 
        Ntot = len(data)
        vmin = float(self.vminLineEdit.text())
        vmax = float(self.vmaxLineEdit.text())
        Nsel = ( (data<=vmax)*(data>=vmin) ).sum()
        label = "Yield: %.2f%% - %i/%i" % (100*Nsel/(1.*Ntot),Nsel,Ntot)
        self.yieldLabel.setText(label)
        self.limitsChanged.emit(vmin,vmax)
    
