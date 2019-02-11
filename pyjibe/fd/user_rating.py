import hashlib
import os
import pathlib
import pkg_resources
import time

import h5py
import numpy as np
from PyQt5 import uic, QtWidgets


# load QWidget from ui file
ui_path = pkg_resources.resource_filename("pyjibe.fd",
                                          "user_rating_design.ui")
UiUserRatingBase = uic.loadUiType(ui_path)[0]


class Rater(QtWidgets.QWidget, UiUserRatingBase):
    def __init__(self, apc, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        UiUserRatingBase.__init__(self)
        self.setupUi(self)
        self.apc = apc

        self.ratings = {}
        self.comments = {}

        self.initial_stuff()
        self.setup_signals()

    def initial_stuff(self):
        # set user name
        user = "unknown"
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            if name in os.environ:
                user = os.environ[name]
        self.user_name.setText(user)
        # set correct initial index
        item = self.apc.list_curves.currentItem()
        idx = self.apc.list_curves.indexOfTopLevelItem(item)
        self.curve_index.setValue(idx+1)
        self.curve_index.setMaximum(len(self.apc.data_set))

    def setup_signals(self, enable=True):
        cn = [
            # Change of index updates apc
            [self.curve_index.valueChanged, self.on_change_index],
            [self.sp_rating.valueChanged, self.on_change_values],
            [self.text_comment.textChanged, self.on_change_values],
            [self.btn_save.clicked, self.on_save],
        ]

        for signal, slot in cn:
            if enable:
                signal.connect(slot)
            else:
                signal.disconnect(slot)

    def on_change_index(self):
        index = self.curve_index.value()-1
        self.setup_signals(False)
        if index in self.ratings:
            a = self.ratings[index]
            b = self.comments[index]
        else:
            a = -1
            b = ""
        self.sp_rating.setValue(a)
        self.text_comment.setPlainText(b)
        self.setup_signals(True)
        it = self.apc.list_curves.topLevelItem(index)
        self.apc.list_curves.setCurrentItem(it)
        self.sp_rating.selectAll()
        self.sp_rating.setFocus()

    def on_change_values(self):
        index = self.curve_index.value()-1
        self.ratings[index] = self.sp_rating.value()
        self.comments[index] = self.text_comment.toPlainText()

    def on_save(self):
        # Let user select directory
        filen = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save rating information", filter="*.h5")

        h5path = pathlib.Path(filen[0]).with_suffix(".h5")
        if h5path.exists():
            h5path.unlink()

        name = self.user_name.text()

        for ii in list(self.ratings.keys()):
            save_hdf5(h5path=h5path,
                      indent=self.apc.data_set[ii],
                      user_rate=self.ratings[ii],
                      user_name=name,
                      user_comment=self.comments[ii])


def hash_file(path, blocksize=65536):
    """Compute sha256 hex-hash of a file

    Parameters
    ----------
    path: str
        path to the file
    blocksize: int
        block size read from the file

    Returns
    -------
    hex: str
        The first six characters of the hash
    """
    fname = pathlib.Path(path)
    hasher = hashlib.sha256()
    with fname.open('rb') as fd:
        buf = fd.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fd.read(blocksize)
    return hasher.hexdigest()[:6]


def save_hdf5(h5path, indent, user_rate, user_name, user_comment, h5mode="a"):
    """Store all relevant data of a user rating into an hdf5 file

    Parameters
    ----------
    h5path: str
        Path to HDF5 file where data will be stored
    indent: afmfit.Indentation
        The experimental data processed and fitted with afmfit
    user_rate: float
        Rating given by the user
    user_name: str
        Name of the rating user
    """
    # TODO:
    # - use this method from afmfit when the time comes
    # - remove h5py dependency from setup.py
    with h5py.File(str(h5path), mode=h5mode) as h5:
        # store raw experimental data as binary array
        if "data" not in h5:
            h5.create_group("data")
        data = h5["data"]
        dhash = hash_file(indent.path)
        if dhash not in data:
            meas = data.create_dataset(
                dhash,
                data=np.fromfile(str(indent.path), dtype=bool),
            )
            meas.attrs["path"] = str(indent.path)
        # store indentation data along with the user rate
        if "analysis" not in h5:
            h5.create_group("analysis")
        ana = h5["analysis"]
        idd = "{}_{}".format(dhash, indent.enum)
        if idd in ana:
            raise ValueError(
                "Cannot store same rating twice in one hdf5 file!")
        out = ana.create_group(idd)
        out.attrs["data enum"] = indent.enum
        out.attrs["data hash"] = dhash
        out.attrs["user comment"] = user_comment
        out.attrs["user name"] = user_name
        out.attrs["user rate"] = user_rate
        out.attrs["user time"] = time.time()
        out.attrs["user time str"] = time.ctime()
        for key in indent.fit_properties:
            val = indent.fit_properties[key]
            if key.startswith("params_"):
                val = val.dumps()
            elif key == "preprocessing":
                val = ",".join(val)
            elif key == "range_x":
                val = str(val)
            out.attrs["fit {}".format(key)] = val

        out["fit"] = indent["fit"].as_matrix()
        out["fit range"] = indent["fit range"].as_matrix()
        out["force"] = indent["force"].as_matrix()
        out["fit residuals"] = indent["fit residuals"].as_matrix()
        out["tip position"] = indent["tip position"].as_matrix()
        out["segment"] = indent["segment"].as_matrix()
