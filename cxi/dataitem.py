from PySide import QtGui, QtCore
import numpy,cmath
import logging
import settingsOwl
from cxi import CXI

class DataItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        #self.H5Dataset = parent.H5Group[self.name]
        self.dtypeName = self.fileLoader.f[self.fullName].dtype.name
        self.dtypeItemsize = self.fileLoader.f[self.fullName].dtype.itemsize
        self.logger = logging.getLogger("DataItem")
        self.logger.setLevel(settingsOwl.loglev["DataItem"])
        self.isSelectedStack = False

        # check whether or not it is a stack
        if len(self.fileLoader.f[self.fullName].attrs.items()) > 0 and "axes" in self.fileLoader.f[self.fullName].attrs.keys():
            axes_attrs = self.fileLoader.f[self.fullName].attrs.get("axes")[0].split(":")
            self.isStack = True
            self.stackDim = axes_attrs.index("experiment_identifier")
            # check wheter or not a stack has modules
            if "module_identifier" in axes_attrs:
                self.stackHasModules = True
                self.moduleDim = axes_attrs.index("module_identifier")
            else:
                self.stackHasModules = False
                self.moduleDim = None
        else:
            self.isStack = False
            self.stackDim = None

        # check whether or not it is text
        self.isText = (str(self.fileLoader.f[self.fullName].dtype.name).find("string") != -1)

        # presentable as values
        self.isPresentable = (self.isText == False)

        # shape?
        self.format = len(self.shape())

        # image stack?
        if self.isStack: 
            self.format -= 1
            if self.stackHasModules:
                self.format -= 1

        # complex?
        self.isComplex = (str(self.fileLoader.f[self.fullName].dtype.name).lower().find("complex") != -1)

        # link tags
        self.tagsItem = self.parent.tagsItem

        # link model parameters
        self.modelItem = self.parent.modelItem

        # link patterson parameters
        self.pattersonItem = self.parent.pattersonItem

        # Selected dimension for filetering etc. where stack has to have only one dimension
        # Set to none by default
        self.selectedIndex = None

    def shape(self,forceRefresh=False):
        #print self.fullName
        #print self.fileLoader.f[self.fullName]
        shape = self.fileLoader.f[self.fullName].shape
        if self.isSelectedStack and self.fileLoader.stackSize != None:
        # MFH: Isnn't the following line be more logical than what we have currently?
        #if self.isStack and self.fileLoader.stackSize != None:
            shape = list(shape)
            shape.pop(0)
            shape.insert(0,self.fileLoader.stackSize)
            if not self.stackHasModules and self.format == 2:
                shape.insert(1,1)
            #self._shape.insert(0,self.H5Dataset.attrs.get("numEvents", (self.H5Dataset.shape))[0])
            shape = tuple(shape)
        return shape
    def width(self):
        return self.shape()[-1]
    def height(self):
        return self.shape()[-2]
    def length(self):
        return self.shape()[-3]
    def deselectStack(self):
        if self.isSelectedStack:
            self.isSelectedStack = False
            self.fileLoader.updateStackSize()
        else:
            self.isSelectedStack = False
    def selectStack(self):
        if self.isStack:
            self.isSelectedStack = True
            self.fileLoader.updateStackSize()
    def attr(self,name):
        return self.fileLoader.f[self.fullName].attrs[name]
        
    def data(self,**kwargs):
        complex_mode = kwargs.get("complex_mode",None)
        if self.isComplex == False and complex_mode != None:
            return None
        img = kwargs.get("img",None)
        if self.isStack and self.format == 2:
            d = numpy.array(self.fileLoader.f[self.fullName][img])
        elif self.isStack and self.format == 1:
            if img != None:
                d = numpy.array(self.fileLoader.f[self.fullName])[img][:]
            elif self.fileLoader.stackSize == None:
                d = numpy.array(self.fileLoader.f[self.fullName])[:,:]
            else:
                d = numpy.array(self.fileLoader.f[self.fullName])[:self.fileLoader.stackSize,:]

        elif self.isStack and self.format == 0:
            if self.fileLoader.stackSize == None:
                d = numpy.array(self.fileLoader.f[self.fullName])
            else:
                d = numpy.array(self.fileLoader.f[self.fullName])[:self.fileLoader.stackSize]

        else:
            d = numpy.array(self.fileLoader.f[self.fullName])
        if kwargs.get("binaryMask",False):
            d = (d & CXI.PIXEL_IS_IN_MASK) == 0

        windowSize = kwargs.get("windowSize",None)
        if windowSize != None:
            # Running average by convolution with an exponentially decaying weight kernel in respect to time.
            # d12: decay half-time
            # The total window size is two times d12, defining the absolute length of the memory.
            d12 = int(windowSize/2.)
            x = numpy.arange(2*d12-1,-1,-1)
            tmp = numpy.exp(x**2/d12**2*numpy.log(2))
            w = tmp/tmp.sum()
            N = len(d)
            d = numpy.convolve(d, w, 'full')[:N]

        if self.isComplex:
            if complex_mode == "phase":
                d = numpy.angle(d)
            elif complex_mode == "real":
                d = d.real
            elif complex_mode == "imag":
                d = d.imag
            else:
                # default is the absolute value / amplitude
                d = abs(d)

        return d
    def data1D(self,**kwargs):
        if len(self.shape()) == 2:
            if self.stackDim == 0:
                return self.data(**kwargs)[:,self.selectedIndex]
            else:
                return self.data(**kwargs)[self.selectedIndex,:]
        elif len(self.shape()) == 3:
            img = kwargs.get("img",0)
            return self.data(**kwargs)[self.selectedIndex,:]
        else:
            return self.data(**kwargs)
