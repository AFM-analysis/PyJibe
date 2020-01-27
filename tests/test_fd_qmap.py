"""Test of data set functionalities"""
import pathlib

from PyQt5 import QtWidgets, QtCore
import pytest


import pyjibe.head


here = pathlib.Path(__file__).parent
jpkfile = here / "data" / "map2x2_extracted.jpk-force-map"


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


@pytest.fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test, for example:
    cleanup_autosave(jpkfile)
    # A test function will be run at this point
    yield
    # Code that will run after your test, for example:
    cleanup_autosave(jpkfile)


def test_qmap_with_unused_curves(qtbot):
    """Uncheck "use" in the curve list and switch to the qmap tab"""
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=[jpkfile])
    war = main_window.subwindows[0].widget()
    # uncheck first curve
    cl1 = war.list_curves.currentItem()
    cl1.setCheckState(3, QtCore.Qt.Unchecked)
    war.tabs.setCurrentIndex(5)
    QtWidgets.QApplication.processEvents()
