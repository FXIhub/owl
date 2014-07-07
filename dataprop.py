#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL
from operator import mul
import numpy,ctypes
import h5py
from matplotlib import colors
from matplotlib import cm
import pyqtgraph
import modelProperties
import fit
import experimentDialog

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
        # properties: data
        self.generalBox = QtGui.QGroupBox("General Properties");
        #self.generalBox.setCheckable(True)
        #self.generalBox.isChecked(True)
        self.generalBox.vbox = QtGui.QVBoxLayout()
        self.generalBox.setLayout(self.generalBox.vbox)
        self.shape = QtGui.QLabel("Shape:", parent=self)
        self.datatype = QtGui.QLabel("Data Type:", parent=self)
        self.datasize = QtGui.QLabel("Data Size:", parent=self)
        self.dataform = QtGui.QLabel("Data Form:", parent=self)

        self.currentViewIndex = QtGui.QLabel("Central Index:", parent=self)

        self.currentImg = QtGui.QLineEdit(self)
        self.currentImg.setMaximumWidth(100)
        self.currentImg.validator = QtGui.QIntValidator()
        self.currentImg.validator.setBottom(0)
        self.currentImg.setValidator(self.currentImg.validator)
        self.currentImg.hbox = QtGui.QHBoxLayout()
        self.currentImg.label = QtGui.QLabel("Central Image:", parent=self)
        self.currentImg.hbox.addWidget(self.currentImg.label)
        self.currentImg.hbox.addStretch()
        self.currentImg.hbox.addWidget(self.currentImg)
        self.currentImg.edited = False

        self.generalBox.vbox.addWidget(self.shape)
        self.generalBox.vbox.addWidget(self.datatype)
        self.generalBox.vbox.addWidget(self.datasize)
        self.generalBox.vbox.addWidget(self.dataform)
        self.generalBox.vbox.addLayout(self.currentImg.hbox)
        self.generalBox.vbox.addWidget(self.currentViewIndex)
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

        #hbox0 = QtGui.QHBoxLayout()
        #vbox = QtGui.QVBoxLayout()
	#self.imageStackMeanButton = QtGui.QPushButton("Mean",parent=self)
	#self.imageStackStdButton = QtGui.QPushButton("Std",parent=self)
	#self.imageStackMinButton = QtGui.QPushButton("Min",parent=self)
	#self.imageStackMaxButton = QtGui.QPushButton("Max",parent=self)
        #validator = QtGui.QIntValidator()
        #validator.setBottom(0)
        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("N:"))
        #self.imageStackNEdit = QtGui.QLineEdit(self)
        #self.imageStackNEdit.setMaximumWidth(100)
        #hbox.addWidget(self.imageStackNEdit)
        #vbox.addWidget(self.imageStackMeanButton)
	#vbox.addWidget(self.imageStackStdButton)
	#vbox.addWidget(self.imageStackMinButton)
	#vbox.addWidget(self.imageStackMaxButton)
        #hbox0.addLayout(hbox)
        #hbox0.addLayout(vbox)
        #self.imageStackBox.vbox.addLayout(hbox0)

        # properties: selected image
        self.imageBox = QtGui.QGroupBox("Selected Image");
        self.imageBox.vbox = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Image:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageImg = widget

        self.imageBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("View index:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.imageViewIndex = widget
        self.imageBox.vbox.addLayout(hbox)

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

        hbox = QtGui.QHBoxLayout()
        hbox.addStretch();
        hbox.addWidget(QtGui.QLabel("No tags available"))
        hbox.addStretch();
        hbox.setSpacing(0);
        widget = QtGui.QWidget()
        widget.setFixedHeight(32)
        hbox.setContentsMargins(0,0,0,0);
        widget.setLayout(hbox)

        self.imageBox.vbox.addWidget(widget)
#        self.imageBox.vbox.addLayout(hbox)
        self.tagsBox = hbox

        self.imageBox.setLayout(self.imageBox.vbox)
        self.imageBox.hide()

        self.pixelBox = QtGui.QGroupBox("Selected Pixel");
        self.pixelBox.vbox = QtGui.QVBoxLayout()

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("X:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.pixelIx = widget
        self.pixelBox.vbox.addLayout(hbox)

        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(QtGui.QLabel("Y:"))
        widget = QtGui.QLabel("None",parent=self)
        hbox.addWidget(widget)
        self.pixelIy = widget
        self.pixelBox.vbox.addLayout(hbox)

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

        vbox = QtGui.QVBoxLayout()

        # autorange
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Autorange")
        label.setToolTip("If enabled scale is dynamically adjusted to min/max range of every image")
        hbox.addWidget(label)
        hbox.addStretch()
        self.displayAutorange = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.displayAutorange)
        vbox.addLayout(hbox)

        # normClamp
        hbox = QtGui.QHBoxLayout()
        label = QtGui.QLabel("Clamp")
        label.setToolTip("If enabled set values outside the min/max range to min/max")
        hbox.addWidget(label)
        hbox.addStretch()
        self.displayClamp = QtGui.QCheckBox("",parent=self)
        hbox.addWidget(self.displayClamp)
        vbox.addLayout(hbox)

        # colormap
        hbox = QtGui.QHBoxLayout()
        hbox.addLayout(vbox)
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

        # pixel stack
        #self.pixelStackBox = QtGui.QGroupBox("Pixel stack")
        #self.pixelStackBox.vbox = QtGui.QVBoxLayout()
        #hbox0 = QtGui.QHBoxLayout()

        #validator = QtGui.QIntValidator()
        #validator.setBottom(0)
        #self.pixelStackXEdit = QtGui.QLineEdit(self)
        #self.pixelStackXEdit.setMaximumWidth(100)
        #self.pixelStackXEdit.setValidator(validator)
        #self.pixelStackYEdit = QtGui.QLineEdit(self)
        #self.pixelStackYEdit.setMaximumWidth(100)
        #self.pixelStackYEdit.setValidator(validator)
        #self.pixelStackNEdit = QtGui.QLineEdit(self)
        #self.pixelStackNEdit.setMaximumWidth(100)
        #self.pixelStackNEdit.setValidator(validator)

        #vbox = QtGui.QVBoxLayout()

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("X:"))
        #hbox.addWidget(self.pixelStackXEdit)
        #vbox.addLayout(hbox)

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("Y:"))
        #hbox.addWidget(self.pixelStackYEdit)
        #vbox.addLayout(hbox)

        #hbox = QtGui.QHBoxLayout()
        #hbox.addWidget(QtGui.QLabel("N:"))
        #hbox.addWidget(self.pixelStackNEdit)
        #vbox.addLayout(hbox)

        #hbox0.addLayout(vbox)

        #self.pixelStackPickButton = QtGui.QPushButton("Pick",self)
        #self.pixelStackPick = False
        #hbox0.addWidget(self.pixelStackPickButton)
        #self.pixelStackBox.vbox.addLayout(hbox0)

        #self.pixelStackPlotButton = QtGui.QPushButton("Plot",self)
        #self.pixelStackBox.vbox.addWidget(self.pixelStackPlotButton)

        #self.pixelStackBox.setLayout(self.pixelStackBox.vbox)
        #self.pixelStackBox.show()

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
        
        # add all widgets to main vbox
        self.vboxScroll.addWidget(self.generalBox)
        self.vboxScroll.addWidget(self.imageBox)
        self.vboxScroll.addWidget(self.pixelBox)
        self.vboxScroll.addWidget(self.displayBox)
        #self.vboxScroll.addWidget(self.pixelStackBox)
        self.vboxScroll.addWidget(self.imageStackBox)
        self.vboxScroll.addWidget(self.sortingBox)
        self.vboxScroll.addWidget(self.filterBox)
        self.vboxScroll.addWidget(self.plotBox)
        self.vboxScroll.addWidget(self.modelProperties)
        self.vboxScroll.addStretch()
        self.setLayout(self.vbox)
        # clear all properties
        self.clear()
        # connect signals
        self.imageStackSubplots.editingFinished.connect(self.emitView2DProp)
        self.displayMax.editingFinished.connect(self.checkLimits)
        self.displayMin.editingFinished.connect(self.checkLimits)
        self.displayClamp.stateChanged.connect(self.emitView2DProp)
        self.displayAutorange.stateChanged.connect(self.emitView2DProp)
        self.displayAutorange.stateChanged.connect(self.setModMinMax)
        self.displayLin.toggled.connect(self.emitView2DProp)
        self.displayLog.toggled.connect(self.emitView2DProp)
        self.displayPow.toggled.connect(self.emitView2DProp)
        self.displayGamma.editingFinished.connect(self.emitView2DProp)
        self.invertSortingCheckBox.toggled.connect(self.emitView2DProp)
        self.invertSortingCheckBox.toggled.connect(self.emitView1DProp)
        self.viewer.colormapActionGroup.triggered.connect(self.emitView2DProp)
        #self.pixelStackPickButton.released.connect(self.onPixelStackPickButton)
        #self.pixelStackPlotButton.released.connect(self.emitView1DProp)
        self.plotLinesCheckBox.toggled.connect(self.emitView1DProp)
        self.plotPointsCheckBox.toggled.connect(self.emitView1DProp)
        self.plotNBinsEdit.editingFinished.connect(self.emitView1DProp)
        self.currentImg.editingFinished.connect(self.onCurrentImg)
        self.modelProperties.paramsChanged.connect(self.emitView2DProp)
        #self.modelProperties.fitNeeded.connect(self.emitView2DProp)
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
        if self.data != None:
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
        if data != None:
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
        if self.data != None and info != None:
            self.imageViewIndex.setText(str(int(info["viewIndex"])))
            self.imageImg.setText(str(int(info["img"])))
            self.imageMin.setText("%.3e" % float(info["imageMin"]))
            self.imageMax.setText("%.3e" % float(info["imageMax"]))
            self.imageSum.setText("%.3e" % float(info["imageSum"]))
            self.imageMean.setText("%.3e" % float(info["imageMean"]))
            self.imageStd.setText("%.3e" % float(info["imageStd"]))
            self.pixelIx.setText(str(int(info["ix"])))
            self.pixelIy.setText(str(int(info["iy"])))
            self.pixelImageValue.setText("%.3f" % (info["imageValue"]))
            if info["maskValue"] == None:
                self.pixelMaskValue.setText("None")
            else:
                self.pixelMaskValue.setText(str(int(info["maskValue"])))
            self.imageBox.show()
            self.pixelBox.show()
            (hist,edges) = numpy.histogram(self.data.data(img=info["img"]),bins=100)
            self.intensityHistogram.clear()
            edges = (edges[:-1]+edges[1:])/2.0
            item = self.intensityHistogram.plot(edges,numpy.log10(hist+1),fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
            self.intensityHistogram.getPlotItem().getViewBox().setMouseEnabled(x=False,y=False)
            self.intensityHistogramRegion = pyqtgraph.LinearRegionItem(values=[self.displayMin.value(),self.displayMax.value()],brush="#ffffff15")
            self.intensityHistogramRegion.sigRegionChangeFinished.connect(self.onHistogramClicked)
            self.intensityHistogram.addItem(self.intensityHistogramRegion)
            self.intensityHistogram.autoRange()
            # Check if we clicked on a tag
            if(info["tagClicked"] != -1):
                # Toggle tag
                self.data.tagsItem.setTag(info["img"],info["tagClicked"],(self.data.tagsItem.tagMembers[info["tagClicked"],info["img"]]+1)%2)
            
            self.showTags(self.data)
            
            self.modelProperties.showParams()
            #if self.pixelStackPick:
            #    self.pixelStackPick = False
            #    self.pixelStackXEdit.setText(str(int(info["ix"])))
            #    self.pixelStackYEdit.setText(str(int(info["iy"])))
            #    self.pixelStackNEdit.setText(str(self.data.shape()[0]))
        else:
            self.imageBox.hide()
            self.pixelBox.hide()
    def onHistogramClicked(self,region):
        (min,max) = region.getRegion()
        self.displayMin.setValue(min)
        self.displayMax.setValue(max)
        self.checkLimits()
        self.emitView2DProp()
    # NORM
    def setNorm(self):
        P = self.view2DProp
        P["normVmin"] = self.displayMin.value()
        P["normVmax"] = self.displayMax.value()
        P["autorange"] = self.displayAutorange.isChecked()
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
        if(settings.contains("normVmin")):
            autorange = bool(settings.value('autorange'))
        else:
            autorange = False
        self.displayAutorange.setChecked(autorange)
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
        P = self.view2DProp
        a = self.viewer.colormapActionGroup.checkedAction()
        self.displayColormap.setText(a.text())
        self.displayColormap.setIcon(a.icon())
        P["colormapText"] = a.text()

    def clearColormap(self):
#        self.displayColormap.setCurrentIndex(0)
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
        if data != None:
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
        c =  self.displayAutorange.isChecked() == False
        self.displayMin.setEnabled(c)
        self.displayMax.setEnabled(c)
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
        self.setCurrentImg()
        self.view2DPropChanged.emit(self.view2DProp)
    def checkLimits(self):
        self.displayMax.setMinimum(self.displayMin.value())
        self.displayMin.setMaximum(self.displayMax.value())
        self.emitView2DProp()
    # still needed?
    def keyPressEvent(self,event):
        if event.key() == QtCore.Qt.Key_H:
            if self.isVisible():
                self.hide()
            else:
                self.show()
    def showTags(self,data):
        img = self.viewer.view.view2D.selectedImage
        if(img == None):
            return
        # clear layout
        while True:
            item = self.tagsBox.takeAt(0)
            if(item):
                if(item.widget()):                
                    item.widget().deleteLater()
            else:
                break
        group = QtGui.QButtonGroup(self)  
        group.setExclusive(False)
        for i in range(0,len(data.tagsItem.tags)):
            pixmap = QtGui.QPixmap(32,32);
            pixmap.fill(data.tagsItem.tags[i][1])
            button = QtGui.QPushButton(pixmap,"")    
            button.setFixedSize(32,32)
            button.setFlat(True)
            button.setCheckable(True)
            button.setToolTip(data.tagsItem.tags[i][0])
            if(data.tagsItem.tagMembers[i,img]):
                button.setChecked(True)
            else:
                button.setChecked(False)
            self.tagsBox.addWidget(button)
            group.addButton(button,i)
        group.buttonClicked[int].connect(self.tagClicked)
        self.tagGroup = group
    def tagClicked(self,id):
        img = self.viewer.view.view2D.selectedImage
        if(img == None):
            return
        value = self.tagGroup.button(id).isChecked()
        self.data.tagItem.setTag(img,id,value)
        self.viewer.tagsChanged = True
    def toggleTag(self,id):
        img = self.viewer.view.view2D.selectedImage
        if(img == None):
            return
        if(self.tagGroup.button(id) == None):
            return
        self.tagGroup.button(id).toggle()
        value = self.tagGroup.button(id).isChecked()
        self.data.tagItem.setTag(img,id,value)
        self.viewer.tagsChanged = True

               

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
            for i,tag in zip(range(nDims),self.dataItem.tags):
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
        if self.histogram.itemPlot != None:
            self.histogram.removeItem(self.histogram.itemPlot)
        #self.histogram.clear()
        item = self.histogram.plot(edges,hist,fillLevel=0,fillBrush=QtGui.QColor(255, 255, 255, 128),antialias=True)
        item.getViewBox().setMouseEnabled(x=False,y=False)
        self.histogram.itemPlot = item
        self.histogram.region.setRegion([vmin,vmax])
        self.histogram.autoRange()
        if self.dataItem.selectedIndex == None:
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
        self.refreshData(self.dataItem)


class ModelProperties(QtGui.QGroupBox, modelProperties.Ui_ModelProperties):
    paramsChanged = QtCore.Signal()
    def __init__(self,parent):
        self.parent = parent
        QtGui.QGroupBox.__init__(self,parent)
        self.setupUi(self)
        self.params = {}
        self.setModelItem(None)
        self.centerX.editingFinished.connect(self.emitParams)
        self.centerY.editingFinished.connect(self.emitParams)
        self.diameter.editingFinished.connect(self.emitParams)
        self.scaling.editingFinished.connect(self.emitParams)
        self.experiment.released.connect(self.onExperiment)
        self.fitPushButton.released.connect(self.calculateFit)
        self.visibilitySlider.sliderMoved.connect(self.emitParams)
    def setModelItem(self,modelItem=None):
        self.modelItem = modelItem
        if modelItem == None:
            paramsImg = None
        else:
            img = self.parent.viewer.view.view2D.selectedImage
            if img == None:
                paramsImg = None
                self.showParams(paramsImg)
            else:
                paramsImg = self.modelItem.getParams(img)
                self.showParams(paramsImg)
                self.emitParams()
    def showParams(self,params=None):
        img = self.parent.viewer.view.view2D.selectedImage
        if self.modelItem == None or img == None:
            self.centerX.setText("")
            self.centerX.setReadOnly(True)
            self.centerY.setText("")
            self.centerY.setReadOnly(True)
            self.diameter.setText("")
            self.diameter.setReadOnly(True)
            self.scaling.setText("")
            self.scaling.setReadOnly(True)
            self.visibilitySlider.setValue(50)
            self.visibilitySlider.setEnabled(False)
        else:
            params = self.modelItem.getParams(img)
            self.centerX.setText(str(params["offCenterX"]))
            self.centerX.setReadOnly(False)
            self.centerY.setText(str(params["offCenterY"]))
            self.centerY.setReadOnly(False)
            self.diameter.setText(str(params["diameterNM"]))
            self.diameter.setReadOnly(False)
            self.scaling.setText(str(params["intensityMJUM2"]))
            self.scaling.setReadOnly(False)
            self.visibilitySlider.setValue(params["_visibility"]*100)
            self.visibilitySlider.setEnabled(True)
    def emitParams(self):
        params = {}
        img = self.parent.viewer.view.view2D.selectedImage
        params["offCenterX"] = float(self.centerX.text())
        params["offCenterY"] = float(self.centerY.text())
        params["diameterNM"] = float(self.diameter.text())
        params["intensityMJUM2"] = float(self.scaling.text())
        params["_visibility"] = float(self.visibilitySlider.value()/100.)
        self.modelItem.setParams(img,params)
        self.paramsChanged.emit()
    def onExperiment(self):
        expDialog = ExperimentDialog(self)
        expDialog.exec_()
    def calculateFit(self):
        img = self.parent.viewer.view.view2D.selectedImage
        self.modelItem.centerAndFit(img)
        self.showParams()
    def toggleVisible(self):
        self.setVisible(not self.isVisible())


class ExperimentDialog(QtGui.QDialog, experimentDialog.Ui_ExperimentDialog):
    def __init__(self,modelProperties):
        QtGui.QDialog.__init__(self,modelProperties,QtCore.Qt.WindowTitleHint)
        self.setupUi(self)
        self.modelProperties = modelProperties
        self.materialType.addItems(fit.DICT_atomic_composition.keys())
        params = self.modelProperties.modelItem.getParams(0)
        self.wavelength.setValue(params["photonWavelengthNM"])
        self.syncEnergy()
        self.distance.setValue(params["detectorDistanceMM"])
        self.pixelSize.setValue(params["detectorPixelSizeUM"])
        allItems = [self.materialType.itemText(i) for i in range(self.materialType.count())]
        self.materialType.setCurrentIndex(allItems.index(params["materialType"]))
        self.wavelength.editingFinished.connect(self.syncEnergy)
        self.energy.editingFinished.connect(self.syncWavelength)
        self.buttonBox.accepted.connect(self.onOkButtonClicked)
    def syncEnergy(self):
        wl = self.wavelength.value()
        h = fit.DICT_physical_constants['h']
        c = fit.DICT_physical_constants['c']
        qe = fit.DICT_physical_constants['e']
        ey = h*c/wl/1.E-9/qe
        self.energy.setValue(ey)
    def syncWavelength(self):
        ey = self.energy.value()
        h = fit.DICT_physical_constants['h']
        c = fit.DICT_physical_constants['c']
        qe = fit.DICT_physical_constants['e']
        wl = h*c/ey/1.E-9/qe
        self.wavelength.setValue(wl)
    def onOkButtonClicked(self):
        print "Here we are!"
        params = {}
        params["photonWavelengthNM"] = self.wavelength.value()
        params["photonEnergyEV"] = self.energy.value()
        params["detectorDistanceMM"] = self.distance.value()
        params["detectorPixelSizeUM"] = self.pixelSize.value()
        params["materialType"] = self.materialType.currentText()
        self.modelProperties.modelItem.setParams(None,params)
