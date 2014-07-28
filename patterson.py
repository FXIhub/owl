import numpy
import logging
import scipy.signal
import scipy.ndimage

def patterson(I,M,params,normalize=False):
    I = numpy.clip(I - params["imageThreshold"], 0, numpy.inf)
    if not params["darkfield"]:
        K = kernel(M,params["maskSmooth"],params["maskThreshold"])
    else:
        K = kernel(M,params["maskSmooth"],params["maskThreshold"],params["darkfieldX"],params["darkfieldY"],params["darkfieldSigma"])
    P = numpy.fft.fftshift(numpy.fft.fft2(numpy.fft.fftshift(K*I)))
    if normalize:
        P = abs(P)
        P /= numpy.median(P)*10
    return P

def kernel(mask,smooth,threshold,x=None,y=None,sigma=None):
    K = scipy.ndimage.gaussian_filter(numpy.array(mask,dtype="float"),smooth)
    t = K.max()*threshold
    K[K<t] = 0
    K = scipy.ndimage.gaussian_filter(numpy.array(K,dtype="float"),smooth)
    K /= K.max()
    if x!=None and y!=None and sigma!=None: 
        # multiply by darkfield kernel
        Ny, Nx = mask.shape
        cx = (Nx-1)/2
        cy = (Ny-1)/2
        NN = Nx*Ny
        X, Y = numpy.ogrid[0:Ny, 0:Nx]
        r = numpy.hypot(X - (cx + x), Y - (cx + y))
        G = numpy.exp(-r**2/(2*sigma**2))
        K = K*G
    return K
