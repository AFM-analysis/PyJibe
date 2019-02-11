import pathlib
import pkg_resources
import signal
import sys
import traceback

from PyQt5 import uic, QtWidgets

from . import custom_widgets

from .. import registry
from ..settings import SettingsFile
from .._version import version as __version__

# load QMainWindow from ui file
ui_path = pkg_resources.resource_filename("pyjibe.head", "main_design.ui")
MainBase = uic.loadUiType(ui_path)[0]


class PyJibeQMdiSubWindow(QtWidgets.QMdiSubWindow):
    def closeEvent(self, QCloseEvent):
        """Correctly de-register a data set before removing the subwindow"""
        mainwidget = self.mdiArea().parentWidget().parentWidget()
        mainwidget.rem_subwindow(self.windowTitle())
        super(PyJibeQMdiSubWindow, self).closeEvent(QCloseEvent)


class PyJibe(QtWidgets.QMainWindow, MainBase):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        MainBase.__init__(self)
        self.setupUi(self)
        self.setWindowTitle("PyJibe {}".format(__version__))
        # Disable native menubar (e.g. on Mac)
        self.menubar.setNativeMenuBar(False)
        # Connect menu entries
        self.action_open_bulk.triggered.connect(self.on_open_bulk)
        self.action_open_single.triggered.connect(self.on_open_single)
        self.action_open_multiple.triggered.connect(self.on_open_multiple)
        # Add settings
        self.settings = SettingsFile()

        self.subwindows = []
        self.subwindow_data = []
        self.mdiArea.cascadeSubWindows()
        self.showMaximized()

    def add_subwindow(self, widget, obj):
        """Add a subwindow, register data set and add to menu"""
        sub = PyJibeQMdiSubWindow()
        sub.setWidget(widget)
        self.mdiArea.addSubWindow(sub)
        sub.show()
        self.subwindows.append(sub)
        self.subwindow_data.append(obj)
        # Add export choices
        if hasattr(obj, "get_export_choices"):
            choices = obj.get_export_choices()
            menobj = self.menuExport.addMenu(widget.windowTitle())
            for choice in choices:
                action = menobj.addAction(choice[0])
                action.triggered.connect(getattr(obj, choice[1]))

    def rem_subwindow(self, title):
        """De-register a data set and remove from the menu"""
        for ii, sub in enumerate(self.subwindows):
            if sub.windowTitle() == title:
                self.subwindows.pop(ii)
                self.subwindow_data.pop(ii)
                break

        for action in self.menuExport.actions():
            if action.text() == title:
                self.menuExport.removeAction(action)
                break

    def on_open_bulk(self, evt=None):
        dlg = custom_widgets.FileDialog()
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
        dlg = custom_widgets.FileDialog()
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
        exts = ["*"+e for e in registry.file_extensions]
        exts_str = "Supported file types ({})".format(" ".join(exts))
        search_dir = self.settings.get_path("load data")

        n, _e = QtWidgets.QFileDialog.getOpenFileName(self, "Open single file",
                                                      search_dir, exts_str)
        if n:
            # user did not press cancel
            self.load_data(files=[n], retry_open=self.on_open_single)
            self.settings.set_path(pathlib.Path(n).parent, name="load data")

    def load_data(self, files, retry_open=None, separate_analysis=False):
        # approach-retract data files
        supfiles = []
        for ff in files:
            path = pathlib.Path(ff)
            if path.suffix in registry.file_extensions:
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
                widget = QtWidgets.QWidget()
                fdist = registry.fd.UiForceDistance(widget)
                fdist.add_files(flist)
                self.add_subwindow(widget, fdist)
                # Add to self, otherwise events will not be triggered!
                setattr(self, "subwindow_{}".format(
                    len(self.subwindows)), fdist)


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
