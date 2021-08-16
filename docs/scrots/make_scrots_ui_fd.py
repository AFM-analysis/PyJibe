"""Screenshots for quick guide import ts (not working automatically)"""
import pathlib
import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from pyjibe.head.main import PyJibe

jpkfiles = [pathlib.Path("map-data-2015.05.21-18.16.49.170.jpk-force-map")]


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


app = QApplication(sys.argv)
QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))
mw = PyJibe()

cleanup_autosave(jpkfile=jpkfiles[0])

# build up a session
mw.load_data(jpkfiles)
war = mw.subwindows[0].widget()
war.tab_fit.sp_range_2.setValue(2.3)
war.tab_fit.table_parameters_initial.item(1, 1).setText("18.65")


# do not fit all curves, because it takes too long
for ii in range(200, 230):
    it = war.list_curves.topLevelItem(ii)
    war.list_curves.setCurrentItem(it)

# Set a nice example curve
it = war.list_curves.topLevelItem(210)
war.list_curves.setCurrentItem(it)
war.sp_rating_thresh.setValue(4.0)
war.btn_rating_filter.clicked.emit()

# main
QApplication.processEvents()
mw.grab().save("_ui_fd_main.png")

# controls
QApplication.processEvents()
war.widget_list_controls.grab().save("_ui_fd_curve_controls.png")

# preprocess
war.tabs.setCurrentIndex(0)
QApplication.processEvents()
war.tabs.grab().save("_ui_fd_tab_preproc.png")

# fit
war.tabs.setCurrentIndex(1)
QApplication.processEvents()
war.tabs.grab().save("_ui_fd_tab_fit.png")

# edelta
war.tabs.setCurrentIndex(2)
QApplication.processEvents()
war.tabs.grab().save("_ui_fd_tab_edelta.png")

# info
war.tabs.setCurrentIndex(4)
QApplication.processEvents()
war.tabs.grab().save("_ui_fd_tab_info.png")

# qmap
# Select all curves (so QMap is fully visible)
war.sp_rating_thresh.setValue(0.0)
war.btn_rating_filter.clicked.emit()
war.tabs.setCurrentIndex(5)
war.sp_rating_thresh.setValue(0)
war.btn_rating_filter.clicked.emit()
QApplication.processEvents()
war.tabs.grab().save("_ui_fd_tab_qmap.png")

# plot
war.tabs.setCurrentIndex(3)
QApplication.processEvents()
war.tabs.setFixedSize(war.tabs.sizeHint().width(), 300)
war.tabs.grab().save("_ui_fd_tab_plot.png")

mw.close()

cleanup_autosave(jpkfile=jpkfiles[0])
