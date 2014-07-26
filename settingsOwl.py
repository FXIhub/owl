import logging,h5py

# logging
loglev = {}
loglev["Viewer"] = logging.WARNING
loglev["IndexProjector"] = logging.WARNING
loglev["DataItem"] = logging.WARNING
loglev["ImageLoader"] = logging.WARNING

# SWMR support
try:
    h5py.h5f.ACC_SWMR_READ
except:
    swmrSupported = False
else:
    swmrSupported = True
