"""Test of data set functionalities"""
from PyQt5 import QtWidgets, QtCore

import pyjibe.head

from helpers import make_directory_with_data


def test_qmap_with_unused_curves(qtbot):
    """Uncheck "use" in the curve list and switch to the qmap tab"""
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data())
    war = main_window.subwindows[0].widget()
    # uncheck first curve
    cl1 = war.list_curves.currentItem()
    cl1.setCheckState(3, QtCore.Qt.Unchecked)
    war.tabs.setCurrentIndex(5)
    QtWidgets.QApplication.processEvents()
