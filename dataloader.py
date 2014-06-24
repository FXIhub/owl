from PySide import QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl

class FileLoader(QtCore.QObject):
    stackSizeChanged = QtCore.Signal(int)
    def __init__(self,parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
    def loadFile(self,fullFilename):
        self.f = h5py.File(fullFilename, "r")
        #self.f = h5py.File(fullFilename, "r*") # for swmr
        self.fullFilename = fullFilename
        self.filename = QtCore.QFileInfo(fullFilename).fileName()
        self.fullName = self.name = "/"
        self.H5Group = self.f["/"]
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self,"/"+k)
        self.dataItems = {}
        self.collectDataItems(self.children)
        self.stackSize = None
    def collectDataItems(self,item):
        for k in item.keys():
            child = item[k]
            if isinstance(child,DataItem):
                self.dataItems[child.fullName] = child
            elif isinstance(child,GroupItem):
                self.collectDataItems(child.children)
            else:
                print "no valid item."
    def updateStackSize(self):
        N = []
        for n,d in self.dataItems.items():
            if d.isSelectedStack:
                #try:
                #print "About to refresh dataset:"
                #print dataItem.H5Dataset.dtype.name
                #print d.fullName,d.H5Dataset,d.H5Dataset.attrs.get("numEvents"),d.H5Dataset.id.id
                #self.f[n].refresh()
                #print "Dataset refreshed:"
                #print d.fullName,d.H5Dataset,d.H5Dataset.attrs.get("numEvents")
                #except:
                #    self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")
                N.append(self.f[n].attrs.get("numEvents", self.f[n].shape)[0])
        if len(N) > 0:
            N = numpy.array(N).min()
        else:
            N = None
        if N != self.stackSize:
            self.stackSize = N
            self.stackSizeChanged.emit(N)


class GroupItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.H5Group = parent.H5Group[self.name]
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fileLoader,self.fullName+"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fileLoader,self.fullName+"/"+k)

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
        if len(self.fileLoader.f[self.fullName].attrs.items()) > 0:
            self.isStack = ("axes" in self.fileLoader.f[self.fullName].attrs.items()[0])
        #self.isStack = (len(list(self.H5Dataset.shape)) == 3)
        else:
            self.isStack = False
        # check whether or not it is text
        self.isText = (str(self.fileLoader.f[self.fullName].dtype.name).find("string") != -1)
        # presentable as values
        self.isPresentable = (self.isText == False)
        # shape?
        self.format = len(self.shape())
        # complex?
        self.isComplex = (str(self.fileLoader.f[self.fullName].dtype.name).lower().find("complex") != -1)
        # image stack?
        if self.isStack: self.format -= 1
    def shape(self,forceRefresh=False):
        shape = self.fileLoader.f[self.fullName].shape
        if self.isSelectedStack and self.fileLoader.stackSize != None:
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
    def data(self,**kwargs):
        # COMMENT: Refreshing datasets can have the side effect that they are being closed. Why is that?
        #try:
        #self.fileLoader.f[self.fullName].refresh()
        #except:
        #    self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")
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
                d = numpy.array(self.fileLoader.f[self.fullName][img])
            elif N != None:
                if self.isSelectedStack and self.fileLoader.stackSize != None:
                    if self.fileloader.stackSize == None:
                        d = self.fileLoader.f[self.fullName]
                    else:
                        d = self.fileLoader.f[self.fullName][:self.fileLoader.stackSize]
                else:
                    d = self.fileLoader.f[self.fullName]
                if filterMask != None:
                    d = d[filterMask]
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
                    d = numpy.array(self.fileLoader.f[self.fullName]).flatten()

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
            if self.fileLoader.stackSize == None:
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