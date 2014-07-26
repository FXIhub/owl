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
        I[I<params["min_threshold"]] = params["min_threshold"]
        M = self.dataItemMask.data(img=img,binaryMask=True)
        if params["darkfield"] == 0:
            K = kernel(M,params["smooth"])
        else:
            K = kernel(M,params["smooth"],params["x"],params["y"],params["sigma"])
        P = numpy.fft.fftshift(numpy.fft.fft2(numpy.fft.fftshift(K*I)))
        return P

def patterson(img,mask,**kwargs):
    smooth = kwargs.get("smooth",5.)
    K = kernel(mask,smooth)
    P = numpy.fft.fftshift(numpy.fft.fft2(numpy.fft.fftshift(K*img)))
    return P

def kernel(mask,smooth,x=None,y=None,sigma=None):
    K = scipy.ndimage.gaussian_filter(numpy.array(mask,dtype="float"),smooth)
    K -= 0.5*K.max()
    K[K<0] = 0.
    K /= K.max()
    if x!=None and y!=None and sigma!=None: 
        # multiply by darkfield kernel
        Ny, Nx = mask.shape
        NN = Nx*Ny
        X, Y = numpy.ogrid[0:Ny, 0:Nx]
        r = numpy.hypot(X - x, Y - y)
        G = numpy.exp(-r**2/(2*sigma**2))
        K = K*G
    return K
        
