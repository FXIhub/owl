from PySide import QtGui, QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl
import fit
import patterson

class FileLoader(QtCore.QObject):
    stackSizeChanged = QtCore.Signal(int)
    datasetTreeChanged = QtCore.Signal()
    def __init__(self,parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.stackSize = None
    def loadFile(self,fullFilename):
        try:
            self.f = h5py.File(fullFilename, "r+")
        except IOError as e:            
            if( str(e) == 'Unable to open file (File is already open for write or swmr write)'):                                
                print "\n\n!!! TIP: Trying running h5clearsb.py on the file !!!\n\n"
            raise
#            print e.strerror
        #self.f = h5py.File(fullFilename, "r*") # for swmr
        self.fullFilename = fullFilename
        self.filename = QtCore.QFileInfo(fullFilename).fileName()
        self.fullName = self.name = "/"
        self.H5Group = self.f["/"]
        self.tagsItem = None
        self.modelItem = None
        self.pattersonItem = None
        self.dataItems = {}
        self.groupItems = {}
        self.tagsItems = {}
        self.modelItems = {}
        self.pattersonItems = {}
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self,"/"+k)
        self.collectItems(self.children)
        self.stackSize = None
    def collectItems(self,item):
        for k in item.keys():
            child = item[k]
            if isinstance(child,DataItem):
                self.dataItems[child.fullName] = child
            elif isinstance(child,GroupItem):
                self.groupItems[child.fullName] = child
                self.tagsItems[child.fullName] = child.tagsItem
                self.modelItems[child.fullName] = child.modelItem
                self.pattersonItems[child.fullName] = child.pattersonItem
                self.collectItems(child.children)
            else:
                print "no valid item."
    def addGroupPosterior(self,name0):
        name = name0
        if name[0] == "/": name = name[1:]
        if name[-1] == "/": name = name[:-1]
        path = name[0:name.rindex('/')]

        def addGroupRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    g = GroupItem(group,self,"/"+name)
                    c.children[name[name.rindex('/')+1:]] = g
                    self.groupItems[name] = g
                elif isinstance(c,GroupItem):                  
                    addGroupRecursively(c,c.children)

        addGroupRecursively(self,self.children)
    def addDatasetPosterior(self,name0):
        name = name0
        if name[0] == "/": name = name[1:]
        if name[-1] == "/": name = name[:-1]
        path = name[0:name.rindex('/')]

        def addDatasetRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    d = DataItem(group,self,"/"+name)
                    c.children[name[name.rindex('/')+1:]] = d
                    self.dataItems[name] = d
                elif isinstance(c,GroupItem):                  
                    addDatasetRecursively(c,c.children)

        addDatasetRecursively(self,self.children)
    def updateStackSize(self):
        N = []
        for n,d in self.dataItems.items():
            if d.isSelectedStack:
                if "numEvents" in self.f[n].attrs.keys():
                    N.append(self.f[n].attrs.get("numEvents")[0])
                else:
                    N.append(self.f[n].shape[d.stackDim])
        if len(N) > 0:
            N = numpy.array(N).min()
        else:
            N = None
        if N != self.stackSize:
            self.stackSize = N
            self.stackSizeChanged.emit(N)
    def saveTags(self):
        for n,t in self.tagsItems.items():
            t.saveTags()
    def modelsChanged(self):
        for n,m in self.modelItems.items():
            if m.paramsDirty:
                return True
        return False
    def saveModels(self):
        for n,m in self.modelItems.items():
            m.saveParams()

class GroupItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.H5Group = parent.H5Group[self.name]
        self.tagsItem = TagsItem(self,fileLoader,fullName+"/")
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fileLoader,self.fullName+"/"+k)
        self.modelItem = ModelItem(self,fileLoader,fullName+"/",self.children)
        self.pattersonItem = PattersonItem(self,fileLoader,fullName+"/",self.children)
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fileLoader,self.fullName+"/"+k)

