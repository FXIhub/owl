from PySide import QtCore
import numpy


class IndexProjector(QtCore.QObject):
    projectionChanged = QtCore.Signal(object)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.stackSize = 0
        self.clear()
    def setProjector(self,sortingDataset,sortingInverted,filterMask):
        self.sortingDataset = sortingDataset
        self.sortingInverted = sortingInverted
        self.filterMask = filterMask
        self.update()
    def update(self):
        if self.stackSize != 0:
            self.imgs = numpy.arange(self.stackSize,dtype="int")
            if self.sortingDataItem != None:
                if self.sortingDataItem.shape()[0] == self.stackSize:
                    sortingDataItem = -numpy.array(self.sortingDataItem.data())
                else:
                    sortingDataItem = numpy.arange(self.stackSize,dtype="int")
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
        self.stackSize = 0
        self.filterMask = None
        self.sortingDataset = None
        self.sortingInverted = False
        self.viewIndices = None
        self.imgs = None
        self.projectionChanged.emit(self)

