#!/usr/bin/python3.6
from petal import Petal
import subprocess
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
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
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
