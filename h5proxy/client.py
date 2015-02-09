class Client(object):
    def __init__(self, host, port):
        if(host):
            import zmq
            self._context = zmq.Context()
            self._socket = self._context.socket(zmq.REQ)
            self._socket.connect("tcp://"+host+":"+str(port))
            self._ser = Serializer(self, self._socket)
        else:
            self._ser = Serializer(self)
        
    def file_init(self, fileName,mode,driver,libver,userblock_size,**kwds):
        args = dict(
            func = "file_init",
            fileName = fileName,
            mode = mode,
            driver = driver,
            libver = libver,
            userblock_size = userblock_size,
            kwds = kwds
        )
        return self._ser.call(args)
   
    def create_dataset(self, fileName, path, name, shape, dtype, data, **kwds):
        args = dict(
            func = "create_dataset",
            fileName = fileName,
            path = path,
            name = name,
            shape = shape,
            dtype = dtype,
            data = data,
            kwds = kwds
        )
        return self._ser.call(args)

    def create_group(self, fileName, path, groupName):
        args = dict(
            func = "create_group",
            fileName = fileName,
            path = path,
            groupName = groupName
        )
        return self._ser.call(args)

    def close(self, fileName):
        args = dict(
            func = "close",
            fileName = fileName
        )
        return self._ser.call(args)

    def keys(self, fileName, path, attrs = False):
        args = dict(
            func = "keys",
            fileName = fileName,
            path = path,
            attrs = attrs
        )
        return self._ser.call(args)

    def getitem(self, fileName, path, fargs, attrs = False):
        args = dict(
            func = "getitem",
            fileName = fileName,
            path = path,
            args = fargs,
            attrs = attrs
        )
        return self._ser.call(args)

    def setitem(self, fileName, path, fargs, vals, attrs = False):
        args = dict(
            func = "setitem",
            fileName = fileName,
            path = path,
            args = fargs,
            vals = vals,
            attrs = attrs
        )
        return self._ser.call(args)

    def shape(self, fileName, path):
        args = dict(
            func = "shape",
            fileName = fileName,
            path = path
        )
        return self._ser.call(args)

    def len(self, fileName, path, attrs = False):
        args = dict(
            func = "len",
            fileName = fileName,
            path = path,
            attrs = attrs
        )
        return self._ser.call(args)

    def repr(self, fileName, path, attrs = False):
        args = dict(
            func = "repr",
            fileName = fileName,
            path = path,
            attrs = attrs
        )
        return self._ser.call(args)

    def dtype(self, fileName, path):
        args = dict(
            func = "dtype",
            fileName = fileName,
            path = path
        )
        return self._ser.call(args)

    def attrs(self, fileName, path):
        args = dict(
            func = "attrs",
            fileName = fileName,
            path = path
        )
        return self._ser.call(args)

    def array(self, fileName, path, dtype):
        args = dict(
            func = "array",
            fileName = fileName,
            path = path,
            dtype = dtype
        )
        return self._ser.call(args)

    def mode(self, fileName):
        args = dict(
            func = "mode",
            fileName = fileName
        )
        return self._ser.call(args)

    def contains(self, fileName, path, name):
        args = dict(
            func = "contains",
            fileName = fileName,
            path = path,
            name = name
        )
        return self._ser.call(args)

    def values(self, fileName, path):
        args = dict(
            func = "values",
            fileName = fileName,
            path = path
        )
        return self._ser.call(args)

    def items(self, fileName, path, attrs = False):
        args = dict(
            func = "items",
            fileName = fileName,
            path = path,
            attrs = attrs
        )
        return self._ser.call(args)

    def get(self, fileName, path, name, default=None, getclass=False, getlink=False, attrs = False):
        args = dict(
            func = "get",
            fileName = fileName,
            path = path,
            name = name,
            default = default,
            getclass = getclass,
            getlink = getlink,
            attrs = attrs
        )
        return self._ser.call(args)

    def modify(self, fileName, path, name, value, attrs = False):
        args = dict(
            func = "modify",
            fileName = fileName,
            path = path,
            name = name,
            value = value,
            attrs = attrs
        )
        return self._ser.call(args)

    def resize(self, fileName, path, size, axis):
        args = dict(
            func = "resize",
            fileName = fileName,
            path = path,
            size = size,
            axis = axis
        )
        return self._ser.call(args)


from .serializer import Serializer
