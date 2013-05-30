from PySide import QtGui, QtCore
import pyqtgraph
import numpy
from view import View

class View1D(View,QtGui.QFrame):
    viewIndexSelected = QtCore.Signal(int)
    datasetXChanged = QtCore.Signal(object)
    datasetYChanged = QtCore.Signal(object)
    def __init__(self,parent=None):
        View.__init__(self,parent,"plot")
        QtGui.QFrame.__init__(self,parent)
        self.hbox = QtGui.QHBoxLayout(self)
        margin = 20
        self.hbox.setContentsMargins(margin,margin,margin,margin)
        self.initPlot()
        self.hbox.addWidget(self.plot)
        self.setLayout(self.hbox)
        self.setAcceptDrops(True)
        self.plotMode = "plot"
        self.dataY = None
        self.dataX = None
        self.ix = None
        self.iy = None
        self.N = None
        self.applyIndexProjector = True
        self.nBins = 200
        self.stackSizeChanged.connect(self.refreshPlot)
    def initPlot(self,widgetType="plot"):
        self.lineColor = (255,255,255)
        self.lineWidth = 1
        self.line = True
        self.symbolColor = (255,255,255)
        self.symbolSize = 1
        self.symbol = None
        self.plot = pyqtgraph.PlotWidget()
        infLine = pyqtgraph.InfiniteLine(0,90,None,True)
        self.plot.addItem(infLine)
        infLine.sigPositionChangeFinished.connect(self.emitViewIndexSelected)    
        self.infLine = infLine
        space = 60
        self.p = self.plot.plot([0])#,symbol=1,symbolSize=1,symbolBrush=(255,255,255,255),symbolPen=None,pen=None)
        self.p.setPointMode(True)
        self.p.setPen(None)
        self.plot.getAxis("top").setHeight(space)
        self.plot.getAxis("bottom").setHeight(space)
        self.plot.getAxis("left").setWidth(space)
        self.plot.getAxis("right").setWidth(space)
        self.setStyle()
        #self.p.update()
    def setStyle(self,**kwargs):
        self.lineWidth = kwargs.get("lineWidth",self.lineWidth)
        self.lineColor = kwargs.get("lineColor",self.lineColor)
        self.line = kwargs.get("line",self.line)
        self.symbolSize = kwargs.get("symbolSize",self.symbolSize)
        self.symbolColor = kwargs.get("symbolColor",self.symbolColor)
        self.symbol = kwargs.get("symbol",self.symbol)
        if self.line == None:
            self.p.setPen(None)
        else:
            pen = pyqtgraph.mkPen(color=self.lineColor,width=self.lineWidth)
            self.p.setPen(pen)
        self.p.setSymbol(self.symbol)
        self.p.setSymbolPen(None)
        if self.symbol != None:
            self.p.setSymbolBrush(self.symbolColor)
            self.p.setSymbolSize(self.symbolSize)
        else:
            self.p.setSymbolBrush((0,0,0))
            self.p.setSymbolSize(0)
    def setData(self,data,axis):
        if axis == "X":
            self.dataX = data
            if hasattr(data,"name"): 
                self.dataXLabel = data.name
            else:
                self.dataXLabel = ""
            self.datasetXChanged.emit(data)
        elif axis == "Y":
            self.dataY = data
            if hasattr(data,"name"):
                self.dataYLabel = data.name
            else:
                self.dataYLabel = ""
            self.setStack()
            self.datasetYChanged.emit(data)
    def setStack(self,ix=None,iy=None,N=None):
        self.ix = ix
        self.iy = iy
        self.N = N
    def getData(self,axis):
        if axis=="X":
            data = self.dataX
        elif axis == "Y":
            data = self.dataY
            if self.ix != None and self.iy != None and data != None:
                numEvents = data.get("numEvents",data.shape[0])
                if self.N != None and self.N <= numEvents:
                    N = self.N
                    iz = numpy.random.randint(0,numEvents,N)
                    iz.sort()
                    data = numpy.zeros(N)
                    # for some reason the following line causes hdf5 errors if the dataset is getting very large
                    #data[:] = self.data[iz,:,:]
                    for i in range(N):
                        data[i] = data[iz[i],iy,ix]
                else:
                    data = data[:numEvents,iy,ix]
        if data != None:
            data = numpy.array(data).flatten()
        return data
    def setPlotMode(self,plotMode):
        self.plotMode = plotMode
        if plotMode == "plot" or plotMode == "average":
            if self.dataX != None:
                xlabel = self.dataX.name
            else:
                xlabel = "index"
            if self.dataY != None:
                ylabel = self.dataY.name
            else:
                ylabel = ""
        elif plotMode == "histogram":
            ylabel = "#"
            if self.dataY != None:
                xlabel = self.dataY.name
            else:
                xlabel = ""
        self.plot.setLabel("bottom",xlabel)
        self.plot.setLabel("left",ylabel)
    def refreshPlot(self):
        if self.ix != None and self.iy != None and self.N != None:
            dataY = self.getData("Y",ix=self.ix,iy=self.iy,N=self.N)
            dataX = self.getData("X")
            if dataX == None and dataY != None:
                dataX = numpy.arange(len(self.getData("Y")))
        else:
            dataY = self.getData("Y")
            dataX = self.getData("X")
            if dataX == None and dataY != None:
                dataX = numpy.arange(len(self.getData("Y")))
            # that is not particularly nice
            if dataY != None and self.indexProjector.imgs != None:
                if dataY.shape == self.indexProjector.imgs.shape:
                    dataY = dataY[self.indexProjector.imgs]
            if dataX != None and self.indexProjector.imgs != None:
                if dataX.shape == self.indexProjector.imgs.shape:
                    dataX = dataX[self.indexProjector.imgs]
        if dataY == None:
            return
        if self.p == None:
            self.initPlot()
        # line show/hide does not seem to have any effect
        if self.plotMode == "plot":
            self.p.setData(dataX,dataY)
            self.infLine.show()
        elif self.plotMode == "histogram":
            (hist,edges) = numpy.histogram(dataY,bins=self.nBins)
            edges = (edges[:-1]+edges[1:])/2.0
            self.p.setData(edges,hist)        
            self.infLine.hide()
        elif self.plotMode == "average":
            self.p.setData(self.movingAverage(dataY,1000))
            self.infLine.hide()
        self.plot.enableAutoRange('xy')
    def emitViewIndexSelected(self,foovalue=None):
        index = int(self.infLine.getXPos())
        self.viewIndexSelected.emit(index)
    def refreshDisplayProp(self,datasetProp):
        self.refreshPlot()
    def movingAverage(self,data, window_size):
        window= numpy.ones(int(window_size))/float(window_size)
        return numpy.convolve(data, window, 'same')
    def onTogglePlotLines(self):
        if self.line == True:
            self.line = None
        else:
            self.line = True
        self.setStyle(line=self.line)
    def onTogglePlotPoints(self):
        if self.symbol == "o":
            self.symbol = None
        else:
            self.symbol = "o"
        self.setStyle(symbol=self.symbol)
    def onPlotNBinsEdit(self):
        self.nBins = int(self.sender().text())
        self.refreshPlot()
