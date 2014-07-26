from PySide import QtGui, QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl
import parameters
import patterson

class FileLoader(QtCore.QObject):
    stackSizeChanged = QtCore.Signal(int)
    fileLoaderExtended = QtCore.Signal()
    def __init__(self,parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.f = None
        self.stackSize = None
        self.mode = parent.settings.value("fileMode")
    def openFile(self,fullFilename,mode0=None):
        if mode0 != None:
            self.mode = mode0
        mode = self.mode
        if mode == "r*" and not settingsOwl.swmrSupported:
            return 1
        if isinstance(self.f,h5py.File):
            self.f.close()
        try:
            self.f = h5py.File(fullFilename,mode)#,libver='latest')
            return 0
        except IOError as e:            
            if( str(e) == 'Unable to open file (File is already open for write or swmr write)'):                                
                print "\n\n!!! TIP: Trying running h5clearsb.py on the file !!!\n\n"
            raise
            return 2
        print self.f
    def reopenFile(self):
        # IMPORTANT NOTE:
        # Reopening the file is required after groups (/ datasets?) are created, otherwise we corrupt the file.
        # As we have to do this from time to time never rely on direct pointers to HDF5 datatsets. You better access data only via the HDF5 file object fileLoader.f[datasetname].
        if self.mode == "r*":
            self.parent.updateTimer.start()
        elif self.mode == "r+":
            self.parent.updateTimer.stop()
        return self.openFile(self.fullFilename,self.mode)
    def loadFile(self,fullFilename):
        self.f = None
        err =  self.openFile(fullFilename,"r*")
        if err == 1:
            print "Cannot open file. SWMR mode not supported by your h5py version. Please change file mode in the file menue and try again."
            return
        self.fullFilename = fullFilename
        self.filename = QtCore.QFileInfo(fullFilename).fileName()
        self.fullName = self.name = "/"
        self.tagsItem = None
        self.modelItem = None
        self.pattersonItem = None
        self.dataItems = {}
        self.groupItems = {}
        self.tagsItems = {}
        self.modelItems = {}
        self.pattersonItems = {}
        self.children = {}
        H5Group = self.f[self.fullName]
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self,"/"+k)
        self.collectItems(self.children)
        self.stackSize = None
    def collectItems(self,item):
        for k in item.keys():
            child = item[k]
            if isinstance(child,DataItem):
                self.dataItems[child.fullName] = child
            elif isinstance(child,GroupItem):
                self.groupItems[child.fullName] = child
                self.tagsItems[child.fullName] = child.tagsItem
                self.modelItems[child.fullName] = child.modelItem
                self.pattersonItems[child.fullName] = child.pattersonItem
                self.collectItems(child.children)
            else:
                print "no valid item."
    def addGroupPosterior(self,name0):
        name = name0
        if name[-1] == "/": name = name[:-1]
        path = name[0:name.rindex('/')]

        def addGroupRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    g = GroupItem(c,self,name)
                    c.children[name[name.rindex('/')+1:]] = g
                    self.groupItems[name] = g
                    self.modelItems[name] = g.modelItem
                    self.pattersonItems[name] = g.pattersonItem
                    #print "add group",self.groupItems.keys(),name0
                elif isinstance(c,GroupItem):                  
                    addGroupRecursively(c,c.children)

        addGroupRecursively(self,self.children)
    def addDatasetPosterior(self,name0):
        name = name0
        path = name[0:name.rindex('/')]

        def addDatasetRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    d = DataItem(group,self,"/"+name)
                    c.children[name[name.rindex('/')+1:]] = d
                    self.dataItems[name] = d
                elif isinstance(c,GroupItem):                  
                    addDatasetRecursively(c,c.children)

        addDatasetRecursively(self,self.children)
    def updateStackSize(self):
        if self.f == None:
            return
        N = []
        for n,d in self.dataItems.items():
            if d.isSelectedStack:
                if "numEvents" in self.f[n].attrs.keys():
                    if not self.f.mode == "r+": # self.f.mode == None if opened in swmr mode. This is odd.
                        self.f[n].refresh()
                    N.append(self.f[n].attrs.get("numEvents")[0])
                    #print n,N
                else:
                    N.append(self.f[n].shape[d.stackDim])
        if len(N) > 0:
            N = numpy.array(N).min()
        else:
            N = None
        if N != self.stackSize:
            self.stackSize = N
            self.stackSizeChanged.emit(N)
    def ensureReadWriteModeActivated(self):
        if self.f.mode != "r+":
            accepted = QtGui.QMessageBox.question(self.parent,"Change to read-write mode?",
                                                  "The file is currently opened in SWMR mode. Data can not be written to file in this mode. Do you like to reopen the file in read-write mode?",
                                                  QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok
            if accepted:
                self.mode = "r+"
                self.reopenFile()
                return 0
        return 1
    def saveTags(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,t in self.tagsItems.items():
                t.saveTags()
    def modelsChanged(self):
        if self.f == None:
            return
        for n,m in self.modelItems.items():
            if m.paramsDirty:
                return True
        return False
    def pattersonsChanged(self):
        if self.f == None:
            return
        for n,p in self.pattersonItems.items():
            if p.paramsDirty:
                return True
        return False
    def saveModels(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,m in self.modelItems.items():
                m.saveParams()
    def savePattersons(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,m in self.pattersonItems.items():
                m.saveParams()

class GroupItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.tagsItem = parameters.TagsItem(self,fileLoader,fullName+"/")
        self.children = {}
        H5Group = self.fileLoader.f[self.fullName]
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fileLoader,self.fullName+"/"+k)
        self.modelItem = parameters.ModelItem(self,self.fileLoader)
        self.pattersonItem = parameters.PattersonItem(self,self.fileLoader)
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fileLoader,self.fullName+"/"+k)

# CXI pixelmask bits
PIXEL_IS_PERFECT = 0
PIXEL_IS_INVALID = 1
PIXEL_IS_SATURATED = 2
PIXEL_IS_HOT = 4
PIXEL_IS_DEAD = 8
PIXEL_IS_SHADOWED = 16
PIXEL_IS_IN_PEAKMASK = 32
PIXEL_IS_TO_BE_IGNORED = 64
PIXEL_IS_BAD = 128
PIXEL_IS_OUT_OF_RESOLUTION_LIMITS = 256
PIXEL_IS_MISSING = 512
PIXEL_IS_IN_HALO = 1024
PIXEL_IS_ARTIFACT_CORRECTED = 2048
PIXEL_IS_IN_MASK = PIXEL_IS_INVALID |  PIXEL_IS_SATURATED | PIXEL_IS_HOT | PIXEL_IS_DEAD | PIXEL_IS_SHADOWED | PIXEL_IS_IN_PEAKMASK | PIXEL_IS_TO_BE_IGNORED | PIXEL_IS_BAD | PIXEL_IS_MISSING

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
            self.isStack = True
            self.stackDim = self.fileLoader.f[self.fullName].attrs.get("axes")[0].split(":").index("experiment_identifier")
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
        if self.isStack: self.format -= 1
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
            #self._shape.insert(0,self.H5Dataset.attrs.get("numEvents", (self.H5Dataset.shape))[0])
            shape = tuple(shape)
        return shape
    def width(self,forceRefresh=False):
        return self.shape(forceRefresh)[-1]
    def height(self,forceRefresh=False):
        return self.shape(forceRefresh)[-2]
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
            d = (d & PIXEL_IS_IN_MASK) == 0

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


class ImageLoader(QtCore.QObject):
    imageLoaded = QtCore.Signal(int)
    def __init__(self,parent = None,view = None):
        QtCore.QObject.__init__(self,parent)
        self.view = view
        self.clear()
        self.logger = logging.getLogger("ImageLoader")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["ImageLoader"])

    @QtCore.Slot(int)
    def loadImage(self,img):
        if(img in self.loadedImages()):
            # this might seem dangerous but it's not
            # as there is always only 1 thread running
            # loadImage
            self.imageLoaded.emit(img)
            return
        if self.view.data == None:
            return
        self.logger.debug("Loading image %d"  % (img))
        ################### Important Note ##################
        # The reason why everything gets stuck here is that #
        # h5py lock the GIL when doing things. To fix it we #
        # would need to move the loader to a different      #
        # process and this would prevent Carl's hack with   #
        # cheetah and the loader sharing the same hdf5 lib. #
        #####################################################
        data = self.view.getData(img)
        phase = self.view.getPhase(img)
        mask = self.view.getMask(img)
        self.imageData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
        self.imageData[img][:] = data[:]
        if phase != None:
            self.phaseData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
            self.phaseData[img][:] = phase[:]
        else:
            self.phaseData[img] = None
        if mask != None:
            self.maskData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
            self.maskData[img] = mask[:]
        else:
            self.maskData[img] = None

        shape = (min(self.imageData[img].shape[0], 8192), min(self.imageData[img].shape[1], 8192))
        if (shape[1] == 1):
            shape = (shape[0], shape[0])

        #self.imageData[img] = self.imageData[img][0:shape[0],0:shape[1]]
        self.imageData[img].resize(shape)
        #        print "Debug b min %f max %f %s %s" % (numpy.amin(self.imageData[img]), numpy.amax(self.imageData[img]), self.imageData[img].shape, self.imageData[img].dtype)
        #print "Emitting draw request %d " % (img)
        self.imageLoaded.emit(img)
    def loadPatterson(self,img):
        data = self.view.data
        mask = self.view.mask
        PC = patterson.PattersonCreator(data,mask)
        self.pattersonData = abs(PC.patterson(img))
        self.imageLoaded.emit(img)
    def loadedImages(self):
        return self.imageData.keys()
    def loadedPatterson(self):
        return self.pattersonData.keys()
    def clear(self):
        # Unlimited cache
        self.imageData = ArrayCache(1024*1024*int(QtCore.QSettings().value("imageCacheSize")))
        self.phaseData = ArrayCache(1024*1024*int(QtCore.QSettings().value("phaseCacheSize")))
        self.maskData = ArrayCache(1024*1024*int(QtCore.QSettings().value("maskCacheSize")))
        self.pattersonData = None
