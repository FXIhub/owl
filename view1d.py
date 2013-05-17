from PySide import QtGui, QtCore
import pyqtgraph
import numpy
from view import View

class View1D(View,QtGui.QFrame):
    viewIndexSelected = QtCore.Signal(int)
    def __init__(self,parent=None):
        View.__init__(self,parent,"plot")
        QtGui.QFrame.__init__(self,parent)
        self.hbox = QtGui.QHBoxLayout(self)
        margin = 20
        self.hbox.setContentsMargins(margin,margin,margin,margin)
        self.initPlot()
        self.hbox.addWidget(self.plot)
        self.setLayout(self.hbox)
        self.p = None
        self.setAcceptDrops(True)
        self.plotMode = "plot"
        self.ix = None
        self.iy = None
        self.N = None
        self.applyIndexProjector = True
    def initPlot(self):
        self.plot = pyqtgraph.PlotWidget()
        line = pyqtgraph.InfiniteLine(0,90,None,True)
        self.plot.addItem(line)
        line.sigPositionChangeFinished.connect(self.emitViewIndexSelected)    
        self.line = line
        space = 60
        self.plot.getAxis("top").setHeight(space)
        self.plot.getAxis("bottom").setHeight(space)
        self.plot.getAxis("left").setWidth(space)
        self.plot.getAxis("right").setWidth(space)
    def loadData(self,dataset,plotMode,ix=None,iy=None,N=None):
        self.setData(dataset)
        self.ix = ix
        self.iy = iy
        self.N = N
        if N != None:
            self.applyIndexProjector = False
        else:
            self.applyIndexProjector = True
        self.datasetName = self.data.name
        if ix != None and iy != None:
            self.datasetName += (" (%i,%i)" % (ix,iy))
        self.setPlotMode(plotMode)
        self.refreshPlot()
    def setPlotMode(self,plotMode):
        self.plotMode = plotMode
        if plotMode == "plot":
            self.plot.setLabel("bottom","index")
            self.plot.setLabel("left",self.datasetName)
        elif plotMode == "histogram":
            self.plot.setLabel("bottom",self.datasetName)
            self.plot.setLabel("left","#")
        elif plotMode == "average":
            self.plot.setLabel("bottom","index")
            self.plot.setLabel("left",self.datasetName)           
    def refreshPlot(self):
        if self.ix != None and self.iy != None:
            data = self.getData(1,(self.ix,self.iy,self.N)) 
        else:
            data = self.getData(1) 
        if data != None:
            # that is not nice but works:
            if self.indexProjector.imgs != None and self.applyIndexProjector:
                if data.shape == self.indexProjector.imgs.shape:
                    data = data[self.indexProjector.imgs]
            if self.p == None:
                self.p = self.plot.plot(numpy.zeros(1), pen=(255,0,0))
                self.plot.enableAutoRange('xy')
            if self.plotMode == "plot":
                self.plot.enableAutoRange('xy')
                self.p.setData(data)
                # does not seem to work
                self.line.show()
                #self.refreshPlot() #tomas test
            elif self.plotMode == "histogram":
                (hist,edges) = numpy.histogram(data,bins=200)
                edges = (edges[:-1]+edges[1:])/2.0
                self.plot.enableAutoRange('xy')
                self.p.setData(edges,hist)        
                # does not seem to work
                self.line.hide()
                #self.refreshPlot() #tomas test
            elif self.plotMode == "average":
                self.plot.enableAutoRange('xy')
                self.p.setData(self.movingAverage(data,1000))
                self.line.hide()
                #self.refreshPlot() #tomas test
    def emitViewIndexSelected(self,foovalue=None):
        index = int(self.line.getXPos())
        self.viewIndexSelected.emit(index)
    def refreshDisplayProp(self,datasetProp):
        self.refreshPlot()
    def movingAverage(self,data, window_size):
        window= numpy.ones(int(window_size))/float(window_size)
        return numpy.convolve(data, window, 'same')
    
