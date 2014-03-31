from PySide import QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl

class FileLoader:
    def __init__(self,fullFilename):
        #self.f = h5py.File(fullFilename, "r")
        self.f = h5py.File(fullFilename, "r*") # for swmr
        self.fullFilename = fullFilename
        self.filename = QtCore.QFileInfo(fullFilename).fileName()
        self.fullName = self.name = "/"
        self.H5Group = self.f["/"]
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,"/"+k)
        self.dataItems = {}
        self.collectDataItems(self.children)
        self.stack = Stack(self.f)
    def collectDataItems(self,item):
        for k in item.keys():
            child = item[k]
            if isinstance(child,DataItem):
                self.dataItems[child.fullName] = child
            elif isinstance(child,GroupItem):
                self.collectDataItems(child.children)
            else:
                print "no valid item."

class Stack:
    stackSizeChanged = QtCore.Signal(int)
    def __init__(self,f):
        self.f = f
        self.H5Datasets = {} # full name : dataset
        self.stackSize = None
    def addDataset(self,fullName):
        self.H5Datasets[fullName] = self.f[fullName]
    def removeDataset(self,fullName):
        del self.H5Datasets[fullName]
    def updateStackSize(self):
        if not self.H5Datasets == {}:
            N = []
            for n,ds in self.H5Datasets.items():
                try:
                    ds.refresh()
                except:
                    self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")
                N.append(ds.shape[0])
            N = numpy.array(N).min()
        else:
            N = None
        if N != self.stackSize:
            self.stackSizeChanged.emit(N)
        self.stackSize = N

class GroupItem:
    def __init__(self,parent,fullName):
        self.parent = parent
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.H5Group = parent.H5Group[self.name]
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fullName+"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fullName+"/"+k)

class DataItem:
    def __init__(self,parent,fullName):
        self.parent = parent
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.H5Dataset = parent.H5Group[self.name]
        self.dtypeName = self.H5Dataset.dtype.name
        self.dtypeItemsize = self.H5Dataset.dtype.itemsize
        self._shape = None
        self.logger = logging.getLogger("DataItem")
        self.logger.setLevel(settingsOwl.loglev["DataItem"])
        # check whether or not it is a stack
        if len(self.H5Dataset.attrs.items()) > 0:
            self.isStack = ("axes" in self.H5Dataset.attrs.items()[0])
        #self.isStack = (len(list(self.H5Dataset.shape)) == 3)
        else:
            self.isStack = False
        # check whether or not it is text
        self.isText = (str(self.H5Dataset.dtype.name).find("string") != -1)
        # shape?
        self.format = len(self.shape())
        # complex?
        self.isComplex = (str(self.H5Dataset.dtype.name).lower().find("complex") != -1)
        # image stack?
        if self.isStack: self.format -= 1
    def shape(self,forceRefresh=False):
        if self._shape == None or forceRefresh:
            try:
                self.H5Dataset.refresh()
            except:
                self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")
            self._shape = self.H5Dataset.shape
            if self.isStack:
                self._shape = list(self._shape)
                self._shape.pop(0)
                self._shape.insert(0,self.H5Dataset.attrs.get("numEvents", (self.H5Dataset.shape))[0])
                self._shape = tuple(self._shape)
        return self._shape
    def width(self,forceRefresh=False):
        return self.shape(forceRefresh)[-1]
    def height(self,forceRefresh=False):
        return self.shape(forceRefresh)[-2]
    def data(self,**kwargs):
        try:
            self.H5Dataset.refresh()
        except:
            self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")
        complex_mode = kwargs.get("complex_mode",None)
        if self.isComplex == False and complex_mode != None:
            return None
        if self.isStack and self.format == 2:
            img = kwargs.get("img",None)
            filterMask = kwargs.get("filterMask",None)
            N = kwargs.get("N",None)
            integrationMode = kwargs.get("integrationMode",None)
            pickMode = kwargs.get("pickMode","random")
            if img != None:
                d = numpy.array(self.H5Dataset[img])
            elif N != None:
                if filterMask != None:
                    d = self.H5Dataset[filterMask]
                else:
                    d = self.H5Dataset
                if pickMode == None or N >= d.shape[0]:
                    d = numpy.array(d[:N])
                elif pickMode == "random":
                    iz = numpy.random.randint(0,d.shape[0],N)
                    iz.sort()
                    temp = numpy.zeros(shape=(N,d.shape[1],d.shape[2]))
                    # for some reason the following line causes hdf5 errors if the dataset is getting very large
                    #d[:] = d[iz,:,:]
                    for i in range(self.imageStackN):
                        temp[i,:,:] = d[iz[i]]
                    d = temp
            else:
                s = numpy.array(list(self.shape(True)))
                k = 1
                for si in s: k *= si                
                if k > 100000000:
                    self.logger.warning("You do not really want to load a dataset of the length of %i into memory." % k)
                    d = numpy.zeros(1)
                else:
                    d = numpy.array(self.H5Dataset).flatten()

            if integrationMode != None:
                if integrationMode == "mean":
                    d = numpy.mean(d,0)
                elif integrationMode == "std":
                    d = numpy.std(d,0)
                elif integrationMode == "min":
                    d = numpy.min(d,0)
                elif integrationMode == "max":
                    d = numpy.max(d,0)
        elif self.isStack and self.format == 1:
            d = numpy.array(self.H5Dataset)[:self.shape(True)[0],:]
        elif self.isStack and self.format == 0:
            d = numpy.array(self.H5Dataset)[:self.shape(True)[0]]
        else:
            d = numpy.array(self.H5Dataset)
        ix = kwargs.get("ix",None)
        iy = kwargs.get("iy",None)
        if ix != None and iy != None:
            if len(d.shape) == 3:
                d = d[:,iy,ix]
            else:
                d = d[iy,ix]
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
                # default is the absolute value
                d = abs(d)
        return d

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
    def clear(self):
        # Unlimited cache
        self.imageData = ArrayCache(1024*1024*int(QtCore.QSettings().value("imageCacheSize")))
        self.phaseData = ArrayCache(1024*1024*int(QtCore.QSettings().value("phaseCacheSize")))
        self.maskData = ArrayCache(1024*1024*int(QtCore.QSettings().value("maskCacheSize")))
    def loadedImages(self):
        return self.imageData.keys()

