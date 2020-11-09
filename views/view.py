
class View(object):
    def __init__(self,parent=None,indexProjector=None,datasetMode="image"):
        self.parent = parent
        self.indexProjector = indexProjector
        self.autoLast = False
        self.stackSize = 0
        self.datasetMode = datasetMode
        self.integrationMode = None



	
