import os
import numpy
import pickle
import logging
import scipy.signal
from scipy.optimize import leastsq
import scipy.stats
try:
    import spimage
    HAS_SPIMAGE = True
except:
    HAS_SPIMAGE = False

class FitModel:
    def __init__(self,dataItemImage,dataItemMask):
        self.dataItemImage = dataItemImage
        self.dataItemMask = dataItemMask
    def center_and_fit(self,img, params):
        params = self.center(img,params)
        params = self.fit(img,params)
        return params
    def center(self,img,params):
        if not HAS_SPIMAGE:
            print "No libspimage"
            return params
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        method = params["_findCenterMethod"]
        if method == 'quadrant':
            x,y = spimage.find_center(I,M,method='quadrant', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"])
        elif method == 'pw (slow)':
            x,y = spimage.find_center(I,M,method='pixelwise_slow', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], rmax=params["maskRadius"])
        elif method == 'pw (fast)':
            x,y = spimage.find_center(I,M,method='pixelwise_fast', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], rmax=params["maskRadius"])
        elif method == 'blurred':
            x,y = spimage.find_center(I,M,method='blurred', x0=params["offCenterX"], y0=params["offCenterY"],dmax=params["_maximumShift"], threshold=12., blur_radius=4.)
        else:
            x,y = spimage.find_center(I,M)
        params["offCenterX"] = x
        params["offCenterY"] = y
        return params
    def fit(self,img,params):
        I = self.dataItemImage.data(img=img)
        M = self.dataItemMask.data(img=img,binaryMask=True)
        params = fit(I,M,params,params["maskRadius"],downsampling=5,do_brute=True)
        params = fit(I,M,params,params["maskRadius"],downsampling=1,do_brute=False)
        return params

#from pylab import *
def fit(image,mask,params,r_max,downsampling=1,do_brute=True):
    # Downsample image
    X,Y = numpy.meshgrid(numpy.arange(0.,image.shape[1],1.),numpy.arange(0.,image.shape[0],1.))
    mask = mask[::downsampling,::downsampling]
    s = image.shape
    cx = (s[1]-1)/2.+params["offCenterX"]
    cy = (s[0]-1)/2.+params["offCenterY"]
    Rsq = (X-cx)**2+(Y-cy)**2
    Mr = (r_max**2)>=Rsq
    Mr = Mr[::downsampling,::downsampling]
    Xm = X[mask*Mr]
    Ym = Y[mask*Mr]
    
    #imsave("img.png",log10(image))
    #imsave("mask.png",mask)
    #imsave("Mr.png",Mr)

    p = params["detectorPixelSizeUM"]*1.E-6
    D = params["detectorDistanceMM"]*1.E-3
    wavelength = params["photonWavelengthNM"]*1.E-9
    h = DICT_physical_constants['h']
    c = DICT_physical_constants['c']
    ey_J = h*c/wavelength
    d = params["diameterNM"]*1.E-9
    I0 = params["intensityMJUM2"]*1.E-3*10E12/ey_J
    Mat = Material(material_type=params["materialType"])
    rho_e = Mat.get_electron_density()
    r = d/2.
    V = 4/3.*numpy.pi*r**3

    fitimg = image[mask*Mr]/params["detectorADUPhoton"]/params["detectorQuantumEfficiency"]

    #q = generate_absqmap(X-cx,Y-cy,p,D,wavelength)
    #I_fit = lambda K,r: I_sphere_diffraction(K,q,r)    
    qm = generate_absqmap(Xm-cx,Ym-cy,p,D,wavelength)
    I_fit_m = lambda K,r: I_sphere_diffraction(K,qm,r)

    # v[0]: K, v[1]: r
    #i_fit = lambda v: I_fit(v[0],v[1])
    i_fit_m = lambda v: I_fit_m(v[0],v[1])

    K = I0 * ( rho_e*p/D*DICT_physical_constants["re"]*V )**2

    err = lambda v: 1-scipy.stats.pearsonr(i_fit_m([K,v]),fitimg)[0]
    maxfev=1000 

    # First fit the radius
    # Start with brute force with a sensible range
    # We'll assume at least 20x oversampling
    if(do_brute):
        pixel_size = (D*wavelength/(p * image.shape[0]))
        range = [(pixel_size, pixel_size*image.shape[0]/(40))]
        Ns = 10 * range[0][1]/range[0][0]
        r = scipy.optimize.brute(err, range, Ns=Ns)[0]
    # End with least square
    # r, success = leastsq(err, r, maxfev=maxfev,xtol=1e-3)
    r, cov_r, infodict, mesg, ier = leastsq(err, r, maxfev=maxfev,xtol=1e-3, full_output=1)
    # print infodict
    r = r[0]

    # Now fit the intensity
    err2 = lambda v: i_fit_m([v,r])-fitimg
    K, success = leastsq(err2, K, maxfev=maxfev, xtol=1e-3)

    v1 = [K,r]
    Vnew = 4/3.*numpy.pi*v1[1]**3
    I0 = v1[0] / (rho_e*p/D*DICT_physical_constants["re"]*Vnew)**2
    params["intensityMJUM2"] = I0/1.E-3/1.E12*ey_J
    params["diameterNM"] = v1[1]*2/1.E-9
    #print params
    return params

