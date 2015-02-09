
class Base(object):
    def __init__(self, client, fileName, path):
        self._client = client
        self._fileName = fileName
        self._path = path
    def __getitem__(self, args):
        return self._client.getitem(self._fileName, self._path, args)
    def __setitem__(self, args, vals):
        return self._client.setitem(self._fileName, self._path, args, vals)
    def __len__(self):
        return self._client.len(self._fileName, self._path)
    def __repr__(self):
        return self._client.repr(self._fileName, self._path)
    @property
    def attrs(self):
        return self._client.attrs(self._fileName, self._path)

class Group(Base):
    def create_group(self, name):
        return self._client.create_group(self._fileName,self._path,name)

    def create_dataset(self, name, shape=None, dtype=None, data=None, **kwds):
        return self._client.create_dataset(self._fileName, self._path, name,shape,dtype,data,**kwds)

    def keys(self):
        return self._client.keys(self._fileName, self._path)

    def __contains__(self, name):
        return self._client.contains(self._fileName, self._path, name)

    def values(self):
        return self._client.values(self._fileName, self._path)

    def items(self):
        return self._client.items(self._fileName, self._path)

    def __iter__(self):
        for x in self.keys():
            yield x

    def iterkeys(self):
        return iter(self)

    def itervalues(self):
        for x in self.keys():
            yield self[x]

    def iteritems(self):
        for x in self.keys():
            yield (x,self[x])

    def get(self, name, default=None, getclass=False, getlink=False):
        return self._client.get(self._fileName, self._path, name, default, getclass, getlink)




class Attributes(Base):
    def keys(self):
        return self._client.keys(self._fileName, self._path,True)
    def __getitem__(self, args):
        return self._client.getitem(self._fileName, self._path, args, True)
    def __setitem__(self, args, vals):
        return self._client.setitem(self._fileName, self._path, args, vals, True)
    def __len__(self):
        return self._client.len(self._fileName, self._path, True)
    def __repr__(self):
        return self._client.repr(self._fileName, self._path, True)
    def items(self):
        return self._client.items(self._fileName, self._path, True)
    def get(self, name, default=None, getclass=False, getlink=False):
        return self._client.get(self._fileName, self._path, name, default, getclass, getlink, True)
    def modify(self, name, value):
        return self._client.modify(self._fileName, self._path, name, value, True)
    



class File(Group):
    def __init__(self, locator, mode=None, driver=None, libver=None, userblock_size=None, **kwds):
        host,port,name = self._parseLocator(locator)
        self._client = Client(host,port)
        ret = self._client.file_init(fileName=name, mode=mode, driver=driver, libver=libver, userblock_size=userblock_size, **kwds)
        self._fileName = ret['fileName']
        self._path = ret['path']

    def _parseLocator(self, name):
        # Search for the end of the host field
        i = name.find(':')
        if(i == -1):
            return "","", name
        else:
            # Search for a possible port field
            j = name[i+1:].find(':')
            if(j == -1):
                return name[:i], 30572, name[i+1:]
            else:
                return name[:i], int(name[i+1:i+j+1]), name[i+j+2:]
    def close(self):
        self._client.close(self._fileName)
    @property
    def mode(self):
        return self._client.mode(self._fileName)

        
class Dataset(Base):
    @property
    def dtype(self):
        return self._client.dtype(self._fileName, self._path)
    @property
    def shape(self):
        return self._client.shape(self._fileName, self._path)

    def __array__(self,dtype=None):
        return self._client.array(self._fileName, self._path, dtype)

    def resize(self, size, axis=None):
        return self._client.resize(self._fileName, self._path, size, axis)

    
from .client import Client
from .server import Server
        
