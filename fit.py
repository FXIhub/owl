try:
    import spimage
    hasSpimage = True
except:
    hasSpimage = False

import numpy

class FitModel:
    def __init__(self,dataItemImage,dataItemMask):
        self.dataItemImage = dataItemImage
        self.dataItemMask = dataItemMask

    def find_center(self,img,params):
        if not hasSpimage: return params
        I = self.dataItemImage.data(img=img)
        if(self.dataItemMask):
            M = self.dataItemMask.data(img=img,binaryMask=True)
        else:
            M = numpy.ones(I.shape)
        method = params["_findCenterMethod"]
        x0 = params["offCenterX"]
        y0 = params["offCenterY"]
        dm = params["_maximumShift"]
        th = params["detectorADUPhoton"]/2.
        rm = params["maskRadius"]
        br = params["_blurRadius"]
        if method == 'quadrant':
            x,y = spimage.find_center(I,M,method='quadrant', x0=x0, y0=y0,dmax=dm, threshold=th)
        elif method == 'pw (slow)':
            x,y = spimage.find_center(I,M,method='pixelwise_slow', x0=x0, y0=y0,dmax=dm, rmax=rm)
        elif method == 'pw (fast)':
            x,y = spimage.find_center(I,M,method='pixelwise_fast', x0=x0, y0=y0,dmax=dm, rmax=rm)
        elif method == 'blurred':
            x,y = spimage.find_center(I,M,method='blurred', x0=x0, y0=y0,dmax=dm, threshold=th, blur_radius=br)
        else:
            x,y = [x0, y0]
        params["offCenterX"] = x
        params["offCenterY"] = y
        return params
        
    def fit_diameter(self,img,params):
        if not hasSpimage: return params
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_fitDiameterMethod"]
        d  = params["diameterNM"]
        i  = params["intensityMJUM2"]
        wl = params["photonWavelengthNM"]
        ps = params["detectorPixelSizeUM"]
        D  = params["detectorDistanceMM"]
        x0 = params["offCenterX"]
        y0 = params["offCenterY"]
        ap = params["detectorADUPhoton"]
        qe = params["detectorQuantumEfficiency"]
        m  = params["materialType"]
        rm = params["maskRadius"]
        ne = params["_nrEval"]
        dp = params["_doPhotonCounting"]
        if method == 'pearson':
            diameter, info = spimage.fit_sphere_diameter(I, M, 
                                                         diameter_nm=d, intensity_mJ_per_um2=i, wavelength_nm=wl, pixelsize_um=ps, detector_distance_mm=D,
                                                         method='pearson', full_output=True, x0=x0, y0=y0, adup=ap, queff=qe, mat=m, rmax=rm, downsampling=1, do_brute_evals=ne, do_photon_counting=dp)
        elif method == 'pixelwise':
            diameter, info = spimage.fit_sphere_diameter(I, M,
                                                         diameter_nm=d, intensity_mJ_per_um2=i, wavelength_nm=wl, pixelsize_um=ps, detector_distance_mm=D,
                                                         method='pixelwise', full_output=True, x0=x0, y0=y0, adup=ap, queff=qe, mat=m, rmax=rm, downsampling=1, do_photon_counting=dp)
        else:
            diameter, info = [d, {"pcov":None, "error":None}]
        params["diameterNM"] = diameter
        params["fitErrorDiameterNM"] = info["pcov"]
        params["fitError"] = info["error"]
        return params
            
    def fit_intensity(self,img,params):
        if not hasSpimage: return params
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_fitIntensityMethod"]
        d  = params["diameterNM"]
        i  = params["intensityMJUM2"]
        wl = params["photonWavelengthNM"]
        ps = params["detectorPixelSizeUM"]
        D  = params["detectorDistanceMM"]
        x0 = params["offCenterX"]
        y0 = params["offCenterY"]
        ap = params["detectorADUPhoton"]
        qe = params["detectorQuantumEfficiency"]
        m  = params["materialType"]
        rm = params["maskRadius"]
        dp = params["_doPhotonCounting"]
        if method == 'pixelwise':
            intensity, info = spimage.fit_sphere_intensity(I, M,
                                                           diameter_nm=d, intensity_mJ_per_um2=i, wavelength_nm=wl, pixelsize_um=ps, detector_distance_mm=D,
                                                           method='pixelwise', full_output=True, x0=x0, y0=y0, adup=ap, queff=qe, mat=m, rmax=rm, downsampling=1, do_photon_counting=dp)
        elif method == 'nrphotons':
            intensity, info = spimage.fit_sphere_intensity(I, M,
                                                           diameter_nm=d, intensity_mJ_per_um2=i, wavelength_nm=wl, pixelsize_um=ps, detector_distance_mm=D,
                                                           method='nrphotons', full_output=True, x0=x0, y0=y0, adup=ap, queff=qe, mat=m, rmax=rm, downsampling=1, do_photon_counting=dp)
        else:
            intensity, info = [i, {"pcov":None, "error":None}]
        params["intensityMJUM2"] = intensity
        params["fitErrorIntensityMJUM2"] = info["pcov"]
        params["fitError"] = info["error"]
        return params

    def fit_refine(self, img, params):
        if not hasSpimage: return params
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        d  = params["diameterNM"]
        i  = params["intensityMJUM2"]
        wl = params["photonWavelengthNM"]
        ps = params["detectorPixelSizeUM"]
        D  = params["detectorDistanceMM"]
        x0 = params["offCenterX"]
        y0 = params["offCenterY"]
        ap = params["detectorADUPhoton"]
        qe = params["detectorQuantumEfficiency"]
        m  = params["materialType"]
        rm = params["maskRadius"]
        dp = params["_doPhotonCounting"]
        x0, y0, d, i, info = spimage.fit_full_sphere_model(I, M,
                                                           diameter_nm=d, intensity_mJ_per_um2=i, wavelength_nm=wl, pixelsize_um=ps, detector_distance_mm=D,
                                                           full_output=True, x0=x0, y0=y0, adup=ap, queff=qe, mat=m, rmax=rm, downsampling=1, do_photon_counting=dp)
        params["offCenterX"] = x0
        params["offCenterY"] = y0
        params["diameterNM"] = d
        params["intensityMJUM2"] = i
        params["fitErrorOffCenterX"] = info["pcov"][0]
        params["fitErrorOffCenterY"] = info["pcov"][1]
        params["fitErrorDiameterNM"] = info["pcov"][2]
        params["fitErrorIntensityMJUM2"] = info["pcov"][3]
        params["fitError"] = info["error"]
        return params
        
    def fit_model(self,img,params):
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_fitModelMethod"]
        if method == 'fast':
            if not hasSpimage: return params
            params = self.find_center(img, params)
            params = self.fit_diameter(img, params)
            params = self.fit_intensity(img, params)
        elif method == 'refine':
            if not hasSpimage: return params
            params = self.fit_refine(img, params)
        return params
