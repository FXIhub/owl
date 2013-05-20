from collections import OrderedDict
from threading import RLock
import logging
from OpenGL.GL import *
from OpenGL.GLU import *


class Cache:
    # Zero or negative values for size will create an unlimited cache
    def __init__(self,size=100):
        self.maxSize = size
        self.dict = OrderedDict()
        self.lock = RLock()
        self.logger = logging.getLogger("Cache")
        self.logger.setLevel(logging.DEBUG)        
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)        

    def __getitem__(self,key):
        with self.lock:
            # This curious code just puts the item at
            # the end of the OrderedDict to enforce the
            # LRO caching algorithm
            retval = self.dict.pop(key)
            self.dict[key] = retval
            return retval

    def __setitem__(self,key,value):
        with self.lock:
            self.trim()
            self.dict[key] = value

    def __delitem__(self,key):
        with self.lock:
            del self.dict[key]

    def __contains__(self,key):
        return self.dict.__contains__(key)
            
    def values(self):
        return self.dict.values()

    def keys(self):
        return self.dict.keys()
            
    def touch(self,key):
        self.__getitem__(key)
        
    def setMaxSize(self,size):
        self.maxSize = size        
        self.trim()
    
    def trim(self):
        with self.lock:
            if(self.maxSize > 0):
                while len(self.dict) >= self.maxSize:
                    (k,v) = self.dict.popitem(last=False) # FIFO pop
                    self.logger.debug("Removing %d from cache" % k)

    

class ArrayCache(Cache):
    # Default size is 10 MB
    def __init__(self, sizeInBytes=1024*1024*10):
        Cache.__init__(self)
        self.itemSize = None
        self.sizeInBytes = int(sizeInBytes)
    def __setitem__(self,key,value):
        if(self.itemSize is None and value is not None):
            self.itemSize = int(value.nbytes)
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting ArrayCache size to %d" % size)
        Cache.__setitem__(self,key,value)
    def setSizeInBytes(self,size):
        self.sizeInBytes = size
        if(self.itemSize is not None):
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting ArrayCache size to %d" % size)


class GLCache(Cache):
    # Default size is 10 MB
    def __init__(self,sizeInBytes=1024*1024*10):
        Cache.__init__(self)
        self.itemSize = None
        self.sizeInBytes = sizeInBytes
    def __setitem__(self,key,texture):
        if(self.itemSize is None):
            glBindTexture(GL_TEXTURE_2D, texture)
            foo = 0
            width = glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_WIDTH)
            height = glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_HEIGHT)
            format = glGetTexLevelParameteriv(GL_TEXTURE_2D,0,GL_TEXTURE_INTERNAL_FORMAT)
            if(format == OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB):
                bytes_per_pixel = 4
            else:
                bytes_per_pixel = 4
                self.logger.warning("Unsupported GL Texture Format %s" % format)
            self.itemSize = width*height*bytes_per_pixel
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)            
            self.logger.warning("Setting GLCache size to %d" % size)
        Cache.__setitem__(self,key,texture)
    def trim(self):
        with self.lock:
            if(self.maxSize > 0):
                while len(self.dict) >= self.maxSize:
                    (k,v) = self.dict.popitem(last=False) # FIFO pop
                    self.logger.warning("Texture %d , %s to be removed is %s" % (k, str(v), str(glIsTexture(v))))
                    glDeleteTextures(v)
                    self.logger.debug("Removing %d from GLCache" % k)

    def setSizeInBytes(self,size):
        self.sizeInBytes = size
        if(self.itemSize is not None):
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting GLCache size to %d" % size)
