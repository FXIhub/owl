import numpy
import logging
import scipy.signal
import scipy.ndimage

class PattersonCreator:
    def __init__(self,dataItemImage,dataItemMask):
        self.dataItemMask = dataItemMask
        self.dataItemImage = dataItemImage
    def patterson(self,img):
        params = self.dataItemImage.pattersonItem.getParams(img)
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        K = kernel(M,params["smooth"])
        P = numpy.fft.fftshift(numpy.fft.fft2(numpy.fft.fftshift(K*I)))
        return P

def patterson(img,mask,**kwargs):
    smooth = kwargs.get("smooth",5.)
    K = kernel(mask,smooth)
    P = numpy.fft.fftshift(numpy.fft.fft2(numpy.fft.fftshift(K*img)))
    return P

def kernel(mask,smooth):
    K = scipy.ndimage.gaussian_filter(numpy.array(mask,dtype="float"),smooth)
    #K = scipy.ndimage.gaussian_filter(mask,smooth)
    K -= 0.5*K.max()
    K[K<0] = 0.
    K /= K.max()
    return K
