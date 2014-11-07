from Qt import QtCore, QtGui
import settingsOwl
import logging

class Sizing(QtCore.QObject):
    sizingProgress = QtCore.Signal(int, str)
    sizingDone = QtCore.Signal()
    def __init__(self,parent,model):
        QtCore.QObject.__init__(self,parent)
        self.modelItem = model
        self.logger = logging.getLogger("Sizing")
        self.logger.setLevel(settingsOwl.loglev["Sizing"])
        self.stop = False
        self.running = False

    def setImgs(self, imgs):
        self.imgs = imgs

    @QtCore.Slot(int)
    def startSizing(self):
        self.running = True
        N = len(self.imgs)
        for i in range(N):
            self.modelItem.center(self.imgs[i])
            self.modelItem.fit(self.imgs[i])
            status = int((float(i+1)/N)*100.)
            status_msg = "Sizing image %d/%d (%.2f %%)" %(i+1, N, status)
            self.sizingProgress.emit(status, status_msg)
            if self.stop: break 
        self.running = False
        self.sizingDone.emit()

    def stopSizing(self):
        self.stop = True
        if not self.running: self.sizingDone.emit()
