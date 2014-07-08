import numpy
import logging
import scipy.signal

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


def kernel(mask,smooth):
    K = gaussian_smooth(mask,smooth)
    K -= 0.5*K.max()
    K[K<0] = 0.
    K /= K.max()
    return K

def gaussian_smooth(I,sm,precision=1.):
    N = 2*int(numpy.round(precision*sm))+1
    if len(I.shape) == 2:
        X,Y = numpy.meshgrid(numpy.arange(0,N,1),numpy.arange(0,N,1))
        X = X-N/2
        Y = Y-N/2
        R = numpy.sqrt(X**2 + Y**2)
        kernel = numpy.exp(R**2/(2.0*sm**2))
        kernel[abs(R)>N/2] = 0.
        kernel /= kernel.sum()
        Ism = scipy.signal.convolve2d(I,kernel,mode='same',boundary='fill')
        return Ism
    elif len(I.shape) == 1:
        X = numpy.arange(0,N,1)
        X = X-(N-1)/2.
        kernel = numpy.exp(X**2/(2.0*sm**2))
        kernel /= kernel.sum()
        Ism = numpy.convolve(I,kernel,mode='same')
        return Ism
