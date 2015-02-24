#!/usr/bin/env python
import os
#prefix = "/usr/local"
prefix = "/usr"
owl_dir = os.path.dirname(os.path.realpath(__file__))
os.system("ln -sf %s/owl %s/bin/owl" % (owl_dir,prefix))