# CXI pixelmask bits
PIXEL_IS_PERFECT = 0
PIXEL_IS_INVALID = 1
PIXEL_IS_SATURATED = 2
PIXEL_IS_HOT = 4
PIXEL_IS_DEAD = 8
PIXEL_IS_SHADOWED = 16
PIXEL_IS_IN_PEAKMASK = 32
PIXEL_IS_TO_BE_IGNORED = 64
PIXEL_IS_BAD = 128
PIXEL_IS_OUT_OF_RESOLUTION_LIMITS = 256
PIXEL_IS_MISSING = 512
PIXEL_IS_IN_HALO = 1024
PIXEL_IS_ARTIFACT_CORRECTED = 2048
PIXEL_IS_IN_MASK = PIXEL_IS_INVALID |  PIXEL_IS_SATURATED | PIXEL_IS_HOT | PIXEL_IS_DEAD | PIXEL_IS_SHADOWED | PIXEL_IS_IN_PEAKMASK | PIXEL_IS_TO_BE_IGNORED | PIXEL_IS_BAD | PIXEL_IS_MISSING

class DataItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        #self.H5Dataset = parent.H5Group[self.name]
        self.dtypeName = self.fileLoader.f[self.fullName].dtype.name
        self.dtypeItemsize = self.fileLoader.f[self.fullName].dtype.itemsize
        self.logger = logging.getLogger("DataItem")
        self.logger.setLevel(settingsOwl.loglev["DataItem"])
        self.isSelectedStack = False
        # check whether or not it is a stack
        if len(self.fileLoader.f[self.fullName].attrs.items()) > 0 and "axes" in self.fileLoader.f[self.fullName].attrs.keys():
            self.isStack = True
            self.stackDim = self.fileLoader.f[self.fullName].attrs.get("axes")[0].split(":").index("experiment_identifier")
        else:
            self.isStack = False
            self.stackDim = None
        # check whether or not it is text
        self.isText = (str(self.fileLoader.f[self.fullName].dtype.name).find("string") != -1)
        # presentable as values
        self.isPresentable = (self.isText == False)
        # shape?
        self.format = len(self.shape())
        # image stack?
        if self.isStack: self.format -= 1
        # complex?
        self.isComplex = (str(self.fileLoader.f[self.fullName].dtype.name).lower().find("complex") != -1)

        # link tags
        self.tagsItem = self.parent.tagsItem

        # link model parameters
        self.modelItem = self.parent.modelItem

        # link patterson parameters
        self.pattersonItem = self.parent.pattersonItem

        # Selected dimension for filetering etc. where stack has to have only one dimension
        # Set to none by default
        self.selectedIndex = None

    def shape(self,forceRefresh=False):
        shape = self.fileLoader.f[self.fullName].shape
        if self.isSelectedStack and self.fileLoader.stackSize != None:
        # MFH: Isnn't the following line be more logical than what we have currently?
        #if self.isStack and self.fileLoader.stackSize != None:
            shape = list(shape)
            shape.pop(0)
            shape.insert(0,self.fileLoader.stackSize)
            #self._shape.insert(0,self.H5Dataset.attrs.get("numEvents", (self.H5Dataset.shape))[0])
            shape = tuple(shape)
        return shape
    def width(self,forceRefresh=False):
        return self.shape(forceRefresh)[-1]
    def height(self,forceRefresh=False):
        return self.shape(forceRefresh)[-2]
    def deselectStack(self):
        if self.isSelectedStack:
            self.isSelectedStack = False
            self.fileLoader.updateStackSize()
        else:
            self.isSelectedStack = False
    def selectStack(self):
        if self.isStack:
            self.isSelectedStack = True
            self.fileLoader.updateStackSize()
    def attr(self,name):
        return self.fileLoader.f[self.fullName].attrs[name]
        
    def data(self,**kwargs):
        try:
            self.fileLoader.f[self.fullName].refresh()
        except:
            self.logger.debug("Failed to refresh dataset. Probably the h5py version that is installed does not support SWMR.")

        complex_mode = kwargs.get("complex_mode",None)
        if self.isComplex == False and complex_mode != None:
            return None
        if self.isStack and self.format == 2:
            img = kwargs.get("img",None)
            d = numpy.array(self.fileLoader.f[self.fullName][img])

        elif self.isStack and self.format == 1:
            if self.fileLoader.stackSize == None:
                d = numpy.array(self.fileLoader.f[self.fullName])[:,:]
            else:
                d = numpy.array(self.fileLoader.f[self.fullName])[:self.fileLoader.stackSize,:]

        elif self.isStack and self.format == 0:
            if self.fileLoader.stackSize == None:
                d = numpy.array(self.fileLoader.f[self.fullName])
            else:
                d = numpy.array(self.fileLoader.f[self.fullName])[:self.fileLoader.stackSize]

        else:
            d = numpy.array(self.fileLoader.f[self.fullName])

        ix = kwargs.get("ix",None)
        iy = kwargs.get("iy",None)
        if ix != None and iy != None:
            if len(d.shape) == 3:
                d = d[:,iy,ix]
            else:
                d = d[iy,ix]

        if kwargs.get("binaryMask",False):
            d = (d & PIXEL_IS_IN_MASK) == 0

        windowSize = kwargs.get("windowSize",None)
        if windowSize != None:
            # Running average by convolution with an exponentially decaying weight kernel in respect to time.
            # d12: decay half-time
            # The total window size is two times d12, defining the absolute length of the memory.
            d12 = int(windowSize/2.)
            x = numpy.arange(2*d12-1,-1,-1)
            tmp = numpy.exp(x**2/d12**2*numpy.log(2))
            w = tmp/tmp.sum()
            N = len(d)
            d = numpy.convolve(d, w, 'full')[:N]

        if self.isComplex:
            if complex_mode == "phase":
                d = numpy.angle(d)
            elif complex_mode == "real":
                d = d.real
            elif complex_mode == "imag":
                d = d.imag
            else:
                # default is the absolute value / amplitude
                d = abs(d)

        return d
    def data1D(self,**kwargs):
        if len(self.shape()) == 2:
            if self.stackDim == 0:
                return self.data(**kwargs)[:,self.selectedIndex]
            else:
                return self.data(**kwargs)[self.selectedIndex,:]
        else:
            return f.data(**kwargs)


