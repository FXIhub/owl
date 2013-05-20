#from PyQt4 import QtGui, QtCore, QtOpenGL, Qt
from PySide import QtGui, QtCore, QtOpenGL
import h5py
from operator import mul
import numpy
import sys,os

# Add new functions to h5py.Dataset, names for functions are supposed to be unique in order to avoid conflicts
def isCXIStack(dataset):
    items = dataset.attrs.items()
    if len(items) > 0:
        cacheCXIStack = ("axes" == items[0][0])
    else:
        cacheCXIStack = False
    return cacheCXIStack      
h5py.Dataset.isCXIStack = isCXIStack 
def getCXIStackSize(dataset):
    if dataset.isCXIStack():
        return dataset.attrs.get("numEvents", [dataset.shape[0]])[0]
    else:
        None
h5py.Dataset.getCXIStackSize = getCXIStackSize 
def getCXIFormat(dataset):
    cacheCXIformat = len(dataset.shape)
    if dataset.isCXIStack() and cacheCXIformat == 3:
        cacheCXIformat = 2
    return cacheCXIformat

h5py.Dataset.getCXIFormat = getCXIFormat
def getCXIImageShape(dataset):
    if dataset.getCXIFormat() == 2:
        return (dataset.shape[-2],dataset.shape[-1])
    else:
        return None
h5py.Dataset.getCXIImageShape = getCXIImageShape
def isCXIText(dataset):
    return (str(dataset.dtype.name).find("string") != -1)
h5py.Dataset.isCXIText = isCXIText
def getCXIMasks(dataset):
    masks = {}
    suppMaskTypes = ["mask_shared","mask"]
    for maskType in suppMaskTypes:
        if maskType in dataset.parent.keys():
            masks[maskType] = dataset.parent[maskType]
    return masks
h5py.Dataset.getCXIMasks = getCXIMasks
def getCXIWidth(dataset):
    return dataset.shape[-1]
h5py.Dataset.getCXIWidth = getCXIWidth
def getCXIHeight(dataset):
    return dataset.shape[-2]
h5py.Dataset.getCXIHeight = getCXIHeight

class DatasetButton(QtGui.QPushButton):
    needDataset = QtCore.Signal(str)    
    def __init__(self,datasetBox,imageFile,datasetMode,menu=None):
        QtGui.QPushButton.__init__(self)
        self.datasetBox = datasetBox
        self.datasetMode = datasetMode
        self.setName()
        self.setIcon(QtGui.QIcon(imageFile))
        S = 30
        Htot = S + 15
        Wtot = 400
        self.setIconSize(QtCore.QSize(S,S))
        self.setToolTip("drag dataset here")
        self.setAcceptDrops(True)
        if menu != None:
            self.setMenu(menu)
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('text/plain'):
            e.accept()
        else:
            e.ignore() 
    def dropEvent(self, e):
        t = e.mimeData().text()
        self.needDataset.emit(t)
    def setName(self,name=None):
        if name == None:
            self.setStyleSheet("text-align: left; font-style: italic")
            self.setText("drag %s dataset here" % self.datasetMode)
        else:
            self.setStyleSheet("text-align: left; font-style: roman") 
            self.setText(name)

class DatasetBox(QtGui.QHBoxLayout):
    def __init__(self,imageFile,datasetMode,menu):
        QtGui.QHBoxLayout.__init__(self)
        self.menu = menu
        self.button = DatasetButton(self,imageFile,datasetMode,menu)
        self.addWidget(self.button)
        self.vbox = QtGui.QVBoxLayout()
        self.addLayout(self.vbox)
        if menu != None:
            self.menu.clearAction.triggered.connect(self.clear)
    def clear(self):
        self.button.setName()
        self.button.needDataset.emit(None)

class DatasetMenu(QtGui.QMenu):
    def __init__(self,parent=None):
        QtGui.QMenu.__init__(self,parent)
        self.clearAction = self.addAction("Clear")

