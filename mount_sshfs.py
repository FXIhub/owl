#!/usr/bin/env python

import os,sys

if len(sys.argv) < 3:
    print "Usage: ./mount_sshfs USER@HOST:DIRECTORY MOUNTPOINT"

source = sys.argv[1]
target = sys.argv[2]

options = ""
options += "-o direct_io "
#options += "-o nolocalcaches "
#options += "-o noauto_cache "
#options += "-o no_readahed "
#options += "-oIdentityFile=/Users/home/hantke/.ssh/id_rsa "

cmd = "sshfs -p 22 %s %s %s" % (source,target,options)

os.system(cmd)
