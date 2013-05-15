from PySide import QtGui, QtCore
from view2d import View2D

class View2DScrollWidget(QtGui.QWidget):
    def __init__(self,parent,view2D):
        QtGui.QWidget.__init__(self,parent)
        self.view2D = view2D
        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(0) 
        hbox.addWidget(view2D)
        self.scrollbar = QtGui.QScrollBar(QtCore.Qt.Vertical,self)
        self.scrollbar.setTracking(False)
        self.scrollbar.setMinimum(self.view2D.minimumTranslation())
        self.scrollbar.setPageStep(1)
        self.scrollbar.valueChanged.connect(self.onValueChanged)
        self.view2D.indexProjector.projectionChanged.connect(self.update)
        self.view2D.stackWidthChanged.connect(self.update)
        self.view2D.translationChanged.connect(self.onTranslationChanged)
        hbox.addWidget(self.scrollbar)
        self.setLayout(hbox)
    def onValueChanged(self,value):
        self.view2D.scrollTo(value)
    def update(self,foo=None):
        if self.view2D.indexProjector.viewIndices == None or self.view2D.indexProjector.stackSize == None:
            self.scrollbar.hide()
        else:
            NViewIndices = len(self.view2D.indexProjector.viewIndices)
            imgHeight = self.view2D.getImgHeight("window",True)
            self.scrollbar.setPageStep(imgHeight)
            maximum = self.view2D.maximumTranslation()            
            self.scrollbar.setMaximum(maximum)
            self.scrollbar.setValue(0)
            self.view2D.scrollTo(0)
            self.scrollbar.show()
    def onTranslationChanged(self,x,y):
        self.scrollbar.setValue(y)
        