# scattering amplitude from homogeneous sphere:
# -----------------------------------------------
# Source:
# Feigin 1987
#
# r: sphere radius
#
# F = sqrt(I_0) rho_e p/D r_0 4/3 pi r^3 [ 3 { sin(qr) - qr cos(qr) } / (qr)^3 ]
#   = sqrt(I_0) rho_e p/D r_0 V f(r,qx,qy)
# f = 3 { sin(qr) - qr cos(qr) } / (qr)^3
# K = I_0 (rho_e p/D r_0 V)^2
# S = I_0 rho_e^2 = K / (p/D r_0 V)^2
# ============================================================================================
# I = F^2 = K [ f(r,qx,qy) ]^2
# ============================================================================================
_F_sphere_diffraction = lambda K,q,r: numpy.sqrt(abs(K))*3*(numpy.sin(q*r)-q*r*numpy.cos(q*r))/((q*r)**3+numpy.finfo("float64").eps)
F_sphere_diffraction = lambda K,q,r: ((q*r)**6 < numpy.finfo("float64").resolution)*numpy.sqrt(abs(K)) + ((q*r)**6 >= numpy.finfo("float64").resolution)*_F_sphere_diffraction(K,q,r)
_I_sphere_diffraction = lambda K,q,r: abs(K)*(3*(numpy.sin(q*r)-q*r*numpy.cos(q*r))/((q*r)**3+numpy.finfo("float64").eps))**2
I_sphere_diffraction = lambda K,q,r: ((q*r)**6 < numpy.finfo("float64").resolution)*abs(K) + ((q*r)**6 >= numpy.finfo("float64").resolution)*_I_sphere_diffraction(K,q,r)

def generate_absqmap(X,Y,p,D,wavelength):
    R_Ewald = 2*numpy.pi/(1.*wavelength)
    qx = R_Ewald*p*X/D
    qy = R_Ewald*p*Y/D
    q_map = numpy.sqrt(qx**2+qy**2)
    return q_map      

