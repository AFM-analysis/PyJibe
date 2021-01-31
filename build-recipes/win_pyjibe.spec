import os
from os.path import abspath, exists, join, dirname, relpath
import platform
import sys
import warnings

cdir = abspath(".")
sys.path.insert(0, cdir)

if not exists(join(cdir, "pyjibe")):
	warnings.warn("Cannot find 'pyjibe'! Please run pyinstaller "+
                  "from git root folder.")

pyinstdir = os.path.realpath(cdir+"/build-recipes/")
script = os.path.join(pyinstdir, "PyJibeApp.py")

# Icon
icofile = os.path.join(pyinstdir,"PyJibe.ico")

a = Analysis([script],
             pathex=[cdir],
             hookspath=[pyinstdir],
             runtime_hooks=None)

options = [ ('u', None, 'OPTION'), ('W ignore', None, 'OPTION') ]

pyz = PYZ(a.pure)
exe = EXE(pyz,
          a.scripts,
          options,
          exclude_binaries=True,
          name="PyJibe.exe",
          debug=False,
          strip=False,
          upx=False,
          icon=icofile,
          console=False)

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name="PyJibe")
