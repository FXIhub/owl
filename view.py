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
    #def setData(self,dataset=None):
    #    self.data = dataset        
    #    self.updateStackSize(True)
    #    self.datasetChanged.emit(dataset,self.datasetMode)
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

	