class TagsItem:
    def __init__(self,parent,fileLoader,path):
        self.parent = parent
        self.fileLoader = fileLoader
        self.path = path
        # Check for tags
        self.tags = []
        self.tagMembers = None
        self.tagsDirty = False
        #self.path = fullName[0:fullName.rindex('/')+1]

        settings = QtCore.QSettings()
        defaultColors = settings.value('TagColors')
        if('tags' in self.fileLoader.f[self.path].keys()):
            self.tagMembers = numpy.array(self.fileLoader.f[self.path+'tags'])
            has_headings = False
            has_colors = False
            if('headings' in self.fileLoader.f[self.path+'tags'].attrs.keys()):
                has_headings = True
            if('colors' in self.fileLoader.f[self.path+'tags'].attrs.keys()):
                has_colors = True
            
            for i in range(0,self.tagMembers.shape[0]):
                if(has_headings):
                    title = self.fileLoader.f[self.path+'tags'].attrs['headings'][i]
                else:
                    title = 'Tag %i' % (i+1)
                if(has_colors):
                    r =  self.fileLoader.f[self.path+'tags'].attrs['colors'][i][0]
                    g =  self.fileLoader.f[self.path+'tags'].attrs['colors'][i][1]
                    b =  self.fileLoader.f[self.path+'tags'].attrs['colors'][i][2]
                    color = QtGui.QColor(r,g,b)
                else:
                    color = defaultColors[i]
                self.tags.append([title,color,QtCore.Qt.Unchecked,self.tagMembers[i,:].sum()])
    def setTags(self,tags):
        self.tagsDirty = True
        newMembers = numpy.zeros((len(tags),self.fileLoader.stackSize),dtype=numpy.int8)
        if(self.tagMembers != None):
            newMembers = numpy.zeros((len(tags),self.fileLoader.stackSize),dtype=numpy.int8)
            # Copy old members to new members
            for i in range(0,len(tags)):
                # Check if the new tag is an old tag
                newTag = True
                for j in range(0,len(self.tags)):
                    if tags[i][0] == self.tags[j][0]:
                        newMembers[i][:] = self.tagMembers[j][:]
                        newTag = False
                        break
                if(newTag):
                    newMembers[i][:] = 0

        self.tagMembers = newMembers
        self.tags = tags
    def saveTags(self):
        # Do we really have to write anything? If not just return.
        if (self.tags == []) or (self.tagsDirty == False):
            return
        # Is a tag dataset already existing
        if('tags' in self.fileLoader.f[self.path]):
            ds = self.fileLoader.f[self.path+"tags"]
            # MFH: I suspect that this corrupts the file somethimes. Therefore I just do a resize of the dataset instead if it already exists
            #del self.fileLoader.f[self.path+'tags']
            oldShape = ds.shape
            newShape = self.tagMembers.shape
            if (oldShape[0] == newShape[0]) and (oldShape[1] == newShape[1]):
                ds.resize(newShape)
                ds[:,:] = self.tagMembers[:,:]
        else:
            ds = self.fileLoader.f[self.path].create_dataset('tags',self.tagMembers.shape,maxshape=(None,None),chunks=(1,10000),data=self.tagMembers)
            ds.attrs.modify("axes",["tag:experiment_identifier"])
            self.fileLoader.addDatasetPosterior(self.path+"tags")
            self.fileLoader.datasetTreeChanged.emit()
        # Save tag names
        headings = []
        for i in range(0,len(self.tags)):
            headings.append(str(self.tags[i][0]))
        ds.attrs['headings'] = headings
        # Save tag colors
        colors = numpy.zeros((len(self.tags),3),dtype=numpy.uint8)
        for i in range(0,len(self.tags)):
            colors[i,0] = self.tags[i][1].red()
            colors[i,1] = self.tags[i][1].green()
            colors[i,2] = self.tags[i][1].blue()
        ds.attrs['colors'] = colors
    def setTag(self,img,tag,value):
        if(tag >= self.tagMembers.shape[0]):
            return
        self.tagsDirty = True
        if(value):
            self.tagMembers[tag,img] = 1
        else:
            self.tagMembers[tag,img] = 0
        self.fileLoader.parent.statusBar.showMessage('Tag '+self.tags[tag][0]+' set to '+str(bool(value)))
        self.updateTagSum()
    def updateTagSum(self):
        for i in range(0,len(self.tags)):
            self.tags[i][3] = self.tagMembers[i,:].sum()

