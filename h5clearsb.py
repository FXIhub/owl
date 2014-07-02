#!/usr/bin/env python

import sys

if(len(sys.argv) < 2):
    print "Usage: h5clearsb <hdf5 file>"
    sys.exit(0)

f = open(sys.argv[1],'rb')
f.seek(20)
flags = ord(f.read(1))
if(flags == 0):
    sys.exit(0)
else:
    print "File consistency flags were %d. Resetting to 0." % flags
f.close()
f = open(sys.argv[1],'r+b')
f.seek(20)
f.write(chr(0))
f.close()
