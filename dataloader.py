from PySide import QtGui, QtCore
import numpy,cmath
import logging
from cache import ArrayCache
import h5py
import settingsOwl

class FileLoader(QtCore.QObject):
    stackSizeChanged = QtCore.Signal(int)
    def __init__(self,parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
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
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self,"/"+k)
        self.dataItems = {}
        self.groupItems = {}
        self.tagsItems = {}
        self.modelItems = {}
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
                self.collectItems(child.children)
            else:
                print "no valid item."
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


class GroupItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.H5Group = parent.H5Group[self.name]
        self.modelItem = ModelItem(self,fileLoader,fullName+"/")
        self.tagsItem = TagsItem(self,fileLoader,fullName+"/")
        self.children = {}
        for k in self.H5Group.keys():
            item = self.H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fileLoader,self.fullName+"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fileLoader,self.fullName+"/"+k)

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
                    title = 'Tag '+(i+1)
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
    def __init__(self,parent,fileLoader,path):
        self.parent = parent
        self.fileLoader = fileLoader
        self.path = path
        self.params = {}
        if("model_parameters" in self.fileLoader.f[self.path].keys()):
            if "names" in self.fileLoader.f[self.path+"model_parameters"].attrs.keys():
                names = self.fileLoader.f[self.path+"model_parameters"].attrs["names"]
                for i,name in zip(range(len(names)),names):
                    self.params[name] = self.fileLoader.f[self.path+"model_parameters"][i,:]



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
    #def patterson(self,**kwargs):
    #    data = self.data(**kwargs)
        
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
        #patterson = self.view.getPatterson(img)
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
    def clear(self):
        # Unlimited cache
        self.imageData = ArrayCache(1024*1024*int(QtCore.QSettings().value("imageCacheSize")))
        self.phaseData = ArrayCache(1024*1024*int(QtCore.QSettings().value("phaseCacheSize")))
        self.maskData = ArrayCache(1024*1024*int(QtCore.QSettings().value("maskCacheSize")))
    def loadedImages(self):
        return self.imageData.keys()
