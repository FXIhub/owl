
class Base(object):
    def __init__(self, client, fileName, path):
        self._client = client
        self._fileName = fileName
        self._path = path
    def __getitem__(self, args):
        return self._client.call('getitem', fileName=self._fileName, path=self._path, args=args)
    def __setitem__(self, args, vals):
        return self._client.call('setitem', fileName=self._fileName, path=self._path, args=args, vals=vals)
    def __len__(self):
        return self._client.call('len', fileName=self._fileName, path=self._path)
    def __repr__(self):
        return self._client.call('repr', fileName=self._fileName, path=self._path)
    @property
    def attrs(self):
        return self._client.call('attrs', fileName=self._fileName, path=self._path)

class Group(Base):
    def __iter__(self):
        for x in self.keys():
            yield x
    def __contains__(self, name):
        return self._client.call('contains', fileName=self._fileName, path=self._path, name=name)
    # __getitem__ from parent
    # __settitem__ from parent
    def keys(self):
        return self._client.call('keys', fileName=self._fileName, path=self._path)
    def values(self):
        return self._client.call('values', fileName=self._fileName, path=self._path)
    def items(self):
        return self._client.call('items', fileName=self._fileName, path=self._path)
    def iterkeys(self):
        return iter(self)
    def itervalues(self):
        for x in self.keys():
            yield self[x]
    def iteritems(self):
        for x in self.keys():
            yield (x,self[x])
    def get(self, name, default=None, getclass=False, getlink=False):
        return self._client.call('get', fileName=self._fileName, path=self._path, name=name, default=default, getclass=getclass, getlink=getlink)
    # visit NOT implemented
    # visititems NOT implemented
    def move(self, source, dest):
        return self._client.call('move', fileName=self._fileName, path=self._path, source=source, dest=dest)
    def copy(self, source, dest, name=None, shallow=False, expand_soft=False, expand_external=False, expand_refs=False, without_attrs=False):
        return self._client.call('copy', fileName=self._fileName, path=self._path, source=source, dest=dest, name=name, shallow=shallow,
                                 expand_soft=expand_soft, expand_external=expand_external, expand_refs=expand_refs, without_attrs=without_attrs)
    def create_group(self, name):
        return self._client.call('create_group', fileName=self._fileName, path=self._path, name=name)
    def require_group(self, name):
        return self._client.call('require_group', fileName=self._fileName, path=self._path, name=name)
    def create_dataset(self, name, shape=None, dtype=None, data=None, **kwds):
        return self._client.call('create_dataset', fileName=self._fileName, path=self._path, name=name,shape=shape,dtype=dtype,data=data,**kwds)
    def require_dataset(self, name, shape=None, dtype=None, exact=None, **kwds):
        return self._client.call('require_dataset', fileName=self._fileName, path=self._path, name=name,shape=shape,dtype=dtype,exact=exact,**kwds)
    # attrs from parent
    @property
    def id(self):
       return self._client.call('id',fileName=self._fileName, path=self._path)
    @property
    def ref(self):
       return self._client.call('ref',fileName=self._fileName, path=self._path)
    @property
    def regionref(self):
       return self._client.call('regionref',fileName=self._fileName, path=self._path)
    @property
    def name(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)
    @property
    def file(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)
    @property
    def parent(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)


