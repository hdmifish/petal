#!/usr/bin/python3.5
from petal import Petal

import traceback
import os, ctypes
import sys
import pip
print("DETECTED ARGS: " + str(sys.argv))

if "-u" in sys.argv or "--update" in sys.argv:
    try:
        root = os.getuid() == 0
    except AttributeError:
        root = ctypes.windll.shell32.IsUserAdmin() != 0

    if not root:
        print("You are not root or administrator, auto updates wont work")
    else:
        print("Checking for updates before running...")
        try:
            with open("requirements.txt", "r") as fp:
                for line in fp.readlines():
                    pip.main(['install', '--upgrade', line.strip()])
        except Exception as e:
            print("Exception: " + str(e))
        else:
            print("Upgraded packages, starting program")


if "--dev-mode" in sys.argv:
    print("ALERT: Using Developer Mode!")
    bot = Petal(devmode=True)
else:
    bot = Petal(devmode=False)


try:
    print("Attempting to connect to Discord, please wait....")
    bot.run()
except Exception as e:
    traceback.print_exc()
