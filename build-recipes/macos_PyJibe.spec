# -*- mode: python ; coding: utf-8 -*-
from os.path import exists
import warnings

if not exists("./PyJibeLauncher.py"):
    warnings.warn("Cannot find 'PyJibeLauncher.py'! Please run pyinstaller " +
                  "from the 'build-recipes' directory.")

block_cipher = None

a = Analysis(['PyJibeLauncher.py'],
             pathex=['.'],
             binaries=[],
             datas=[],
             hiddenimports=[],
             hookspath=['.'],
             runtime_hooks=[],
             excludes=['tkinter'],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='PyJibe',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='PyJibe')
app = BUNDLE(coll,
             name='PyJibe.app',
             icon='PyJibe.icns',
             bundle_identifier=None,
             info_plist = {
                'NSHighResolutionCapable' : 'True',
                }
             )