class DatasetMaskMenu(DatasetMenu):
    def __init__(self,parent=None):
        DatasetMenu.__init__(self,parent)
        self.addSeparator()
        self.PIXELMASK_BITS = {'perfect' : 0,# PIXEL_IS_PERFECT
                               'invalid' : 1,# PIXEL_IS_INVALID
                               'saturated' : 2,# PIXEL_IS_SATURATED
                               'hot' : 4,# PIXEL_IS_HOT
                               'dead' : 8,# PIXEL_IS_DEAD
                               'shadowed' : 16, # PIXEL_IS_SHADOWED
                               'peakmask' : 32, # PIXEL_IS_IN_PEAKMASK
                               'ignore' : 64, # PIXEL_IS_TO_BE_IGNORED
                               'bad' : 128, # PIXEL_IS_BAD
                               'resolution' : 256, # PIXEL_IS_OUT_OF_RESOLUTION_LIMITS
                               'missing' : 512, # PIXEL_IS_MISSING
                               'halo' : 1024} # PIXEL_IS_IN_HALO
        self.maskActions = {}
        for key in self.PIXELMASK_BITS.keys():
            self.maskActions[key] = self.addAction(key)
            self.maskActions[key].setCheckable(True)
            self.maskActions[key].setChecked(True)
        self.maskActions["resolution"].setChecked(False)
    def getMaskOutBits(self):
        maskOutBits=0
        for key in self.maskActions:
            if self.maskActions[key].isChecked():
                maskOutBits |= self.PIXELMASK_BITS[key]
        return maskOutBits
        

class DatasetPlotMenu(DatasetMenu):
    def __init__(self,parent=None):
        DatasetMenu.__init__(self,parent)
        self.addSeparator()
        actionGroup = QtGui.QActionGroup(self)
        actionGroup.setExclusive(True)
        self.plotActions = {}
        keys = ["plot","average","histogram"]
        for key in keys:
            self.plotActions[key] = actionGroup.addAction(key)
            self.addAction(self.plotActions[key])
            self.plotActions[key].setCheckable(True)
        self.plotActions["plot"].setChecked(True)
    def getPlotMode(self):
        for key in self.plotActions.keys():
            if self.plotActions[key].isChecked():
                return key        


class CXINavigation(QtGui.QWidget):
    def __init__(self,parent=None):
        QtGui.QWidget.__init__(self,parent)
        self.parent = parent
        self.vbox = QtGui.QVBoxLayout()
        self.setLayout(self.vbox)

        self.datasetMenus = {}
        self.datasetBoxes = {}

        self.datasetMenus["image"] = DatasetMenu(self)
        self.basePath = os.path.dirname(os.path.realpath(__file__))
        self.datasetBoxes["image"] = DatasetBox(self.basePath + "/icons/image.png","image",self.datasetMenus["image"])
        self.vbox.addLayout(self.datasetBoxes["image"])

        self.datasetMenus["mask"] = DatasetMaskMenu(self)
        self.datasetBoxes["mask"] = DatasetBox(self.basePath + "/icons/mask_simple.png","mask",self.datasetMenus["mask"])
        self.vbox.addLayout(self.datasetBoxes["mask"])

        self.datasetMenus["sort"] = DatasetMenu(self)
        self.datasetBoxes["sort"] = DatasetBox(self.basePath + "/icons/sort.png","sort",self.datasetMenus["sort"])
        self.vbox.addLayout(self.datasetBoxes["sort"])

        self.datasetBoxes["filter0"] = DatasetBox(self.basePath + "/icons/filter.png","filter",None)
        self.vbox.addLayout(self.datasetBoxes["filter0"])

        self.vboxFilters = QtGui.QVBoxLayout()
        #self.vboxFilters.setDirection(QtGui.QBoxLayout.BottomToTop)
        self.vbox.addLayout(self.vboxFilters)
        self.datasetMenus["filters"] = []
        self.datasetBoxes["filters"] = []

        line = QtGui.QFrame()
        line.setFrameShape(QtGui.QFrame.HLine)
        self.vbox.addWidget(line)

        self.datasetMenus["plot"] = DatasetPlotMenu(self)
        self.datasetBoxes["plot"] = DatasetBox(self.basePath + "/icons/plot.png","plot",self.datasetMenus["plot"])
        self.vbox.addLayout(self.datasetBoxes["plot"])

        self.CXITree = CXITree(self)
        self.vbox.addWidget(self.CXITree)

    def addFilterBox(self):
        menu = DatasetMenu(self)
        self.datasetMenus["filters"].append(menu)
        box = DatasetBox(self.basePath + "/icons/filter.png","filter",menu)
        self.datasetBoxes["filters"].append(box)
        self.vboxFilters.addLayout(box)
        return box

    def removeFilterBox(self,filterBox):
        i = self.datasetBoxes["filters"].index(filterBox)
        self.datasetBoxes["filters"][i].removeWidget(self.datasetBoxes["filters"][i].button)
        self.datasetBoxes["filters"][i].button.setParent(None)
        self.datasetBoxes["filters"].pop(i)
        self.datasetMenus["filters"].pop(i)
        

