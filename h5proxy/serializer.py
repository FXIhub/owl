import numpy
import h5py
import cPickle as pickle


class Serializer(object):
    def __init__(self, parent, socket = None):
        self._parent = parent
        self._socket = socket
        if(socket):
            import threading

            self.lock = threading.Lock()
        else:
            # Use an internal server is there's no socket
            self._server = Server(None)
            

    def call(self, data):
        if(self._socket):
            with self.lock:
                self.send(data)
                return self.recv()
        else:
            if(data['func'] == 'attrs'):
                ret, _ = self._serialize(self._server.handleRPC(data),[],data['fileName'],data['path'])
                return self._deserialize(ret)
            else:
                ret, _ = self._serialize(self._server.handleRPC(data),[],None,None)
                return self._deserialize(ret)

    def recv(self):
        data = pickle.loads(self._socket.recv())
        ret = self._deserialize(data)
        return ret
        

    def _deserialize(self, data):
        if(isinstance(data, dict)):
            if('className' in data):
                if(data['className'] == "Dataset"):
                    data = Dataset(self._parent, data['fileName'], data['path'])
                elif(data['className'] == "Group"):
                    data = Group(self._parent, data['fileName'], data['path'])
                elif(data['className'] == "Attributes"):
                    data = Attributes(self._parent, data['fileName'], data['path'])
                elif(data['className'] == "exception"):
                    exc_type = data['exc_type']
                    exc_value = data['exc_value']
                    raise exc_type(exc_value)
                elif(data['className'] == "ndarray" and self._socket):
                    d = self._socket.recv()
                    data = numpy.frombuffer(buffer(d), dtype=data['dtype']).reshape(data['shape'])
                elif(data['className'] == "File"):
                    pass
                else:
                    raise RuntimeError('Unknown class: %s' % data['className'])
            else:
                # We need to sort to be able to receive any possible arrays
                # in the correct order
                for k in sorted(data.keys()):
                    data[k] = self._deserialize(data[k])
        elif isinstance(data, list) or isinstance(data, tuple):
            ldata = [None]*len(data)
            for i in range(len(data)):
                ldata[i] = self._deserialize(data[i])
            data = type(data)(ldata)
        return data


    def send(self,data, fileName = None, path = None):
        data, arrays = self._serialize(data, [], fileName, path)
        flags = 0
        if(len(arrays)):
            import zmq
            flags = zmq.SNDMORE
        self._socket.send(pickle.dumps(data), flags)

        for i in range(len(arrays)):
            # When sending the last array change the flag back
            if(i == len(arrays) -1):
                flags = 0
            self._socket.send(arrays[i], flags)            

    def _serialize(self, data, arrays, fileName, path):
        if type(data) is h5py.Dataset:
            data = dict(
                className = "Dataset",
                fileName = data.file.filename,
                path = data.name
            )
        elif type(data) is h5py.Group:
            data = dict(
                className = "Group",
                fileName = data.file.filename,
                path = data.name
            )
        elif type(data) is h5py.AttributeManager:
            data = dict(
                className = "Attributes",
                fileName = fileName,
                path = path,
            )
        elif type(data) is h5py.File:
            data = dict(
                className = "File",
                fileName = data.file.filename,
                path = ''
            )
        elif isinstance(data, numpy.ndarray) and self._socket:
            arrays.append(data)
            data = dict(
                className = "ndarray",
                dtype = data.dtype,
                shape = data.shape
            )
        elif isinstance(data, dict):
            # We need to sort to be able to receive any possible arrays
            # in the correct order
            for k in sorted(data.keys()):
                data[k], arrays = self._serialize(data[k], arrays, fileName, path)
        elif isinstance(data, list) or isinstance(data, tuple):
            ldata = [None]*len(data)
            for i in range(len(data)):
                ldata[i], arrays = self._serialize(data[i], arrays, fileName, path)
            data = type(data)(ldata)
        return data, arrays

from .h5proxy import Dataset,Group,File,Attributes 
from .server import Server
