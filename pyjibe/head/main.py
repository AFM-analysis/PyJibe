# flake8: noqa: E402 (matplotlib.use has to be right after the import)
import os.path as os_path
import pathlib
import pkg_resources
import signal
import sys
import traceback
import webbrowser

import matplotlib
matplotlib.use('QT5Agg')

from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtCore import QStandardPaths

import afmformats
import h5py
import lmfit
import nanite
import nanite.read
import numpy
import scipy
import sklearn

from . import custom_widgets
from .dlg_tool_convert import ConvertDialog
from . import preferences
from . import update

from ..extensions import ExtensionManager
from .. import registry
from .._version import version as __version__


class PyJibeQMdiSubWindow(QtWidgets.QMdiSubWindow):
    def closeEvent(self, QCloseEvent):
        """Correctly de-register a data set before removing the subwindow"""
        mainwidget = self.mdiArea().parentWidget().parentWidget()
        mainwidget.rem_subwindow(self.windowTitle())
        super(PyJibeQMdiSubWindow, self).closeEvent(QCloseEvent)


class PyJibe(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        """Initialize PyJibe

        If you pass the "--version" command line argument, the
        application will print the version after initialization
        and exit.
        """
        super(PyJibe, self).__init__(*args, **kwargs)
        # Settings are stored in the .ini file format. Even though
        # `self.settings` may return integer/bool in the same session,
        # in the next session, it will reliably return strings. Lists
        # of strings (comma-separated) work nicely though.
        QtCore.QCoreApplication.setOrganizationName("AFM-Analysis")
        QtCore.QCoreApplication.setOrganizationDomain("pyjibe.mpl.mpg.de")
        QtCore.QCoreApplication.setApplicationName("PyJibe")
        QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
        #: PyJibe settings
        self.settings = QtCore.QSettings()
        self.settings.setIniCodec("utf-8")

        # update check
        self._update_thread = None
        self._update_worker = None

        # load ui files
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
        # Edit menu
        self.actionPreferences.triggered.connect(self.on_preferences)
        # Tool menu
        self.actionConvert_AFM_data.triggered.connect(self.on_tool_convert)
        # Help menu
        self.actionDocumentation.triggered.connect(self.on_documentation)
        self.actionSoftware.triggered.connect(self.on_software)
        self.actionAbout.triggered.connect(self.on_about)

        #: Extensions
        store_path = os_path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.AppLocalDataLocation), "extensions")
        try:
            self.extensions = ExtensionManager(store_path)
        except BaseException:
            QtWidgets.QMessageBox.warning(
                self,
                "Extensions automatically disabled",
                "Some extensions could not be loaded and were disabled:\n\n"
                + traceback.format_exc(),
                )

        self.subwindows = []
        self.subwindow_data = []
        self.mdiArea.cascadeSubWindows()
        self.showMaximized()
        # if "--version" was specified, print the version and exit
        if "--version" in sys.argv:
            print(__version__)
            QtWidgets.QApplication.processEvents(
                QtCore.QEventLoop.AllEvents, 300)
            sys.exit(0)

        # check for updates
        do_update = int(self.settings.value("check for updates", 1))
        self.on_action_check_update(do_update)

        self.show()
        self.raise_()
        self.activateWindow()
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)

    def load_data(self, files, retry_open=None, separate_analysis=False):
        """Load AFM data"""
        # expand directories
        data_files = []
        for ff in files:
            data_files += afmformats.find_data(ff)

        if not data_files:
            ret = QtWidgets.QMessageBox.warning(
                self,
                "No AFM data found!",
                "No AFM data files could be found in the location specified.",
                QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Retry
            )
            if retry_open is not None and ret == QtWidgets.QMessageBox.Retry:
                retry_open()
        else:
            # Make sure there are no duplicate files (#12)
            data_files = sorted(set(data_files))
            if separate_analysis:
                # open each file in one analysis
                usable = [[ss] for ss in data_files]
            else:
                usable = [data_files]
            for flist in usable:
                aclass = registry.fd.UiForceDistance
                self.add_subwindow(aclass, flist)

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

    @QtCore.pyqtSlot()
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

    @QtCore.pyqtSlot(bool)
    def on_action_check_update(self, b):
        self.settings.setValue("check for updates", int(b))
        if b and self._update_thread is None:
            self._update_thread = QtCore.QThread()
            self._update_worker = update.UpdateWorker()
            self._update_worker.moveToThread(self._update_thread)
            self._update_worker.finished.connect(self._update_thread.quit)
            self._update_worker.data_ready.connect(
                self.on_action_check_update_finished)
            self._update_thread.start()

            version = __version__
            ghrepo = "AFM-analysis/PyJibe"

            QtCore.QMetaObject.invokeMethod(self._update_worker,
                                            'processUpdate',
                                            QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, version),
                                            QtCore.Q_ARG(str, ghrepo),
                                            )

    @QtCore.pyqtSlot(dict)
    def on_action_check_update_finished(self, mdict):
        # cleanup
        self._update_thread.quit()
        self._update_thread.wait()
        self._update_worker = None
        self._update_thread = None
        # display message box
        ver = mdict["version"]
        web = mdict["releases url"]
        dlb = mdict["binary url"]
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("PyJibe {} available!".format(ver))
        msg.setTextFormat(QtCore.Qt.RichText)
        text = "You can install PyJibe {} ".format(ver)
        if dlb is not None:
            text += 'from a <a href="{}">direct download</a>. '.format(dlb)
        else:
            text += 'by running `pip install --upgrade pyjibe`. '
        text += 'Visit the <a href="{}">official release page</a>!'.format(web)
        msg.setText(text)
        msg.exec_()

    @QtCore.pyqtSlot()
    def on_documentation(self):
        webbrowser.open("https://pyjibe.readthedocs.io")

    @QtCore.pyqtSlot()
    def on_open_bulk(self):
        dlg = custom_widgets.DirectoryDialogMultiSelect(self)
        search_dir = self.settings.value("paths/load data", "")
        dlg.setDirectory(search_dir)
        if dlg.exec_():
            files = dlg.selectedFiles()
            if files:
                self.load_data(files=files, retry_open=self.on_open_bulk,
                               separate_analysis=False)
                self.settings.setValue("paths/load data",
                                       str(dlg.getDirectory()))

    @QtCore.pyqtSlot()
    def on_open_multiple(self):
        dlg = custom_widgets.DirectoryDialogMultiSelect(self)
        search_dir = self.settings.value("paths/load data", "")
        dlg.setDirectory(search_dir)

        if dlg.exec_():
            files = dlg.selectedFiles()
            if files:
                self.load_data(files=files, retry_open=self.on_open_multiple,
                               separate_analysis=True)
                self.settings.setValue("paths/load data",
                                       str(dlg.getDirectory()))

    @QtCore.pyqtSlot()
    def on_open_single(self):
        ext_opts = []
        # all
        exts = ["*"+e for e in registry.known_suffixes]
        ext_opts.append("Supported file types ({})".format(" ".join(exts)))
        # individual
        for suffix in registry.known_suffixes:
            for item in afmformats.formats.formats_by_suffix[suffix]:
                ext_opts.append("{} - {} (*{})".format(
                    item["maker"], item["descr"], suffix))
        exts_str = ";;".join(ext_opts)

        search_dir = self.settings.value("paths/load data", "")
        n, _e = QtWidgets.QFileDialog.getOpenFileNames(
            self, "Open single file", search_dir, exts_str, "")
        if n:
            # user did not press cancel
            self.load_data(files=n, retry_open=self.on_open_single)
            self.settings.setValue("paths/load data",
                                   str(pathlib.Path(n[0]).parent))

    @QtCore.pyqtSlot()
    def on_preferences(self):
        """Show the DCOR import dialog"""
        dlg = preferences.Preferences(self)
        dlg.exec()

    @QtCore.pyqtSlot()
    def on_software(self):
        libs = [afmformats,
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

    @QtCore.pyqtSlot()
    def on_tool_convert(self):
        dlg = ConvertDialog(self)
        dlg.show()


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
