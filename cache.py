from collections import OrderedDict
from threading import Lock
import logging

class Cache:
    # Zero or negative values for size will create an unlimited cache
    def __init__(self,size=100):
        self.maxSize = size
        self.dict = OrderedDict()
        self.lock = Lock()
        self.logger = logging.getLogger("Cache")
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)        

    def __getitem__(self,key):
        return self.touch(key)

    def __setitem__(self,key,value):
        with self.lock:
            if(self.maxSize > 0):
                while len(self.dict) >= self.maxSize:
                    (k,v) = self.dict.popitem(last=False) # FIFO pop
                    self.logger.debug("Removing %d from cache" % k)
            self.dict[key]=value

    def __delitem__(self,key):
        with self.lock:
            del self.dict[key]

    def keys(self):
        with self.lock:
            return self.dict.keys()

    def touch(self,key):
        with self.lock:
            # This curious code just puts the item at
            # the end of the OrderedDict to enforce the
            # LRO caching algorithm
            retval = self.dict.pop(key)
            self.dict[key] = retval
            return retval

    

class ArrayCache(Cache):
    # Default size is 10 MB
    def __init__(self,sizeInBytes=1024*1024*10):
        Cache.__init__(self)
        self.itemSize = None
        self.sizeInBytes = sizeInBytes
    def __setitem__(self,key,value):
        if(self.itemSize is None):
            self.itemSize = value.nbytes
            size = self.sizeInBytes/self.itemSize
            self.maxSize = size
            self.logger.debug("Setting cache size to %d" % size)
        Cache.__setitem__(self,key,value)