class Material:
    def __init__(self,**kwargs):
        if "massdensity" in kwargs:
            self.materialtype = "custom"
            for key in kwargs:
                if key[0] == 'c' or key == 'massdensity':
                    exec "self." + key + " = kwargs[key]"
                else:
                    logger.error("%s is no valid argument for custom initialization of Material." % key)
                    return
        elif "material_type" in kwargs:
            self.material_type = kwargs['material_type']
            self.massdensity = DICT_massdensity[self.material_type]
            self.cH = DICT_atomic_composition[self.material_type][0]
            self.cC = DICT_atomic_composition[self.material_type][1]
            self.cN = DICT_atomic_composition[self.material_type][2]
            self.cO = DICT_atomic_composition[self.material_type][3]
            self.cP = DICT_atomic_composition[self.material_type][4]
            self.cS = DICT_atomic_composition[self.material_type][5]
            self.cAu = DICT_atomic_composition[self.material_type][6]
        else:
            logger.error("No valid arguments for Material initialization.")
            return

    def get_fX(self,element,photon_energy_eV):
        """
        Get the scattering factor for an element through linear interpolation.
        """
        SF_X = DICT_scattering_factors[element]
        e = DICT_physical_constants['e']
        c = DICT_physical_constants['c']
        h = DICT_physical_constants['h']
        f1 = numpy.interp(photon_energy_eV,SF_X[:,0],SF_X[:,1])
        f2 = numpy.interp(photon_energy_eV,SF_X[:,0],SF_X[:,2])
        return complex(f1,f2) 
 
    def get_n(self,photon_energy_eV):
        """
        Obtains complex refractive index.
        Henke (1994): n = 1 - r_0/(2pi) lambda^2 sum_q rho_q f_q(0)
        r_0: classical electron radius
        rho_q: atomic number density of atom species q
        f_q(0): atomic scattering factor (forward scattering) of atom species q
        """

        re = DICT_physical_constants['re']
        h = DICT_physical_constants['h']
        c = DICT_physical_constants['c']
        qe = DICT_physical_constants['e']

        photon_wavelength = h*c/photon_energy_eV/qe

        f = self.get_f(photon_energy_eV)
        atom_density = self.get_atom_density()
        
        n = 1 - re/2/numpy.pi * photon_wavelength**2 * f * atom_density

        return n

    def get_dn(self,photon_energy_eV):
        return (1-self.get_n(photon_energy_eV))

    # convenience functions
    # n = 1 - delta - i beta
    def get_delta(self,photon_energy_eV):
        return (1-self.get_n(photon_energy_eV).real)
    def get_beta(self,photon_energy_eV):
        return (-self.get_n(photon_energy_eV).imag)
    def get_photoabsorption_cross_section(self,photon_energy_eV):
        re = DICT_physical_constants['re']
        h = DICT_physical_constants['h']
        c = DICT_physical_constants['c']
        qe = DICT_physical_constants['e']
        photon_wavelength = h*c/photon_energy_eV/qe
        mu = 2*re*photon_wavelength*self.get_f(photon_energy_eV).imag
        return mu
    def get_transmission(self,thickness,photon_energy_eV):
        n = self.get_n(photon_energy_eV)
        mu = self.get_photoabsorption_cross_section(photon_energy_eV)
        rho = self.get_atom_density()
        return numpy.exp(-rho*mu*thickness)

    def get_f(self,photon_energy_eV):

        h = DICT_physical_constants['h']
        c = DICT_physical_constants['c']
        qe = DICT_physical_constants['e']

        photon_wavelength = h*c/photon_energy_eV/qe

        atomic_composition = self.get_atomic_composition_dict()

        f_sum = 0
        for element in atomic_composition.keys():
            # sum up average atom factor
            f = self.get_fX(element,photon_energy_eV)
            f_sum += atomic_composition[element] * f
        
        return f_sum


    def get_atom_density(self):
                
        u = DICT_physical_constants['u']

        atomic_composition = self.get_atomic_composition_dict()

        M = 0
        for element in atomic_composition.keys():
            # sum up mass
            M += atomic_composition[element]*DICT_atomic_mass[element]*u

        number_density = self.massdensity/M
        
        return number_density


    def get_electron_density(self):

        u = DICT_physical_constants['u']

        atomic_composition = self.get_atomic_composition_dict()

        M = 0
        Q = 0
        for element in atomic_composition.keys():
            # sum up electrons
            M += atomic_composition[element]*DICT_atomic_mass[element]*u
            Q += atomic_composition[element]*DICT_atomic_number[element]

        electron_density = Q*self.massdensity/M
        
        return electron_density
        
        
    def get_atomic_composition_dict(self):

        atomic_composition = {}
        
        for key in self.__dict__.keys():
            if key[0] == 'c':
                exec "c_tmp = self." + key
                atomic_composition[key[1:]] = c_tmp 
 
        tmp_sum = float(sum(atomic_composition.values()))
        for element in atomic_composition.keys():
            atomic_composition[element] /= tmp_sum 
        
        return atomic_composition

# Realative atomic compositions of certain material types (order: H,C,N,O,P,S,Au)
DICT_atomic_composition = {'protein':[86,52,13,15,0,3,0],
                           'cell':[23,3,1,10,0,1,0], # Bergh et al. 2008
                           'latex':[1,1,0,0,0,0,0], 
                           'water':[2,0,0,1,0,0,0], 
                           'dna':[11,10,4,6,1,0,0],
                           'lipid':[69,36,0,6,1,0,0],
                           'genophore':[205,134,38,48,3,6,0],
                           'virus':[72.43,49.85,16.32,24.49,2.57,1.39,0],
                           'mimivirus':[23,3,1,10,0,1,0],
                           'carboxysome':[0.51,0.30,0.07,0.10,0.,0.02,0],
                           'sucrose':[22,12,0,11,0,0,0],
                           'gold':[0,0,0,0,0,0,1]}
