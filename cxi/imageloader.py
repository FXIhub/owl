from PySide import QtGui, QtCore
import numpy
import logging
from cache import ArrayCache
import settingsOwl
import patterson


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
        self.imageData[img] = numpy.ones((self.view.data.length(),self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
        self.imageData[img][:] = data[:]
        if phase != None:
            self.phaseData[img] = numpy.ones((self.view.data.length(), self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
            self.phaseData[img][:] = phase[:]
        else:
            self.phaseData[img] = None
        if mask != None:
            self.maskData[img] = numpy.ones((self.view.data.length(), self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
            self.maskData[img][:] = mask[:]
        else:
            self.maskData[img] = None

        shape = (self.view.data.length(), min(self.imageData[img].shape[1], 8192), min(self.imageData[img].shape[2], 8192))
        if (shape[1] == 1):
            shape = (shape[0], shape[0])

        #self.imageData[img] = self.imageData[img][0:shape[0],0:shape[1]]
        self.imageData[img].resize(shape)
        #        print "Debug b min %f max %f %s %s" % (numpy.amin(self.imageData[img]), numpy.amax(self.imageData[img]), self.imageData[img].shape, self.imageData[img].dtype)
        #print "Emitting draw request %d " % (img)
        self.imageLoaded.emit(img)
    def loadGeometry(self,img):
        pass

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
        self.geometryData = ArrayCache(1024*1024*int(QtCore.QSettings().value("geometryCacheSize")))
        self.pattersonData = None
