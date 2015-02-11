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

    def call(self, func, **kwds):
        args = dict(
            func = func
        )
        for k in kwds.keys():
            args[k] = kwds[k]
        return self._ser.call(args)        
        
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

from .serializer import Serializer
