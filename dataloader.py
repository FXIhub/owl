from PySide import QtGui, QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl
import parameters
import patterson
from cxi import CXI

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
    def width(self):
        return self.shape()[-1]
    def height(self):
        return self.shape()[-2]
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
            d = (d & CXI.PIXEL_IS_IN_MASK) == 0

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
        params = self.view.data.pattersonItem.getParams(img)
        I = self.view.data.data(img=img)
        M = self.view.mask.data(img=img,binaryMask=True)
        self.pattersonData = patterson.patterson(I,M,params,normalize=True)
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