class ModelItem:
    def __init__(self,parent,fileLoader,path,groupChildren):
        self.parent = parent
        self.fileLoader = fileLoader
        self.path = path
        self.paramsDirty = False
        self.dataItemImage = None
        self.dataItemMask = None
        self.indParams = {}
        self.genParams = {}
        self.paramsIndDef = {"offCenterX":0.,"offCenterY":0.,"intensityMJUM2":1.,"diameterNM":100.,"maskRadius":100}
        self.paramsGenDef = {"photonWavelengthNM":1.,"detectorDistanceMM":1000.,"detectorPixelSizeUM":75.,"detectorQuantumEfficiency":1.,"detectorADUPhoton":10.,"materialType":"water","_visibility":0.5}
        self.dataItems = {}
        if "model" in groupChildren:
            for n in self.paramsIndDef:
                self.dataItems[n] = groupChildren["model"].children[n]
            for n in self.paramsGenDef:
                self.dataItems[n] = groupChildren["model"].children[n]
        self.initParams()
    def initParams(self):
        if self.fileLoader.stackSize == None:
            return
        else:
            N = self.fileLoader.stackSize
            # set all general params to default values
            for n,v in self.paramsGenDef.items():
                self.genParams[n] = v
            #  set all individual params to default values
            for n,v in self.paramsIndDef.items():
                self.indParams[n] = numpy.ones(N)*v
            # read data from file if available
            for n,d in self.dataItems.items():
                data = d.data()
                if n in self.genParams:
                    self.genParams[n] = data[0]
                elif n in self.indParams:
                    self.indParams[n][:len(data)] = data[:]
    def getParams(self,img0):
        if (self.genParams == {}) or (self.indParams == {}):
            self.initParams()
        if img0 == None:
            img = 0
        else:
            img = img0
        ps = {}
        for n,p in self.genParams.items():
            ps[n] = p
        for n,p in self.indParams.items():
            ps[n] = p[img]
        return ps
    def setParams(self,img,paramsNew):
        paramsOld = self.getParams(img)
        for n,pNew in paramsNew.items():
            if n in self.indParams:
                if pNew != paramsOld[n]:
                    self.paramsDirty = True
                    self.indParams[n][img] = pNew
            elif n in self.genParams:
                if pNew != paramsOld[n]:
                    self.paramsDirty = True
                    self.genParams[n] = pNew
    def saveParams(self):
        treeDirty = False
        if self.paramsDirty:
            if "model" in self.fileLoader.f[self.path]:
                grp = self.fileLoader.f[self.path+"model"]
            else:
                grp = self.fileLoader.f.create_group(self.path+"model")
                self.fileLoader.addGroupPosterior(self.path+"model")
                treeDirty = True
            for n,p in self.indParams.items():
                if n in grp:
                    ds = grp[n]
                    if ds.shape[0] != p.shape:
                        ds.resize(p.shape)
                    ds[:len(p)] = p[:]
                else:
                    ds = self.fileLoader.f.create_dataset(self.path+"model/"+n,p.shape,maxshape=(None,),chunks=(10000,),data=p)
                    ds.attrs.modify("axes",["experiment_identifier"])
                    self.fileLoader.addDatasetPosterior(self.path+"model/"+n)
                    treeDirty = True
            for n,p in self.genParams.items():
                if n in grp:
                    ds = grp[n]
                    ds[0] = p
                else:
                    ds = self.fileLoader.f.create_dataset(self.path+"model/"+n,(1,),data=p)
                    self.fileLoader.addDatasetPosterior(self.path+"model/"+n)
                    treeDirty = True
            self.paramsDirty = False
        # the following two lines lead to a crash and a corrupt file, I have no clue why
        #if treeDirty:
        #    self.fileLoader.datasetTreeChanged.emit()
    def centerAndFit(self,img):
        M = fit.FitModel(self.dataItemImage,self.dataItemMask)
        newParams = M.center_and_fit(img)
        self.setParams(img,newParams)
    def center(self,img):
        M = fit.FitModel(self.dataItemImage,self.dataItemMask)
        newParams = M.center(img,self.getParams(img))
        self.setParams(img,newParams)
    def fit(self,img):
        M = fit.FitModel(self.dataItemImage,self.dataItemMask)
        newParams = M.fit(img,self.getParams(img))
        self.setParams(img,newParams)


