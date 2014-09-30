from PySide import QtGui, QtCore
import numpy
import h5py
import settingsOwl
import dataloader
import groupitem

class FileLoader(QtCore.QObject):
    stackSizeChanged = QtCore.Signal(int)
    fileLoaderExtended = QtCore.Signal()
    def __init__(self,parent):
        QtCore.QObject.__init__(self)
        self.parent = parent
        self.f = None
        self.stackSize = None
        self.mode = parent.settings.value("fileMode")
    def openFile(self,fullFilename,mode0=None):
        if mode0 != None:
            self.mode = mode0
        mode = self.mode
        if mode == "r*" and not settingsOwl.swmrSupported:
            return 1
        if isinstance(self.f,h5py.File):
            self.f.close()
        try:
            self.f = h5py.File(fullFilename,mode)#,libver='latest')
            return 0
        except IOError as e:            
            if( str(e) == 'Unable to open file (File is already open for write or swmr write)'):                                
                print "\n\n!!! TIP: Trying running h5clearsb.py on the file !!!\n\n"
            raise
            return 2
        print self.f
    def reopenFile(self):
        # IMPORTANT NOTE:
        # Reopening the file is required after groups (/ datasets?) are created, otherwise we corrupt the file.
        # As we have to do this from time to time never rely on direct pointers to HDF5 datatsets. 
        # You better access data only via the HDF5 file object fileLoader.f[datasetname].
        if self.mode == "r*":
            self.parent.updateTimer.start()
        elif self.mode == "r+":
            self.parent.updateTimer.stop()
        return self.openFile(self.fullFilename,self.mode)
    def loadFile(self,fullFilename):
        self.f = None
        err =  self.openFile(fullFilename)
        if err == 1:
            print "Cannot open file. SWMR mode not supported by your h5py version. Please change file mode in the file menue and try again."
            return
        self.fullFilename = fullFilename
        self.filename = QtCore.QFileInfo(fullFilename).fileName()
        self.fullName = self.name = "/"
        self.tagsItem = None
        self.modelItem = None
        self.pattersonItem = None
        self.dataItems = {}
        self.groupItems = {}
        self.tagsItems = {}
        self.modelItems = {}
        self.pattersonItems = {}
        self.children = {}
        H5Group = self.f[self.fullName]
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = dataloader.DataItem(self,self,"/"+k)
            elif isinstance(item,h5py.Group):
                self.children[k] = groupitem.GroupItem(self,self,"/"+k)
        self.collectItems(self.children)
        self.stackSize = None
    def collectItems(self,item):
        for k in item.keys():
            child = item[k]
            if isinstance(child,dataloader.DataItem):
                self.dataItems[child.fullName] = child
            elif isinstance(child,groupitem.GroupItem):
                self.groupItems[child.fullName] = child
                self.tagsItems[child.fullName] = child.tagsItem
                self.modelItems[child.fullName] = child.modelItem
                self.pattersonItems[child.fullName] = child.pattersonItem
                self.collectItems(child.children)
            else:
                print "no valid item."
    def addGroupPosterior(self,name0):
        name = name0
        if name[-1] == "/": name = name[:-1]
        path = name[0:name.rindex('/')]

        def addGroupRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    g = groupitem.GroupItem(c,self,name)
                    c.children[name[name.rindex('/')+1:]] = g
                    self.groupItems[name] = g
                    self.modelItems[name] = g.modelItem
                    self.pattersonItems[name] = g.pattersonItem
                    #print "add group",self.groupItems.keys(),name0
                elif isinstance(c,groupitem.GroupItem):                  
                    addGroupRecursively(c,c.children)

        addGroupRecursively(self,self.children)
    def addDatasetPosterior(self,name0):
        name = name0
        path = name[0:name.rindex('/')]

        def addDatasetRecursively(group,children):
            for n,c in children.items():
                if c.fullName == path:
                    d = dataloader.DataItem(group,self,"/"+name)
                    c.children[name[name.rindex('/')+1:]] = d
                    self.dataItems[name] = d
                elif isinstance(c,groupitem.GroupItem):                  
                    addDatasetRecursively(c,c.children)

        addDatasetRecursively(self,self.children)
    def updateStackSize(self):
        #print "update"
        if self.f == None:
            return
        N = []
        for n,d in self.dataItems.items():
            if d.isSelectedStack:
                if "numEvents" in self.f[n].attrs.keys():
                    ## if not self.f.mode == "r+": # self.f.mode == None if opened in swmr mode. This is odd.
                    if self.f.mode == "r*": # This is to fix issues in r and r+ mode, does it also work with smwe now?
                        self.f[n].refresh()
                    N.append(self.f[n].attrs.get("numEvents")[0])
                    #print n,N
                else:
                    N.append(self.f[n].shape[d.stackDim])
        if len(N) > 0:
            N = numpy.array(N).min()
        else:
            N = None
        if N != self.stackSize:
            self.stackSize = N
            self.stackSizeChanged.emit(N)
    def ensureReadWriteModeActivated(self):
        if self.f.mode == "r+":
            return 0
        else:
            accepted = QtGui.QMessageBox.question(self.parent,"Change to read-write mode?",
                                                  "The file is currently opened in SWMR mode. Data can "+
                                                  "not be written to file in this mode. Do you like to reopen the file in read-write mode?",
                                                  QtGui.QMessageBox.Ok,QtGui.QMessageBox.Cancel) == QtGui.QMessageBox.Ok
            if accepted:
                self.mode = "r+"
                self.reopenFile()
                return 0
        return 1
    def saveTags(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,t in self.tagsItems.items():
                t.saveTags()
    def modelsChanged(self):
        if self.f == None:
            return
        for n,m in self.modelItems.items():
            if m.paramsDirty:
                return True
        return False
    def pattersonsChanged(self):
        if self.f == None:
            return
        for n,p in self.pattersonItems.items():
            if p.paramsDirty:
                return True
        return False
    def saveModels(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,m in self.modelItems.items():
                m.saveParams()
    def savePattersons(self):
        if self.f == None:
            return
        if 0 ==  self.ensureReadWriteModeActivated():
            for n,m in self.pattersonItems.items():
                m.saveParams()
