#-----------------------------------------------------------------------------
# Copyright (c) 2019, PyInstaller Development Team.
#
# Distributed under the terms of the GNU General Public License with exception
# for distributing bootloader.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

# Hook for PyJibe: https://github.com/AFM-analysis/PyJibe
from PyInstaller.utils.hooks import collect_data_files

# Data files
datas = collect_data_files("shapeout2", include_py_files=True)
datas += collect_data_files("shapeout2", subdir="img")

