# -----------------------------------------------------------------------------
# Copyright (c) 2017, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
# -----------------------------------------------------------------------------

# Hook for sklearn
from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files("sklearn", include_py_files=True)
datas += collect_data_files("sklearn", subdir=".dylibs")

hiddenimports = [
    'sklearn.tree._utils',
    'sklearn.neighbors.typedefs',
    'sklearn.neighbors.quad_tree',
    'sklearn.utils._cython_blas',
    'scipy.special.cython_special',
]
