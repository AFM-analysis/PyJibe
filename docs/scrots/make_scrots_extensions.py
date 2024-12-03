"""Screenshots for quick guide extensions"""
import pathlib
import sys

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from pyjibe.head.main import PyJibe
from pyjibe.head import preferences

data_path = pathlib.Path(__file__).resolve().parent / ".." / "data"

app = QApplication(sys.argv)

QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.Language.C))

mw = PyJibe()
mw.settings.setValue("check for updates", 0)
mw.settings.setValue("advanced/developer mode", 0)
mw.settings.setValue("advanced/expert mode", 0)

mw.extensions.import_extension_from_path(
    data_path / "model_external_basic.py")

# open the dialog window
dlg = preferences.Preferences(mw)
dlg.tabWidget.setCurrentIndex(1)

dlg.show()
QApplication.processEvents(QtCore.QEventLoop.AllEvents, 300)
dlg.grab().save("_qg_extensions.png")

mw.close()
