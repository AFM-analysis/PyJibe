import shutil
import tempfile
import time

from PyQt5 import QtCore

TMPDIR = tempfile.mkdtemp(prefix=time.strftime(
    "pyjibe_test_%H.%M_"))


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    # disable update checking
    QtCore.QCoreApplication.setOrganizationName("AFM-Analysis")
    QtCore.QCoreApplication.setOrganizationDomain("pyjibe.mpl.mpg.de")
    QtCore.QCoreApplication.setApplicationName("PyJibe")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    settings = QtCore.QSettings()
    settings.setIniCodec("utf-8")
    settings.setValue("check for updates", 0)
    settings.sync()
    # set global temp directory
    tempfile.tempdir = TMPDIR


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    QtCore.QCoreApplication.setOrganizationName("AFM-Analysis")
    QtCore.QCoreApplication.setOrganizationDomain("pyjibe.mpl.mpg.de")
    QtCore.QCoreApplication.setApplicationName("PyJibe")
    QtCore.QSettings.setDefaultFormat(QtCore.QSettings.IniFormat)
    settings = QtCore.QSettings()
    settings.setIniCodec("utf-8")
    # clear global temp directory
    shutil.rmtree(TMPDIR, ignore_errors=True)