# Estimated mass densities of certain material types
DICT_massdensity = {'protein':1350,
                    'cell':1000,
                    'latex':1050,
                    'water':998,
                    'gold':19300,
                    'dna':1700,
                    'lipid':1000,
                    'genophore':1560,
                    'virus':1381,
                    'mimivirus':1100,
                    'carboxysome':1250,
                    'sucrose':1587}
DICT_atomic_number = {'H':1,
                      'He':2,
                      'Li':3,
                      'Be':4,
                      'B':5,
                      'C':6,
                      'N':7,
                      'O':8,
                      'F':9,
                      'Ne':10,
                      'Na':11,
                      'Mg':12,
                      'Al':13,
                      'Si':14,
                      'P':15,
                      'S':16,
                      'Cl':17,
                      'Ar':18,
                      'K':19,
                      'Ca':20,
                      'Sc':21,
                      'Ti':22,
                      'V':23,
                      'Cr':24,
                      'Mn':25,
                      'Fe':26,
                      'Co':27,
                      'Ni':28,
                      'Cu':29,
                      'Zn':30,
                      'Ga':31,
                      'Ge':32,
                      'As':33,
                      'Se':34,
                      'Br':35,
                      'Kr':36,
                      'Rb':37,
                      'Sr':38,
                      'Y':39,
                      'Zr':40,
                      'Nb':41,
                      'Mo':42,
                      'Tc':43,
                      'Ru':44,
                      'Rh':45,
                      'Pd':46,
                      'Ag':47,
                      'Cd':48,
                      'In':49,
                      'Sn':50,
                      'Sb':51,
                      'Te':52,
                      'I':53,
                      'Xe':54,
                      'Cs':55,
                      'Ba':56,
                      'La':57,
                      'Ce':58,
                      'Pr':59,
                      'Nd':60,
                      'Pm':61,
                      'Sm':62,
                      'Eu':63,
                      'Gd':64,
                      'Tb':65,
                      'Dy':66,
                      'Ho':67,
                      'Er':68,
                      'Tm':69,
                      'Yb':70,
                      'Lu':71,
                      'Hf':72,
                      'Ta':73,
                      'W':74,
                      'Re':75,
                      'Os':76,
                      'Ir':77,
                      'Pt':78,
                      'Au':79,
                      'Hg':80,
                      'Tl':81,
                      'Pb':82,
                      'Bi':83,
                      'Po':84,
                      'At':85,
                      'Rn':86,
                      'Fr':87,
                      'Ra':88,
                      'Ac':89,
                      'Th':90,
                      'Pa':91,
                      'U':92,
                      'Np':93,
                      'Pu':94,
                      'Am':95,
                      'Cm':96,
                      'Bk':97,
                      'Cf':98,
                      'Es':99,
                      'Fm':100,
                      'Md':101,
                      'No':102,
                      'Lr':103,
                      'Rf':104,
                      'Db':105,
                      'Sg':106,
                      'Bh':107,
                      'Hs':108,
                      'Mt':109,
                      'Ds':110,
                      'Rg':111,
                      'Cp':112,
                      'Uut':113,
                      'Uuq':114,
                      'Uup':115,
                      'Uuh':116,
                      'Uus':117,
                      'Uuo':118}

DICT_physical_constants = {'e':1.60217657E-19,
                           'c':299792458.,
                           'h':6.62606957E-34,
                           're':2.8179403267E-15,
                           'barn':1E-28,
                           'u':1.66053886E-27}

def unpickle_scattering_factors():
    global DICT_atomic_mass
    DICT_atomic_mass = {}
    global DICT_scattering_factors
    DICT_scattering_factors = {}
    this_dir = os.path.dirname(os.path.realpath(__file__))
    ELEMENTS_FILE = open('%s/data/elements.dat' % this_dir,'r')
    DICT_atomic_mass,DICT_scattering_factors = pickle.load(ELEMENTS_FILE)
    F_MIN_ENERGY_EV = 0
    F_MAX_ENERGY_EV = 0
    for var in DICT_scattering_factors.values():
        if F_MIN_ENERGY_EV < var[0,0] or F_MIN_ENERGY_EV == 0: F_MIN_ENERGY_EV = var[0,0]
        if F_MAX_ENERGY_EV > var[-1,0] or F_MAX_ENERGY_EV == 0: F_MAX_ENERGY_EV = var[-1,0]

unpickle_scattering_factors()
