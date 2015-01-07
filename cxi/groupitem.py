import h5py
import parameters
from dataitem import DataItem
from tagsitem import TagsItem

class GroupItem:
    def __init__(self,parent,fileLoader,fullName):
        self.parent = parent
        self.fileLoader = fileLoader
        self.fullName = fullName
        self.name = fullName.split("/")[-1]
        self.tagsItem = TagsItem(self,fileLoader,fullName+"/")
        self.children = {}
        H5Group = self.fileLoader[self.fullName]
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Group):
                self.children[k] = GroupItem(self,self.fileLoader,self.fullName+"/"+k)
        self.modelItem = parameters.ModelItem(self,self.fileLoader)
        self.pattersonItem = parameters.PattersonItem(self,self.fileLoader)
        for k in H5Group.keys():
            item = H5Group[k]
            if isinstance(item,h5py.Dataset):
                self.children[k] = DataItem(self,self.fileLoader,self.fullName+"/"+k)
