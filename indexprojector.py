from PySide import QtCore
import numpy,logging
import settingsOwl

class IndexProjector(QtCore.QObject):
    projectionChanged = QtCore.Signal(object)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.stackSize = 0
        self.clear()
        self.logger = logging.getLogger("IndexProjector")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["IndexProjector"])
    def setProjector(self,sortingDataItem,sortingInverted,filterMask):
        self.sortingDataItem = sortingDataItem
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
                    self.logger.debug("The data for sorting does not match the size of the stack.")
                    sortingDataItem = numpy.arange(self.stackSize,dtype="int")
            else:
                sortingDataItem = numpy.arange(self.stackSize,dtype="int")
            if self.filterMask != None:
                sortingDataItemFiltered = sortingDataItem[self.filterMask]
                self.imgs = self.imgs[self.filterMask]
            else:
                sortingDataItemFiltered = sortingDataItem
            if self.sortingInverted:
                self.imgs = self.imgs[numpy.argsort(sortingDataItemFiltered)[-1::-1]]
            else:
                self.imgs = self.imgs[numpy.argsort(sortingDataItemFiltered)]
            self.viewIndices = numpy.zeros(self.stackSize,dtype="int")
            self.viewIndices[self.imgs] = numpy.arange(len(self.imgs),dtype="int")
        else:
            self.viewIndices = None
            self.imgs = None
        self.projectionChanged.emit(self)
    def onStackSizeChanged(self,newStackSize):
        if self.sortingDataItem != None:
            if newStackSize != self.stackSize:
                self.stackSize = newStackSize
                self.update()
        else:
            self.stackSize = 0
            self.update()
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
    def clear(self):
        self.stackSize = 0
        self.filterMask = None
        self.sortingDataItem = None
        self.sortingInverted = False
        self.viewIndices = None
        self.imgs = None
        self.projectionChanged.emit(self)

