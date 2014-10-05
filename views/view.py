from PySide import QtGui, QtCore
import numpy
import h5py

class View(QtCore.QObject):
    needDataset = QtCore.Signal(str)
    datasetChanged = QtCore.Signal(h5py.Dataset,str)
    def __init__(self,parent=None,indexProjector=None,datasetMode="image"):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.indexProjector = indexProjector
        self.autoLast = False
        self.stackSize = 0
        self.datasetMode = datasetMode
	self.integrationMode = None

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

	
