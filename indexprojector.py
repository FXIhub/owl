from PySide import QtCore
import numpy,logging
import settingsOwl

class IndexProjector(QtCore.QObject):
    projectionChanged = QtCore.Signal(object)
    def __init__(self):
        QtCore.QObject.__init__(self)
        self.stackSize = 0
        self.logger = logging.getLogger("IndexProjector")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["IndexProjector"])
        self.filters = []
        self._filterMask = None
        self.vmins = None
        self.vmaxs = None
        self.clear()
    def setProjector(self,sortingDataItem,sortingInverted):
        self.sortingDataItem = sortingDataItem
        self.sortingInverted = sortingInverted
        self.update()
    def addFilter(self,dataItem):
        self.filters.append(dataItem)
    def removeFilter(self,index):
        self.filters.pop(index)
    def updateFilterMask(self,vmins=None,vmaxs=None):
        if vmins == None or vmaxs == None:
            self._filterMask = None
        else:
            if len(self.filters) > 0:
                F = numpy.ones(shape=(len(self.filters),self.stackSize),dtype="bool")
                for i,f in zip(range(len(self.filters)),self.filters):
                    F[i,:] = f.data()[:self.stackSize]
                for i,filterDataItem,vmin,vmax in zip(range(len(self.filters)),self.filters,vmins,vmaxs):
                    filt = filterDataItem.data()
                    F[i,:] = (filt[:] <= vmax) * (filt[:] >= vmin)
                if len(self.filters) > 1:
                    self._filterMask = numpy.array(F.prod(0),dtype="bool").flatten()
                else:
                    self._filterMask = F.flatten()
            else:
                self._filterMask = None
        self.vmins = vmins
        self.vmaxs = vmaxs
    def filterMask(self):
        if self._filterMask == None:
            return numpy.ones(self.stackSize,dtype="bool")
        else:
            return self._filterMask
    def update(self):
        self.updateFilterMask(self.vmins,self.vmaxs)
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
            if self._filterMask != None:
                M = self.filterMask()
                sortingDataItemFiltered = sortingDataItem[M]
                self.imgs = self.imgs[M]
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
        self.stackSize = newStackSize
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
        self._filterMask = None
        self.sortingDataItem = None
        self.sortingInverted = False
        self.viewIndices = None
        self.imgs = None
        self.projectionChanged.emit(self)

