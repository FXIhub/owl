from OpenGL.GL import *
from OpenGL.GLU import *
#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL
import numpy,h5py

class IndexProjector(QtCore.QObject):
    projectionChanged = QtCore.Signal(object)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.stackSize = None
        self.clear()
    def setProjector(self,sortingDataset,sortingInverted,filterMask):
        self.sortingDataset = sortingDataset
        self.sortingInverted = sortingInverted
        self.filterMask = filterMask
        self.update()
    def update(self):
        if self.stackSize != None:
            self.imgs = numpy.arange(self.stackSize,dtype="int")
            if self.sortingDataset != None:
                sortingDataset = -numpy.array(self.sortingDataset)
            else:
                sortingDataset = numpy.arange(self.stackSize,dtype="int")
            if self.filterMask != None:
                sortingDatasetFiltered = sortingDataset[self.filterMask]
                self.imgs = self.imgs[self.filterMask]
            else:
                sortingDatasetFiltered = sortingDataset
            if self.sortingInverted:
                self.imgs = self.imgs[numpy.argsort(sortingDatasetFiltered)[-1::-1]]
            else:
                self.imgs = self.imgs[numpy.argsort(sortingDatasetFiltered)]
            self.viewIndices = numpy.zeros(self.stackSize,dtype="int")
            self.viewIndices[self.imgs] = numpy.arange(len(self.imgs),dtype="int")
        else:
            self.viewIndices = None
            self.imgs = None
        self.projectionChanged.emit(self)
    def getNViewIndices(self):
        if self.imgs != None:
            return len(self.imgs)
        else:
            return 0
    # get the view index for a given img
    def imgToIndex(self,img):
        if self.viewIndices == None or img == None:
            return img
        else:
            if len(self.viewIndices) == 0:
                return 0
            elif int(img) >= len(self.viewIndices):
                return self.viewIndices[-1]
            else:
                return self.viewIndices[int(img)]
    # get the img for a given view index
    def indexToImg(self,index):
        if self.imgs == None or index == None:
            return index
        else:
            if int(index) >= len(self.imgs):
                return self.imgs[-1]
            else:
                return self.imgs[int(index)]
    def handleStackSizeChanged(self,stackSize):
        self.stackSize = stackSize
        self.update()
    def clear(self):
        self.stackSize = None
        self.filterMask = None
        self.sortingDataset = None
        self.sortingInverted = False
        self.viewIndices = None
        self.imgs = None
        self.projectionChanged.emit(self)

class View(QtCore.QObject):
    needDataset = QtCore.Signal(str)
    datasetChanged = QtCore.Signal(h5py.Dataset,str)
    indexProjector = IndexProjector()
    stackSizeChanged = QtCore.Signal(int)
    def __init__(self,parent=None,datasetMode="image"):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.datasetMode = datasetMode
        self.setData()
        self.setMask()
        #self.setSortingIndices()
        self.stackSizeChanged.connect(self.indexProjector.handleStackSizeChanged)
    def getStackSize(self):
        if self.data == None:
            return 0
        else:
            len(self.data)
    # DATA
    def setData(self,dataset=None):
        self.data = dataset
        if self.data != None:
            self.has_data = True
            if dataset.isCXIStack():
                self.stackSizeChanged.emit(dataset.getCXIStackSize())
        else:
            self.has_data = False
        self.datasetChanged.emit(dataset,self.datasetMode)
    def getData(self,nDims=2,index=0):
        if self.data == None:
            return None
        elif nDims == 1:
            if index != 0:
                (ix,iy,Nz) = index
                if Nz == 0:
                    return numpy.array(self.data[:,iy,ix])
                else:
                    iz = numpy.random.randint(0,len(self.data),Nz)
                    iz.sort()
                    data = numpy.zeros(Nz)
                    for i in range(Nz):
                        data[i] = self.data[iz[i],iy,ix]
                    #data[:] = self.data[iz,:,:]
                    return data
            else:
                return numpy.array(self.data).flatten()                
        elif nDims == 2:
            if self.data.isCXIStack():
                return self.data[index,:,:]
            else:
                return numpy.array(self.data[:,:])
    # MASK
    def setMask(self,maskDataset=None,maskOutBits=0):
        self.mask = maskDataset
        self.maskOutBits = maskOutBits
        self.datasetChanged.emit(maskDataset,"mask")
    def setMaskOutBits(self,maskOutBits=0):
        self.maskOutBits = maskOutBits
    def getMask(self,nDims=2,img_sorted=0):
        if self.mask == None:
            return None
        elif nDims == 2:
            if self.mask.isCXIStack():
                mask = self.mask[img_sorted,:,:]
            else:
                mask = self.mask[:,:]
            # do not apply maskBits, we'll do it in shader
#            return ((mask & self.maskOutBits) == 0)
            return mask
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('text/plain'):
            e.accept()
        else:
            e.ignore() 
    def dropEvent(self, e):
        self.needDataset.emit(e.mimeData().text())
