from PySide import QtGui, QtCore
import numpy
from IPython.core.debugger import Tracer

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
        Tracer()()
        # Is a tag dataset already existing
        if('tags' in self.fileLoader.f[self.path]):
            ds = self.fileLoader.f[self.path+"tags"]
            # MFH: I suspect that this corrupts the file somethimes. Therefore I just do a resize of the dataset instead if it already exists
            #del self.fileLoader.f[self.path+'tags']
            oldShape = ds.shape
            newShape = self.tagMembers.shape
            if (oldShape[0] != newShape[0]) or (oldShape[1] != newShape[1]):
                ds.resize(newShape)
            ds[:,:] = self.tagMembers[:,:]
        else:
            ds = self.fileLoader.f[self.path].create_dataset('tags',self.tagMembers.shape,maxshape=(None,None),chunks=(1,10000),data=self.tagMembers)
            ds.attrs.modify("axes",["tag:experiment_identifier"])
            self.fileLoader.reopenFile()
            ds = self.fileLoader.f[self.path+"tags"]
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
