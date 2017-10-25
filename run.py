#!/usr/bin/python3.5
from petal import Petal

import traceback
import os
import sys
print("DETECTED ARGS: " + str(sys.argv))
if "--dev_mode" in sys.argv:
    print("using dev_mode")
    bot = Petal(devmode=True)
else:
    bot = Petal(devmode=False)

os.system('')



try:
    bot.run()
except Exception as e:
    traceback.print_exc()
