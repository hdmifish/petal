#!/usr/bin/python3.5
from petal import Petal

import traceback
import os

os.system('')

bot = Petal()

try:
    bot.run()
except Exception as e:
    traceback.print_exc()
