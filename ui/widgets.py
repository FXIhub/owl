from Qt import QtGui, QtCore, QtOpenGL
import ui.sizingWidget
import ui.dialogs
from analysis import Sizing

class SizingWidget(QtGui.QGroupBox, ui.sizingWidget.Ui_SizingWidget):
    sizingStopped = QtCore.Signal()
    def __init__(self, parent, view):
        QtGui.QGroupBox.__init__(self,parent)
        self.setupUi(self)
        self.view = view
        self.modelItem = self.view.data.modelItem
        self.sizing = Sizing(None, self.modelItem)
        self.sizingThread = QtCore.QThread()
        self.sizing.moveToThread(self.sizingThread)
        self.sizingThread.start()
        self.setData()
        
        # Connect signals
        self.setdataButton.released.connect(self.setData)
        self.startButton.released.connect(self.sizing.startSizing)
        self.stopButton.released.connect(self.stopSizing)
        self.sizing.sizingProgress.connect(self.updateProgress)
        
    def onExperiment(self):
        expDialog = ui.dialogs.ExperimentDialog(self, self.modelItem)
        expDialog.exec_()

    def setData(self):
        imgs = self.view.indexProjector.imgs
        self.sizing.setImgs(imgs)
        self.progressLabel.setText("Ready for sizing (%d patterns)" % len(imgs))

    def updateProgress(self, status, status_msg):
        self.progressBar.setValue(status)
        self.progressLabel.setText(status_msg)

    def stopSizing(self):
        self.sizing.stopSizing()
        #self.sizingStopped.emit()
