from PySide import QtGui, QtCore
from view1d import View1D
from view2dscrollwidget import View2DScrollWidget
from view2d import View2D

class ViewSplitter(QtGui.QSplitter):
    def __init__(self,parent=None):
        QtGui.QSplitter.__init__(self,parent)
        self.setOrientation(QtCore.Qt.Vertical)

        self.view2D = View2D(parent,self)
        self.view2DScrollWidget = View2DScrollWidget(self,self.view2D)
        self.addWidget(self.view2DScrollWidget)
        #self.addWidget(self.view2D)

        self.view1D = View1D(self)
        self.view1D.hide()
        self.addWidget(self.view1D)

        self.setSizes([1000,1000])