class CXITree(QtGui.QTreeWidget):
    datasetClicked = QtCore.Signal(str)    
    def __init__(self,parent=None):        
        QtGui.QTreeWidget.__init__(self,parent)
        self.parent = parent
        self.itemExpanded.connect(self.treeChanged)
        self.itemCollapsed.connect(self.treeChanged)
        #self.setHeaderLabels(["CXI-file tree"])
        self.resizeColumnToContents(0)
        self.itemClicked.connect(self.handleClick)
        self.setDragEnabled(True)
        self.header().close()
    def treeChanged(self):
        self.manageSizes()
    def manageSizes(self):
        self.resizeColumnToContents(0)
    def buildTree(self,filename):
        self.clear();
        self.datasets = {}
        self.setColumnCount(1)
        self.f = h5py.File(filename, "r")
        self.root = QtGui.QTreeWidgetItem(["/"])
        self.addTopLevelItem(self.root)
        self.item = QtGui.QTreeWidgetItem([QtCore.QFileInfo(filename).fileName()])
        self.item.setToolTip(0,filename)
        self.root.setExpanded(True)
        self.root.addChild(self.item)
        self.buildBranch(self.f,self.item)
        self.loadData1()
    def buildBranch(self,group,item):
        self.columnPath = 1
        for g in group.keys():
            lst = [g]
            if(isinstance(group[g],h5py.Group)):
                child = QtGui.QTreeWidgetItem(lst)
                self.buildBranch(group[g],child)
                item.addChild(child)
            else:
                if(not group[g].shape):# or reduce(mul,group[g].shape) < 10):
                    lst.append(str(group[g][()]))
                    lst.append("")
                    child = QtGui.QTreeWidgetItem(lst)
                else:
                    dataset = self.datasets[group[g].name] = group[g]
                    ds_dtype = dataset.dtype.name
                    ds_shape = dataset.shape
                    string = "<i>"+ds_dtype+"</i> ("
                    for d in ds_shape:
                        string += str(d)+","
                    string = string[:-1]
                    string += ")"
                    lst.append(group[g].name)
                    child = QtGui.QTreeWidgetItem(lst)
                    child.setToolTip(self.columnPath-1,string)
                    numDims = dataset.getCXIFormat()
                    S = 50
                    # 1D blue
                    if numDims == 1:
                        R = 255-S
                        G = 255-S
                        B = 255
                        prop = "1D"
                    # 2D gree
                    elif numDims == 2:
                        R = 255-S
                        G = 255
                        B = 255-S 
                        prop = "2D"
                    # 3D red
                    elif numDims == 3:
                        R = 255
                        G = 255-S
                        B = 255-S
                        prop = "3D"
                    # default grey
                    else:
                        R = 255-S
                        G = 255-S
                        B = 255-S
                        prop = "default"
                    # datsets which are not stacks lighter
                    if not dataset.isCXIStack():
                        fade = S
                        R -= fade
                        G -= fade
                        B -= fade
                        prop += "Stack"
                    child.setForeground(0,QtGui.QBrush(QtGui.QColor(R,G,B)))
                    # make bold if it is a dataset called 'data'
                    if g.rsplit("/",1)[-1] == 'data':
                        font = QtGui.QFont()
                        font.setBold(True)
                        child.setFont(0,font)
                item.addChild(child)
    def loadData1(self):
        root = self.item
        root.setExpanded(True)
        path = ("entry_1","data_1","data")
        for section in path:
            found = False
            for i in range(0,root.childCount()):
                child = root.child(i)
                if(child.text(0) == section):
                    child.setExpanded(True)
                    root = child
                    found = True
                    break
            if(not found):
                break
        if(found):
            self.handleClick(root,1)
            return 1
        return 0
    def startDrag(self, event):
        # create mime data object
        mime = QtCore.QMimeData()
        mime.setText(self.currentItem().text(self.columnPath))
        # start drag 
        drag = QtGui.QDrag(self)
        drag.setMimeData(mime)
        drag.start(QtCore.Qt.MoveAction)
    def handleClick(self,item,column):
        if(item.text(self.columnPath) in self.datasets.keys()):
            self.datasetClicked.emit(item.text(self.columnPath))