class PattersonItem:
    def __init__(self,parent,fileLoader,path,groupChildren):
        self.parent = parent
        self.fileLoader = fileLoader
        self.path = path
        self.paramsDirty = False
        self.dataItemImage = None
        self.dataItemMask = None
        self.indParams = {}
        self.genParams = {}
        self.paramsIndDef = {"smooth":5.}
        self.paramsGenDef = {"pattersonImg":-1}
        self.dataItems = {}
        self.patterson = None
        self.textureLoaded = False
        if "patterson" in groupChildren:
            for n in self.paramsIndDef:
                self.dataItems[n] = groupChildren["patterson"].children[n]
            for n in self.paramsGenDef:
                self.dataItems[n] = groupChildren["patterson"].children[n]
        self.initParams()
    def initParams(self):
        if self.fileLoader.stackSize == None:
            return
        else:
            N = self.fileLoader.stackSize
            # set all general params to default values
            for n,v in self.paramsGenDef.items():
                self.genParams[n] = v
            #  set all individual params to default values
            for n,v in self.paramsIndDef.items():
                self.indParams[n] = numpy.ones(N)*v
            # read data from file if available
            for n,d in self.dataItems.items():
                data = d.data()
                if n in self.genParams:
                    self.genParams[n] = data[0]
                elif n in self.indParams:
                    self.indParams[n][:len(data)] = data[:]
    def getParams(self,img0):
        if (self.genParams == {}) or (self.indParams == {}):
            self.initParams()
        if img0 == None:
            img = 0
        else:
            img = img0
        ps = {}
        for n,p in self.genParams.items():
            ps[n] = p
        for n,p in self.indParams.items():
            ps[n] = p[img]
        return ps
    def setParams(self,img,paramsNew):
        paramsOld = self.getParams(img)
        for n,pNew in paramsNew.items():
            if n in self.indParams:
                if pNew != paramsOld[n]:
                    self.paramsDirty = True
                    self.indParams[n][img] = pNew
            elif n in self.genParams:
                if pNew != paramsOld[n]:
                    self.paramsDirty = True
                    self.genParams[n] = pNew
    def saveParams(self):
        treeDirty = False
        if self.paramsDirty:
            if "patterson" in self.fileLoader.f[self.path]:
                grp = self.fileLoader.f[self.path+"patterson"]
            else:
                grp = self.fileLoader.f.create_group(self.path+"patterson")
                self.fileLoader.addGroupPosterior(self.path+"patterson")
                treeDirty = True
            for n,p in self.indParams.items():
                if n in grp:
                    ds = grp[n]
                    if ds.shape[0] != p.shape:
                        ds.resize(p.shape)
                    ds[:len(p)] = p[:]
                else:
                    ds = self.fileLoader.f.create_dataset(self.path+"patterson/"+n,p.shape,maxshape=(None,),chunks=(10000,),data=p)
                    ds.attrs.modify("axes",["experiment_identifier"])
                    self.fileLoader.addDatasetPosterior(self.path+"patterson/"+n)
                    treeDirty = True
            for n,p in self.genParams.items():
                if n in grp:
                    ds = grp[n]
                    ds[0] = p
                else:
                    ds = self.fileLoader.f.create_dataset(self.path+"patterson/"+n,(1,),data=p)
                    self.fileLoader.addDatasetPosterior(self.path+"patterson/"+n)
                    treeDirty = True
            self.paramsDirty = False
        # the following two lines lead to a crash and a corrupt file, I have no clue why
        #if treeDirty:
        #    self.fileLoader.datasetTreeChanged.emit()
    def calculatePatterson(self,img):
        PC = patterson.PattersonCreator(self.dataItemImage,self.dataItemMask)
        self.patterson = PC.patterson(img)
        self.setParams(img,{"pattersonImg":img})
        self.textureLoaded = False

