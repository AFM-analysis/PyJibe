"""Screenshots for quick guide import ts (not working automatically)"""
import pathlib
import sys
import time

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from pyjibe.head.main import PyJibe

jpkfile = pathlib.Path("PAAm_Compliant_ROI1_force-save-"
                       + "2019.10.25-10.42.02.660.jpk-force")


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


app = QApplication(sys.argv)
QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))
mw = PyJibe()
mw.settings.setValue("check for updates", 0)
mw.settings.setValue("advanced/developer mode", 0)
mw.settings.setValue("advanced/expert mode", 0)

cleanup_autosave(jpkfile=jpkfile)

# build up a session
mw.load_data([jpkfile])

war = mw.subwindows[0].widget()
# unfortunately, this does not grab the popped-up combobox
war.cb_rating_scheme.showPopup()
war.update()
war.repaint()
QApplication.processEvents()
QApplication.processEvents()
war.grab().save("_qg_import_ts.png")

print("Screenshot must be taken manually (closing in 10s)")
time.sleep(10)

mw.close()
