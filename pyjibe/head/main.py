import pathlib
import pkg_resources
import signal
import sys
import traceback
import webbrowser

from PyQt5 import uic, QtCore, QtWidgets

import afmformats
import appdirs
import h5py
import lmfit
import matplotlib
import nanite
import numpy
import scipy
import sklearn


from . import custom_widgets

from .. import registry
from ..settings import SettingsFile
from .._version import version as __version__


class PyJibeQMdiSubWindow(QtWidgets.QMdiSubWindow):
    def closeEvent(self, QCloseEvent):
        """Correctly de-register a data set before removing the subwindow"""
        mainwidget = self.mdiArea().parentWidget().parentWidget()
        mainwidget.rem_subwindow(self.windowTitle())
        super(PyJibeQMdiSubWindow, self).closeEvent(QCloseEvent)


class PyJibe(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(PyJibe, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.head", "main.ui")
        uic.loadUi(path_ui, self)

        self.setWindowTitle("PyJibe {}".format(__version__))
        # Disable native menubar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # Connect menu entries
        # File menu
        self.action_open_bulk.triggered.connect(self.on_open_bulk)
        self.action_open_single.triggered.connect(self.on_open_single)
        self.action_open_multiple.triggered.connect(self.on_open_multiple)
        # Help menu
        self.actionDocumentation.triggered.connect(self.on_documentation)
        self.actionSoftware.triggered.connect(self.on_software)
        self.actionAbout.triggered.connect(self.on_about)
        # Add settings
        self.settings = SettingsFile()

        self.subwindows = []
        self.subwindow_data = []
        self.mdiArea.cascadeSubWindows()
        self.showMaximized()

    def add_subwindow(self, aclass, flist):
        """Add a subwindow, register data set and add to menu"""
        sub = PyJibeQMdiSubWindow()
        inst = aclass(sub)
        sub.setWidget(inst)
        inst.add_files(flist)
        self.mdiArea.addSubWindow(sub)
        sub.show()
        self.subwindows.append(sub)
        # Add export choices
        if hasattr(inst, "get_export_choices"):
            choices = inst.get_export_choices()
            menobj = self.menuExport.addMenu(sub.windowTitle())
            for choice in choices:
                action = menobj.addAction(choice[0])
                action.triggered.connect(getattr(inst, choice[1]))

    def rem_subwindow(self, title):
        """De-register a data set and remove from the menu"""
        for ii, sub in enumerate(self.subwindows):
            if sub.windowTitle() == title:
                self.subwindows.pop(ii)
                break

        for action in self.menuExport.actions():
            if action.text() == title:
                self.menuExport.removeAction(action)
                break

    def on_about(self):
        about_text = "PyJibe is a user interface for data analysis in " \
            + "atomic force microscopy with an emphasis on biological " \
            + "specimens, such as tissue sections or single cells.\n\n" \
            + "Author: Paul Müller\n" \
            + "Repository: https://github.com/AFM-analysis/PyJibe\n" \
            + "Documentation: https://pyjibe.readthedocs.io"
        QtWidgets.QMessageBox.about(self,
                                    "PyJibe {}".format(__version__),
                                    about_text)

    def on_documentation(self):
        webbrowser.open("https://pyjibe.readthedocs.io")

    def on_open_bulk(self, evt=None):
        dlg = custom_widgets.FileDialog(self)
        search_dir = self.settings.get_path("load data")
        dlg.setDirectory(search_dir)
        if dlg.exec_():
            files = dlg.selectedFilesRecursive()
            files.sort()
            if files:
                self.load_data(files=files, retry_open=self.on_open_bulk,
                               separate_analysis=False)
                self.settings.set_path(dlg.getDirectory(), name="load data")

    def on_open_multiple(self, evt=None):
        dlg = custom_widgets.FileDialog(self)
        search_dir = self.settings.get_path("load data")
        dlg.setDirectory(search_dir)

        if dlg.exec_():
            files = dlg.selectedFilesRecursive()
            files.sort()
            if files:
                self.load_data(files=files, retry_open=self.on_open_multiple,
                               separate_analysis=True)
                self.settings.set_path(dlg.getDirectory(), name="load data")

    def on_open_single(self, evt=None):
        exts = ["*"+e for e in registry.known_suffixes]
        exts_str = "Supported file types ({})".format(" ".join(exts))
        search_dir = self.settings.get_path("load data")

        n, _e = QtWidgets.QFileDialog.getOpenFileName(self, "Open single file",
                                                      search_dir, exts_str)
        if n:
            # user did not press cancel
            self.load_data(files=[n], retry_open=self.on_open_single)
            self.settings.set_path(pathlib.Path(n).parent, name="load data")

    def on_software(self):
        libs = [afmformats,
                appdirs,
                h5py,
                lmfit,
                matplotlib,
                nanite,
                numpy,
                sklearn,
                scipy,
                ]
        sw_text = "PyJibe {}\n\n".format(__version__)
        sw_text += "Python {}\n\n".format(sys.version)
        sw_text += "Modules:\n"
        for lib in libs:
            sw_text += "- {} {}\n".format(lib.__name__, lib.__version__)
        sw_text += "- PyQt5 {}\n".format(QtCore.QT_VERSION_STR)
        if hasattr(sys, 'frozen'):
            sw_text += "\nThis executable has been created using PyInstaller."
        QtWidgets.QMessageBox.information(self,
                                          "Software",
                                          sw_text)

    def load_data(self, files, retry_open=None, separate_analysis=False):
        # approach-retract data files
        supfiles = []
        for ff in files:
            path = pathlib.Path(ff)
            if path.suffix in registry.known_suffixes:
                supfiles.append(ff)

        # check if AFM files were found
        if not len(supfiles):
            msg = QtWidgets.QMessageBox()
            msg.setIcon(QtWidgets.QMessageBox.Warning)
            msg.setText("No AFM data files found!")
            msg.setInformativeText("")
            msg.setWindowTitle("No AFM data found!")
            msg.setStandardButtons(
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Retry)
            retval = msg.exec_()
            if (retry_open is not None and
                    retval == QtWidgets.QMessageBox.Retry):
                retry_open()
        else:
            if separate_analysis:
                # open each file in one analysis
                supfiles = [[ss] for ss in supfiles]
            else:
                supfiles = [supfiles]
            for flist in supfiles:
                aclass = registry.fd.UiForceDistance
                self.add_subwindow(aclass, flist)


def excepthook(etype, value, trace):
    """
    Handler for all unhandled exceptions.

    Parameters
    ----------
    etype: Exception
        exception type (`SyntaxError`, `ZeroDivisionError`, etc...)
    value: str
        exception error message
    trace:
        traceback header, if any (otherwise, it prints the
        standard Python header: ``Traceback (most recent call last)``
    """
    vinfo = "Unhandled exception in PyJibe version {}:\n".format(__version__)
    tmp = traceback.format_exception(etype, value, trace)
    exception = "".join([vinfo]+tmp)

    errorbox = QtWidgets.QMessageBox()
    errorbox.addButton(QtWidgets.QPushButton('Close'),
                       QtWidgets.QMessageBox.YesRole)
    errorbox.addButton(QtWidgets.QPushButton(
        'Copy text && Close'), QtWidgets.QMessageBox.NoRole)
    errorbox.setText(exception)
    ret = errorbox.exec_()
    if ret == 1:
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(exception)


# Make Ctr+C close the app
signal.signal(signal.SIGINT, signal.SIG_DFL)
# Display exception hook in separate dialog instead of crashing
sys.excepthook = excepthook