class Attributes(object):
    def __init__(self, client, fileName, path):
        self._client = client
        self._fileName = fileName
        self._path = path

    def __len__(self):
        return self._client.call('len', fileName=self._fileName, path=self._path, attrs=True)
    def __repr__(self):
        return self._client.call('repr', fileName=self._fileName, path=self._path, attrs=True)

    
    def __iter__(self):
        for x in self.keys():
            yield x
    def __contains__(self, name):
        return self._client.call('contains', fileName=self._fileName, path=self._path, name=name, attrs=True)
    def __getitem__(self, args):
        return self._client.call('getitem', fileName=self._fileName, path=self._path, args=args, attrs=True)
    def __setitem__(self, args, vals):
        return self._client.call('setitem', fileName=self._fileName, path=self._path, args=args, vals=vals, attrs=True)
    def __delitem__(self, name):
        return self._client.call('delitem', fileName=self._fileName, path=self._path, name=name, attrs=True)
    def keys(self):
        return self._client.call('keys', fileName=self._fileName, path=self._path, attrs=True)
    def values(self):
        return self._client.call('values', fileName=self._fileName, path=self._path, attrs=True)
    def items(self):
        return self._client.call('items', fileName=self._fileName, path=self._path, attrs=True)
    def iterkeys(self):
        return iter(self)
    def itervalues(self):
        for x in self.keys():
            yield self[x]
    def iteritems(self):
        for x in self.keys():
            yield (x,self[x])
    def get(self, name, default=None, getclass=False, getlink=False):
        return self._client.call('get', fileName=self._fileName, path=self._path, name=name, default=default,
                                 getclass=getclass, getlink=getlink, attrs=True)
    def create(self, name, data, shape=None, dtype=None):
        return self._client.call('create', fileName=self._fileName, path=self._path, name=name, data=data, shape=shape, dtype=dtype, attrs=True)
    def modify(self, name, value):
        return self._client.call('modify', fileName=self._fileName, path=self._path, name=name, value=value, attrs=True)

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
        self._client.call('close', fileName=self._fileName)
    def flush(self):
        self._client.call('flush', fileName=self._fileName)
    # id from parent
    @property    
    def filename(self):
        self._client.call('filename', fileName=self._fileName)        
    @property
    def mode(self):
        return self._client.call('mode', fileName=self._fileName)
    @property
    def driver(self):
        return self._client.call('driver', fileName=self._fileName)
    @property
    def libver(self):
        return self._client.call('libver', fileName=self._fileName)
    @property
    def userblock_size(self):
        return self._client.call('userblock_size', fileName=self._fileName)

        
class Dataset(Base):
    def __array__(self,dtype=None):
        return self._client.call('array', fileName=self._fileName, path=self._path, dtype=dtype)

    def read_direct(self, array, source_sel=None, dest_sel=None):
        return self._client.call('read_direct', fileName=self._fileName, path=self._path, array=array, source_sel=source_sel, dest_sel=dest_sel)

    def astype(self, dtype):
        return self._client.call('astype', fileName=self._fileName, path=self._path, dtype=dtype)
        
    def resize(self, size, axis=None):
        return self._client.call('resize', fileName=self._fileName, path=self._path, size=size, axis=axis)

    @property
    def shape(self):
        return self._client.call('shape',fileName=self._fileName, path=self._path)

    @property
    def dtype(self):
        return self._client.call('dtype',fileName=self._fileName, path=self._path)

    @property
    def size(self):
       return self._client.call('size',fileName=self._fileName, path=self._path)

    @property
    def maxshape(self):
       return self._client.call('maxshape',fileName=self._fileName, path=self._path)

    @property
    def chunks(self):
       return self._client.call('chunks',fileName=self._fileName, path=self._path)

    @property
    def compression(self):
       return self._client.call('compression',fileName=self._fileName, path=self._path)

    @property
    def compression_opts(self):
       return self._client.call('compression_opts',fileName=self._fileName, path=self._path)

    @property
    def scaleoffset(self):
       return self._client.call('scaleoffset',fileName=self._fileName, path=self._path)

    @property
    def shuffle(self):
       return self._client.call('shuffle',fileName=self._fileName, path=self._path)

    @property
    def fletcher32(self):
       return self._client.call('fletcher32',fileName=self._fileName, path=self._path)

    @property
    def fillvalue(self):
       return self._client.call('fillvalue',fileName=self._fileName, path=self._path)

    @property
    def dims(self):
       return self._client.call('fillvalue',fileName=self._fileName, path=self._path)
    @property
    def id(self):
       return self._client.call('id',fileName=self._fileName, path=self._path)

    @property
    def ref(self):
       return self._client.call('ref',fileName=self._fileName, path=self._path)

    @property
    def regionref(self):
       return self._client.call('regionref',fileName=self._fileName, path=self._path)

    @property
    def name(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)

    @property
    def file(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)

    @property
    def parent(self):
       return self._client.call('name',fileName=self._fileName, path=self._path)

    
class HardLink(object):
    pass
    
class SoftLink(object):
    def __init__(self, path):
        self._path = str(path)
    @property
    def path(self):
        return self._path
    def __repr__(self):
        return '<SoftLink to "%s">' % self.path

class ExternalLink(object):
    def __init__(self, filename, path):
        self._filename = str(filename)
        self._path = str(path)
    @property
    def filename(self):
        return self._filename
    @property
    def path(self):
        return self._path
    def __repr__(self):
        return '<ExternalLink to "%s" in file "%s"' % (self.path, self.filename)

from .client import Client
from .server import Server
        
