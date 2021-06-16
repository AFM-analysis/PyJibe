"""Test built-in rater"""
import pathlib
import shutil
import tempfile
from unittest import mock

import h5py
from PyQt5 import QtCore

import pyjibe.head


data_path = pathlib.Path(__file__).parent / "data"


def test_rater_basic(qtbot):
    mw = pyjibe.head.PyJibe()
    td = pathlib.Path(tempfile.mkdtemp(prefix="rater_")) / "map.jpk-force-map"
    shutil.copy2(data_path / "map2x2_extracted.jpk-force-map", td)
    mw.load_data([td])

    war = mw.subwindows[0].widget()

    h5out = pathlib.Path(tempfile.mkdtemp(prefix="rate_")) / "rate.h5"
    with mock.patch("PyQt5.QtWidgets.QFileDialog.getSaveFileName",
                    lambda *args, **kwargs: (str(h5out), None)):
        war.on_user_rate()

    rater = war.curve_rater  # it's not a modal dialog

    # fill in a few values
    assert rater.sp_rating.value() == -1
    rater.sp_rating.setValue(8)
    qtbot.mouseClick(rater.btn_next, QtCore.Qt.LeftButton)
    assert rater.curve_index.value() == 2
    assert rater.sp_rating.value() == -1
    rater.text_comment.setPlainText("peter")
    qtbot.mouseClick(rater.btn_prev, QtCore.Qt.LeftButton)
    assert rater.curve_index.value() == 1
    assert rater.sp_rating.value() == 8
    assert rater.text_comment.toPlainText() == ""
    qtbot.mouseClick(rater.btn_next, QtCore.Qt.LeftButton)
    qtbot.mouseClick(rater.btn_next, QtCore.Qt.LeftButton)
    assert rater.curve_index.value() == 3
    assert rater.sp_rating.value() == -1
    mw.close()

    with h5py.File(h5out, "r") as h5:
        assert len(h5["analysis"]) == 2
        keys = list(h5["analysis"].keys())
        assert h5["analysis"][keys[0]].attrs["user rate"] == 8
        assert h5["analysis"][keys[1]].attrs["user comment"] == "peter"
