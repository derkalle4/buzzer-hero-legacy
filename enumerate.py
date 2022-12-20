#!/usr/bin/env python3
from __future__ import print_function

import hid

for d in hid.enumerate():
    keys = list(d.keys())
    keys.sort()
    for key in keys:
        print("%s : %s" % (key, d[key]))
