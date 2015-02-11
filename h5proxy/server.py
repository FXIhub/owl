import h5py
import numpy
import cPickle as pickle
import sys


class Server(object):
    def __init__(self, interface="*", port=30572, heartbeat=None):
        self._socket = None
        if(interface):
            import zmq
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REP)
            self._socket.bind("tcp://"+interface+":"+str(port))
            self._heartbeat = heartbeat
            # maximum interval between hearbeats
            # corresponds to the socket timeout interval in miliseconds
            self._hbInterval = 10000
            self._ser = Serializer(self, self._socket)
            if(self._heartbeat):            
                self._socket.set(zmq.RCVTIMEO, self._hbInterval)
        self.files = {}
    def start(self):    
        print "Starting server"
        while(True):
            #  Wait for next request from client
            try:
                fc = self._ser.recv()
            except zmq.error.Again:
                raise RuntimeError('Did not receive heartbeat message in time. Aborting...')
                
            self.handleRPC(fc)


    def handleRPC(self, fc):
        # List of available RPC functions
        functions = dict(
            file_init = self.file_init, keys = self.keys, getitem = self.getitem,
            setitem = self.setitem, shape = self.shape, attrs = self.attrs,
            dtype = self.dtype, len = self.len, repr = self.repr, close = self.file_close,
            array = self.array, create_dataset = self.create_dataset,
            create_group = self.create_group, mode = self.mode, 
            contains = self.contains, values = self.values,
            items = self.items, get = self.get, modify = self.modify, resize = self.resize,
            read_direct = self.read_direct, astype = self.astype, size = self.size,
            maxshape = self.maxshape, chunks = self.chunks, compression = self.compression,
            compression_opts = self.compression_opts, scaleoffset = self.scaleoffset,
            shuffle = self.shuffle, fletcher32 = self.fletcher32, fillvalue = self.fillvalue,
            dims = self.dims, id = self.id, ref = self.ref, regionref = self.regionref,
            name = self.name, file = self.file, parent = self.parent, delitem = self.delitem,
            create = self.create, move = self.move, copy = self.copy, 
            require_group = self.require_group, require_dataset = self.require_dataset,
            flush = self.flush, filename = self.filename, driver = self.driver,
            libver = self.libver, userblock_size = self.userblock_size
        )
        # Get the function name to be called from the 'func' key
        fname = fc.pop('func')
        # Append eventual extra keyword arguments to the fc dictionary of arguments
        if 'kwds' in fc:
            kwds = fc.pop('kwds')
            for k in kwds.keys():
                fc[k] = kwds[k]
        try:
            if(fname not in functions):            
                raise RuntimeError("%s is not an available function",fname)
            # Do the actual function call with all the arguments
            if(fname == 'attrs'):
                if 'path' not in fc:
                    fc['path'] = None
                if(self._socket):
                    self._ser.send(functions[fname](**fc),fc['fileName'],fc['path'])
                else:
                    return functions[fname](**fc)
            else:
                if(self._socket):
                    self._ser.send(functions[fname](**fc))
                else:
                    return functions[fname](**fc)
        except:
            if(self._socket):
                ret = dict()
                ret['className'] = 'exception'
                ret['exc_type'] = sys.exc_type
                ret['exc_value'] = sys.exc_value
                self._ser.send(ret)
            else:
                raise
        return
         
    def resolve(self, fileName, path = None, attrs = None):
        if(attrs):
            if(path):
                return self.files[fileName][path].attrs
            else:
                return self.files[fileName].attrs
        else:
            if(path):
                return self.files[fileName][path]
            else:
                return self.files[fileName]                

    def file_init(self, fileName,mode,driver,libver,userblock_size,**kwds):
        f = h5py.File(fileName,mode,driver,libver,userblock_size,**kwds)
        self.files[f.file.filename] = f
        return f

    def create_dataset(self, fileName, path, name, shape, dtype, data, **kwds):
        return self.resolve(fileName,path).create_dataset(name,shape,dtype,data,**kwds)

    def create_group(self, fileName, path, name):
        return self.resolve(fileName,path).create_group(name)

    def file_close(self, fileName):
        return  self.resolve(fileName).close()

    def getitem(self, fileName, path, args, attrs = None):   
        return self.resolve(fileName,path, attrs)[args]

    def array(self, fileName, path, dtype):
        return numpy.array(self.resolve(fileName,path), dtype = dtype)

    def setitem(self, fileName, path, args, vals, attrs = None):
        self.resolve(fileName,path, attrs)[args] = vals
                
    def keys(self, fileName, path, attrs = None):
        return self.resolve(fileName,path, attrs).keys()
        
    def dtype(self,fileName,path):
        return self.resolve(fileName,path).dtype

    def shape(self,fileName,path):
        return self.resolve(fileName,path).shape

    def attrs(self,fileName,path):
        return self.resolve(fileName,path).attrs

    def len(self, fileName, path, attrs = None):
        return len(self.resolve(fileName,path,attrs))

    def repr(self, fileName, path, attrs = None):
        return repr(self.resolve(fileName,path,attrs))

    def mode(self,fileName):
        return self.resolve(fileName).mode

    def contains(self,fileName, path, name, attrs = None):
        return self.resolve(fileName, path, attrs).__contains__(name)

    def values(self,fileName, path, attrs=None):
        return self.resolve(fileName, path, attrs).values()

    def items(self,fileName, path, attrs = None):
        return self.resolve(fileName, path, attrs).items()

    def get(self,fileName, path, name, default, getclass, getlink, attrs = None):
        if(attrs):
            return self.resolve(fileName, path, attrs).get(name, default)
        else:
            return self.resolve(fileName, path, attrs).get(name, default, getclass, getlink)

    def modify(self,fileName, path, name, value, attrs = None):
        return self.resolve(fileName, path, attrs).modify(name, value)

    def resize(self,fileName, path, size, axis):
        return self.resolve(fileName, path).resize(size, axis)
            
    def read_direct(self, fileName, path, array, source_sel, dest_sel):
        return self.resolve(fileName, path).read_direct(array, source_sel, dest_sel)

    def astype(self, fileName, path, dtype):
        return self.resolve(fileName, path).astype(dtype)

    def size(self, fileName, path):
        return self.resolve(fileName, path).size

    def maxshape(self, fileName, path):
        return self.resolve(fileName, path).maxshape

    def chunks(self, fileName, path):
        return self.resolve(fileName, path).chunks

    def compression(self, fileName, path):
        return self.resolve(fileName, path).compression

    def compression_opts(self, fileName, path):
        return self.resolve(fileName, path).compression_opts

    def scaleoffset(self, fileName, path):
        return self.resolve(fileName, path).scaleoffset

    def shuffle(self, fileName, path):
        return self.resolve(fileName, path).shuffle

    def fletcher32(self, fileName, path):
        return self.resolve(fileName, path).fletcher32

    def fillvalue(self, fileName, path):
        return self.resolve(fileName, path).fillvalue

    def dims(self, fileName, path):
        return self.resolve(fileName, path).dims

    def id(self, fileName, path):
        return self.resolve(fileName, path).id

    def ref(self, fileName, path):
        return self.resolve(fileName, path).ref

    def regionref(self, fileName, path):
        return self.resolve(fileName, path).regionref

    def name(self, fileName, path):
        return self.resolve(fileName, path).name

    def file(self, fileName, path):
        return self.resolve(fileName, path).file

    def parent(self, fileName, path):
        return self.resolve(fileName, path).parent

    def delitem(self, fileName, path, name, attrs=None):
        return self.resolve(fileName, path, attrs).__delitem__(name)

    def create(self, fileName, path, name, data, shape, dtype, attrs = None):
        return self.resolve(fileName, path, attrs).create(name, data, shape, dtype)

    def move(self, fileName, path, source, dest):
        return self.resolve(fileName, path).move(source, dest)

    def copy(self, fileName, path, source, dest, name, shallow, expand_soft, expand_external, expand_refs, without_attrs):
        return self.resolve(fileName, path).copy(source, dest, name, shallow, expand_soft, expand_external, expand_refs, without_attrs)
        
    def require_group(self, fileName, path, name):
        return self.resolve(fileName,path).require_group(name)

    def require_dataset(self, fileName, path, name, shape, dtype, exact, **kwds):
        return self.resolve(fileName,path).require_dataset(name, shape, dtype, exact, **kwds)

    def flush(self, fileName):
        return self.resolve(fileName).flush()

    def filename(self, fileName):
        return self.resolve(fileName).filename()
        
    def driver(self, fileName):
        return self.resolve(fileName).driver()

    def libver(self, fileName):
        return self.resolve(fileName).libver()

    def userblock_size(self, fileName):
        return self.resolve(fileName).userblock_size()

from .h5proxy import Dataset,Group,File,Attributes 
from .serializer import Serializer
