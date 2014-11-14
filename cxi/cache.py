"""Handles the caching of OpenGL textures and numpy arrays"""
from collections import OrderedDict
from threading import RLock
import logging
from OpenGL import GL
import OpenGL.GL.ARB.texture_float

class Cache(object):
    """Base caching class

    It uses a least recently used (LRU) algorithm to determine which
    entries to delete when the cache gets filled.
    """
    def __init__(self, size=100):
        """Zero or negative values for size will create an unlimited cache"""
        self.maxSize = size
        self.dict = OrderedDict()
        self.lock = RLock()
        self.logger = logging.getLogger("Cache")
        self.logger.setLevel(logging.DEBUG)
        # If you want to see debug messages change level here
        self.logger.setLevel(logging.WARNING)

    def __getitem__(self, key):
        with self.lock:
            # This curious code just puts the item at
            # the end of the OrderedDict to enforce the
            # LRU caching algorithm
            retval = self.dict.pop(key)
            self.dict[key] = retval
            return retval

    def __setitem__(self, key, value):
        with self.lock:
            self._trim()
            self.dict[key] = value

    def __delitem__(self, key):
        with self.lock:
            del self.dict[key]

    def __contains__(self, key):
        return self.dict.__contains__(key)

    def values(self):
        """Returns all the cached values"""
        return self.dict.values()

    def keys(self):
        """Returns the keys of all the cached values"""
        return self.dict.keys()

    def touch(self, key):
        """Accesses a cached item so it will not be removed from the cache"""
        self.__getitem__(key)

    def setMaxSize(self, size):
        """Sets the maximum size of the cache and removes any elements that do not fit"""
        self.maxSize = size
        self._trim()

    def _trim(self):
        """Remove elements that exceed the maximum cache size"""
        with self.lock:
            if(self.maxSize > 0):
                while len(self.dict) >= self.maxSize:
                    (k, _) = self.dict.popitem(last=False) # FIFO pop
                    self.logger.debug("Removing %d from cache", k)



class ArrayCache(Cache):
    """Numpy array caching class

    Defaults to a 10 MB cache
    """
    # Default size is 10 MB
    def __init__(self, sizeInBytes=1024*1024*10):
        Cache.__init__(self)
        self.itemSize = None
        self.sizeInBytes = int(sizeInBytes)
    def __setitem__(self, key, value):
        if(self.itemSize is None and value is not None):
            self.itemSize = int(value.nbytes)
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting ArrayCache size to %d", size)
        Cache.__setitem__(self, key, value)
    def setSizeInBytes(self, size):
        """Sets the maximum size of the cache in bytes and trims excess elements"""
        self.sizeInBytes = size
        if(self.itemSize is not None):
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting ArrayCache size to %d", size)


class GLCache(Cache):
    """OpenGL texture caching class

    Defaults to a 10 MB cache
    """
    # Default size is 10 MB
    def __init__(self, sizeInBytes=1024*1024*10):
        Cache.__init__(self)
        self.itemSize = None
        self.sizeInBytes = sizeInBytes
    def __setitem__(self, key, texture):
        if(self.itemSize is None):
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            width = GL.glGetTexLevelParameteriv(GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_WIDTH)
            height = GL.glGetTexLevelParameteriv(GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_HEIGHT)
            internalFormat = GL.glGetTexLevelParameteriv(GL.GL_TEXTURE_2D, 0, GL.GL_TEXTURE_INTERNAL_FORMAT)
            if(internalFormat == OpenGL.GL.ARB.texture_float.GL_ALPHA32F_ARB):
                bytes_per_pixel = 4
            else:
                bytes_per_pixel = 4
                self.logger.warning("Unsupported GL Texture Format %s",
                                    internalFormat)
            self.itemSize = width*height*bytes_per_pixel
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting GLCache size to %d", size)
        Cache.__setitem__(self, key, texture)
    def _trim(self):
        with self.lock:
            if(self.maxSize > 0):
                while len(self.dict) >= self.maxSize:
                    (k, v) = self.dict.popitem(last=False) # FIFO pop
                    self.logger.debug("Texture %d , %s to be removed is %s", k, str(v), str(GL.glIsTexture(v)))
                    GL.glDeleteTextures(v)
                    self.logger.debug("Removing %d from GLCache", k)

    def setSizeInBytes(self, size):
        """Sets the maximum size of the cache in bytes and trims excess elements"""
        self.sizeInBytes = size
        if(self.itemSize is not None):
            size = self.sizeInBytes/self.itemSize
            self.setMaxSize(size)
            self.logger.debug("Setting GLCache size to %d", size)
