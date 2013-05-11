from PySide import QtCore
import numpy

class ImageLoader(QtCore.QObject):
    imageLoaded = QtCore.Signal(int) 
    def __init__(self,parent = None,view = None):
        QtCore.QObject.__init__(self,parent)  
        self.view = view
        self.loaded = {}
        self.imageData = {}
        self.maskData = {}
    @QtCore.Slot(int,int)
    def loadImage(self,img):
        if(img in self.loaded):
           return
        self.loaded[img] = True
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
        self.imageData[img] = data[:]
        if(mask != None):
            self.maskData[img] = numpy.ones((self.view.data.getCXIHeight(),self.view.data.getCXIWidth()),dtype=numpy.float32)
            self.maskData[img] = mask[:]
        else:
            self.maskData[img] = None
        self.imageLoaded.emit(img)
    def clear(self):
        self.loaded = {}
        self.imageData = {}
        self.maskData = {}
