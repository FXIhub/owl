from PySide import QtGui, QtCore
import logging
import numpy
import fit
import patterson

class AbstractParameterItem:
    def __init__(self,parentGroup,fileLoader,name,individualParamsDef,generalParamsDef):
        self.parentGroup = parentGroup
        self.fileLoader = fileLoader
        self.name = name
        self.path = parentGroup.fullName+"/"
        self.fullName = self.path+name
        self.paramsIndDef = individualParamsDef
        self.paramsGenDef = generalParamsDef
        self.paramsDirty = False
        self.dataItemImage = None
        self.dataItemMask = None
        self.indParams = {}
        self.genParams = {}
        self.dataItems = {}
        self.initParams()
    def initParams(self):
        # return if we do not even know the stack size
        if self.fileLoader.stackSize == None:
            return
        N = self.fileLoader.stackSize
        # set all general params to default values
        for n,v in self.paramsGenDef.items():
            self.genParams[n] = v
        #  set all individual params to default values
        for n,v in self.paramsIndDef.items():
            self.indParams[n] = numpy.ones(N)*v
        # link to existing data items if there are any
        if self.name in self.parentGroup.children:
            gi = self.parentGroup.children[self.name]
            for n in self.paramsIndDef:
                self.dataItems[n] = gi.children[n]
            for n in self.paramsGenDef:
                self.dataItems[n] = gi.children[n]
        # read data from file if data items available
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
            if self.name in self.fileLoader.f[self.path].keys():
                grp = self.fileLoader.f[self.fullName]
            else:
                grp = self.fileLoader.f[self.path].create_group(self.name)
                self.fileLoader.reopenFile()
                self.fileLoader.addGroupPosterior(self.fullName)
                treeDirty = True
            for n,p in self.indParams.items():
                if n in grp:
                    ds = grp[n]
                    if ds.shape[0] != p.shape:
                        ds.resize(p.shape)
                    ds[:len(p)] = p[:]
                else:
                    ds = self.fileLoader.f[self.fullName].create_dataset(n,p.shape,maxshape=(None,),chunks=(10000,),data=self.indParams[n])
                    ds.attrs.modify("axes",["experiment_identifier"])
                    self.fileLoader.reopenFile()
                    self.fileLoader.addDatasetPosterior(self.fullName+"/"+n)
                    treeDirty = True
            for n,p in self.genParams.items():
                if n in grp:
                    ds = grp[n]
                    ds[0] = p
                else:
                    ds = self.fileLoader.f[self.fullName].create_dataset(n,(1,),data=p)
                    self.fileLoader.reopenFile()
                    self.fileLoader.addDatasetPosterior(self.fullName+"/"+n)
                    treeDirty = True
            self.paramsDirty = False
        # the following two lines lead to a crash and a corrupt file, I have no clue why
        if treeDirty:
            self.fileLoader.fileLoaderExtended.emit()



class ModelItem(AbstractParameterItem):
    def __init__(self,parentGroup,fileLoader):
        individualParamsDef = {"offCenterX":0.,"offCenterY":0.,"intensityMJUM2":1.,"diameterNM":100.,"maskRadius":100}
        generalParamsDef = {"photonWavelengthNM":1.,"detectorDistanceMM":1000.,"detectorPixelSizeUM":75.,"detectorQuantumEfficiency":1.,"detectorADUPhoton":10.,"materialType":"water","_visibility":0.5}
        name = "model"
        AbstractParameterItem.__init__(self,parentGroup,fileLoader,name,individualParamsDef,generalParamsDef)
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


class PattersonItem(AbstractParameterItem):
    def __init__(self,parentGroup,fileLoader):
        individualParamsDef = {"smooth":5.}
        generalParamsDef = {"_pattersonImg":-1}
        name = "patterson"
        AbstractParameterItem.__init__(self,parentGroup,fileLoader,name,individualParamsDef,generalParamsDef)
        self.patterson = None
        self.textureLoaded = False
    def calculatePatterson(self,img):
        PC = patterson.PattersonCreator(self.dataItemImage,self.dataItemMask)
        self.patterson = PC.patterson(img)
        self.setParams(img,{"_pattersonImg":img})
        self.textureLoaded = False




class TagsItem:
    def __init__(self,parent,fileLoader,path):
        self.parent = parent
        self.fileLoader = fileLoader
        self.path = path
        # Check for tags
        self.tags = []
        self.tagMembers = None
        self.tagsDirty = False

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
            self.fileLoader.reopenFile()
            self.fileLoader.addDatasetPosterior(self.path+"tags")
            self.fileLoader.fileLoaderExtended.emit()
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