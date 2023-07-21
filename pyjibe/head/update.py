import json
import os
import struct
import sys
import traceback
import urllib.request

from packaging.version import parse as parse_version
from PyQt5 import QtCore


class UpdateWorker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    data_ready = QtCore.pyqtSignal(dict)

    @QtCore.pyqtSlot(str, str)
    def processUpdate(self, version, ghrepo):
        mdict = check_release(ghrepo, version)
        if mdict["update available"]:
            self.data_ready.emit(mdict)
        self.finished.emit()


def check_for_update(version, ghrepo):
    thread = QtCore.QThread()
    obj = UpdateWorker()
    obj.moveToThread(thread)
    obj.finished.connect(thread.quit)
    thread.start()

    QtCore.QMetaObject.invokeMethod(obj, 'processUpdate',
                                    QtCore.Qt.QueuedConnection,
                                    QtCore.Q_ARG(str, version),
                                    QtCore.Q_ARG(str, ghrepo),
                                    )


def check_release(ghrepo="user/repo", version=None, timeout=20):
    """Check GitHub repository for latest release"""
    url = "https://api.github.com/repos/{}/releases/latest".format(ghrepo)
    if "GITHUB_TOKEN" in os.environ:
        hdr = {'authorization': os.environ["GITHUB_TOKEN"]}
    else:
        hdr = {}
    web = "https://github.com/{}/releases".format(ghrepo)
    errors = None  # error messages (str)
    update = False  # whether an update is available
    binary = None  # download link to binary file
    new_version = None  # string identifying new version
    try:
        req = urllib.request.Request(url, headers=hdr)
        data = urllib.request.urlopen(req, timeout=timeout).read()
    except BaseException:
        errors = traceback.format_exc()
    else:
        j = json.loads(data)

        newversion = j["tag_name"]

        if version is not None:
            new = parse_version(newversion)
            old = parse_version(version)
            if new > old:
                update = True
                new_version = newversion
                if hasattr(sys, "frozen"):
                    # determine which binary URL we need
                    if sys.platform == "win32":
                        nbit = 8 * struct.calcsize("P")
                        if nbit == 32:
                            dlid = "win_32bit_setup.exe"
                        else:
                            dlid = "win_64bit_setup.exe"
                    elif sys.platform == "darwin":
                        dlid = ".pkg"
                    else:
                        dlid = False
                    # search for binary download file
                    if dlid:
                        for a in j["assets"]:
                            if a["browser_download_url"].count(dlid):
                                binary = a["browser_download_url"]
                                break
    mdict = {"releases url": web,
             "binary url": binary,
             "version": new_version,
             "update available": update,
             "errors": errors,
             }
    return mdict
