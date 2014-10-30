try:
    import spimage
    hasSpimage = True
except:
    hasSpimage = False

class FitModel:
    def __init__(self,dataItemImage,dataItemMask):
        self.dataItemImage = dataItemImage
        self.dataItemMask = dataItemMask

    def find_center(self,img,params):
        if not hasSpimage: return params
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_findCenterMethod"]
        if method == 'quadrant':
            x,y = spimage.find_center(I,M,method='quadrant', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], threshold=params["detectorADUPhoton"]/2.)
        elif method == 'pw (slow)':
            x,y = spimage.find_center(I,M,method='pixelwise_slow', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], rmax=params["maskRadius"])
        elif method == 'pw (fast)':
            x,y = spimage.find_center(I,M,method='pixelwise_fast', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], rmax=params["maskRadius"])
        elif method == 'blurred':
            x,y = spimage.find_center(I,M,method='blurred', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], threshold=params["detectorADUPhoton"]/2., blur_radius=params["_blurRadius"])
        else:
            x,y = spimage.find_center(I,M)
        params["offCenterX"] = x
        params["offCenterY"] = y
        return params

    def fit_model(self,img,params):
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_fitModelMethod"]
        if method == 'fast':
            if not hasSpimage: return params
            params = self.find_center(img, params)
            params = spimage.fit_sphere_model(I,M,params,params["maskRadius"],downsampling=5,do_brute=True)
            params = spimage.fit_sphere_model(I,M,params,params["maskRadius"],downsampling=1,do_brute=False)
        return params
