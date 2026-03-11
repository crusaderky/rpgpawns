"""Test import the library and print essential information"""

import platform
import sys

import rpgpawns

print("Python interpreter:", sys.executable)
print("Python version    :", sys.version)
print("Platform          :", platform.platform())
print("Library path      :", rpgpawns.__file__)
print("Library version   :", rpgpawns.__version__)
