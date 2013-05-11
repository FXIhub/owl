from PySide import QtCore
import numpy
import logging

class ImageLoader(QtCore.QObject):
    imageLoaded = QtCore.Signal(int) 
    def __init__(self,parent = None,view = None):
        QtCore.QObject.__init__(self,parent)  
        self.view = view
        self._imageData = {}
        self.maskData = {}
    @QtCore.Slot(int,int)
    def loadImage(self,img):
        if(img in self.loadedImages()):
           return
        logging.debug("Loading image %d"  % (img))
        ################### Important Note ##################
        # The reason why everything gets stuck here is that #
        # h5py lock the GIL when doing things. To fix it we #
        # would need to move the loader to a different      #
        # process and this would prevent Carl's hack with   #
        # cheetah and the loader sharing the same hdf5 lib. #
        #####################################################
        data = self.view.getData(2,img)
        mask = self.view.getMask(2,img)
        self._imageData[img] = numpy.ones((self.view.data.getCXIHeight(),self.view.data.getCXIWidth()),dtype=numpy.float32)
        self._imageData[img] = data[:]
        if(mask != None):
            self.maskData[img] = numpy.ones((self.view.data.getCXIHeight(),self.view.data.getCXIWidth()),dtype=numpy.float32)
            self.maskData[img] = mask[:]
        else:
            self.maskData[img] = None
        self.imageLoaded.emit(img)
    def clear(self):
        self._imageData = {}
        self.maskData = {}
    def loadedImages(self):
        return self._imageData.keys()
    def getImage(self,img):
        return self._imageData[img]
