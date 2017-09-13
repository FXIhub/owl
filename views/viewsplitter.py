from Qt import QtGui, QtCore
from view1d import View1D
from view2dscrollwidget import View2DScrollWidget
from view2d import View2D

class ViewSplitter(QtGui.QSplitter):
    def __init__(self, parent=None, indexProjector=None):
        print "ViewSplitter", indexProjector

        QtGui.QSplitter.__init__(self, parent)
        self.setOrientation(QtCore.Qt.Vertical)

        self.view2D = View2D(self, parent, indexProjector)
        print "ViewSplitter", self.view2D.indexProjector
        self.view2DScrollWidget = View2DScrollWidget(self, self.view2D)
        self.addWidget(self.view2DScrollWidget)
        #self.view2D.stackSizeChanged.connect(self.view2DScrollWidget.update)

        self.view1D = View1D(self, indexProjector)
        self.view1D.hide()
        self.addWidget(self.view1D)

        self.setSizes([1000,1000])