class ImageLoader(QtCore.QObject):
    imageLoaded = QtCore.Signal(int)
    def __init__(self,parent = None,view = None):
        QtCore.QObject.__init__(self,parent)
        self.view = view
        self.clear()
        self.logger = logging.getLogger("ImageLoader")
        # If you want to see debug messages change level here
        self.logger.setLevel(settingsOwl.loglev["ImageLoader"])

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
        data = self.view.getData(img)
        phase = self.view.getPhase(img)
        mask = self.view.getMask(img)
        self.imageData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
        self.imageData[img][:] = data[:]
        if phase != None:
            self.phaseData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
            self.phaseData[img][:] = phase[:]
        else:
            self.phaseData[img] = None
        if mask != None:
            self.maskData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
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
    def loadPatterson(self,img):
        patterson = self.view.getPatterson()
        self.pattersonData[img] = numpy.ones((self.view.data.height(),self.view.data.width()),dtype=numpy.float32)
        self.pattersonData[img][:] = abs(patterson)[:]
        self.imageLoaded.emit(img)
    def loadedImages(self):
        return self.imageData.keys()
    def loadedPatterson(self):
        return self.pattersonData.keys()
    def clear(self):
        # Unlimited cache
        self.imageData = ArrayCache(1024*1024*int(QtCore.QSettings().value("imageCacheSize")))
        self.phaseData = ArrayCache(1024*1024*int(QtCore.QSettings().value("phaseCacheSize")))
        self.maskData = ArrayCache(1024*1024*int(QtCore.QSettings().value("maskCacheSize")))
        self.pattersonData = ArrayCache(1024*1024*int(QtCore.QSettings().value("imageCacheSize")))
