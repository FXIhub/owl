from PySide import QtGui, QtCore
import numpy
import h5py
from indexprojector import IndexProjector

class View(QtCore.QObject):
    needDataset = QtCore.Signal(str)
    datasetChanged = QtCore.Signal(h5py.Dataset,str)
    indexProjector = IndexProjector()
    stackSizeChanged = QtCore.Signal(int)
    def __init__(self,parent=None,datasetMode="image"):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.autoLast = False
        self.stackSize = 0
        self.datasetMode = datasetMode
	self.integrationMode = None
        self.setData()
        self.setMask()
        #self.setSortingIndices()
        self.stackSizeChanged.connect(self.indexProjector.handleStackSizeChanged)
    def getStackSize(self):
        return self.stackSize
        #if self.data == None:
        #    return 0
        #else:
        #    len(self.data)
    def toggleAutoLast(self):
        self.autoLast = not self.autoLast
    # DATA
    def updateStackSize(self, emitChanged=True):
        oldSize = self.stackSize
        if self.data != None:
            self.has_data = True        
            if self.data.isCXIStack():
		self.stackSize = self.data.getCXIStackSize()
            else:
                if "numEvents" in self.data.attrs.keys():
                    self.stackSize = self.data.attrs.get("numEvents")[0]
                elif len(self.data.shape) == 3:
                    self.stackSize = self.data.shape[2]
                else:
                    self.stackSize = 1
        else:
            self.stackSize = 0
            self.has_data = False
        if emitChanged == True and self.stackSize != oldSize:# and (self.data == None or self.data.isCXIStack()):
            print "Stack size %i" % self.stackSize
            self.stackSizeChanged.emit(self.stackSize)
    def setData(self,dataset=None):
        self.data = dataset        
        self.updateStackSize(True)
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
		if "numEvents" in self.data.attrs.keys():
		    return numpy.array(self.data).flatten()[:self.data.attrs["numEvents"]]
        elif nDims == 2:
	    if self.data.isCXIStack():
		if self.integrationMode == None:
		    return self.data[index,:,:]
		else:
		    if self.indexProjector.filterMask == None:
			d = self.data
		    else:
			d = self.data[self.indexProjector.filterMask,:,:]
		    if self.integrationMode == "mean":
			return numpy.mean(d,0)
		    elif self.integrationMode == "std":
			return numpy.std(d,0)
		    elif self.integrationMode == "min":
			return numpy.min(d,0)
		    elif self.integrationMode == "max":
			return numpy.max(d,0)
	    else:
                return self.data[:,:]
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
		if self.integrationMode == None:
		    mask = self.mask[img_sorted,:,:]
		else:
		    mask = numpy.zeros(shape=(self.data.shape[1],self.data.shape[2]))
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

    def clearView(self):
	self.stackSize = 0
	self.integrationMode = None
        self.setData()
        self.setMask()
	
