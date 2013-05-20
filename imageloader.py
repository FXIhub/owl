from PySide import QtCore
import numpy
import logging
from cache import ArrayCache

class ImageLoader(QtCore.QObject):
    imageLoaded = QtCore.Signal(int) 
    def __init__(self,parent = None,view = None):
        QtCore.QObject.__init__(self,parent)  
        self.view = view
        self.clear()
        self.logger = logging.getLogger("ImageLoader")
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)

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
        data = self.view.getData(2,img)
        mask = self.view.getMask(2,img)
        self.imageData[img] = numpy.ones((self.view.data.getCXIHeight(),self.view.data.getCXIWidth()),dtype=numpy.float32)
        self.imageData[img][:] = data[:]
        if(mask != None):
            self.maskData[img] = numpy.ones((self.view.data.getCXIHeight(),self.view.data.getCXIWidth()),dtype=numpy.float32)
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
        self.maskData = ArrayCache(1024*1024*int(QtCore.QSettings().value("maskCacheSize")))
    def loadedImages(self):
        return self.imageData.keys()
        
