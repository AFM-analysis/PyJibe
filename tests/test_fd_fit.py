"""Test of data set functionalities"""
import pathlib
import shutil
import tempfile

import nanite.model as nmodel
import numpy as np
import pytest
from PyQt5 import QtCore, QtWidgets

import pyjibe.head

from helpers import make_directory_with_data


data_path = pathlib.Path(__file__).parent / "data"


class MockModel():
    def __init__(self, model_key, **kwargs):
        # rebase on hertz model
        md = nmodel.models_available["hertz_para"]
        for key in dir(md):
            setattr(self, key, getattr(md, key))
        for kw in kwargs:
            setattr(self, kw, kwargs[kw])
        self.model_key = model_key

    def __enter__(self):
        nmodel.register_model(self, self.__repr__())

    def __exit__(self, a, b, c):
        nmodel.models_available.pop(self.model_key)


def test_ancillary_update_init(qtbot):
    with MockModel(
        compute_ancillaries=lambda x: {
            # take initial fit parameter of E
            "E": x.get_initial_fit_parameters(
                model_ancillaries=False)["E"].value},
        parameter_anc_keys=["E"],
        parameter_anc_names=["ancillary E guess"],
        parameter_anc_units=["Pa"],
            model_key="test1"):

        main_window = pyjibe.head.PyJibe()
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.tab_preprocess.list_preproc_applied.clear()
        war.cb_autosave.setChecked(0)
        # perform simple filter
        item = QtWidgets.QListWidgetItem()
        item.setText("compute_tip_position")
        war.tab_preprocess.list_preproc_applied.addItem(item)
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(0)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        war.on_tab_changed(1)
        assert len(war.data_set[0].preprocessing) == 1
        assert war.tab_preprocess.list_preproc_applied.count() == 1
        # The ancillary parameter gets its value from the default parameters
        assert atab.item(0, 1).text() == "3000"
        assert itab.item(0, 1).text() == "3000"
        # Now we change the initial parameter "E" and move on to the next
        # curve. Ancillary parameter "F" should also change.
        itab.item(0, 1).setText("2000")
        assert atab.item(0, 1).text() == "2000"
        it = war.list_curves.topLevelItem(1)
        war.list_curves.setCurrentItem(it)
        assert itab.item(0, 1).text() == "2000"
        assert atab.item(0, 1).text() == "2000"


def test_ancillary_update_nan(qtbot):
    with MockModel(
        compute_ancillaries=lambda x: {"E": np.nan},
        parameter_anc_keys=["E"],
        parameter_anc_names=["ancillary E guess"],
        parameter_anc_units=["Pa"],
            model_key="test1"):

        main_window = pyjibe.head.PyJibe()
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.tab_preprocess.list_preproc_applied.clear()
        war.cb_autosave.setChecked(0)
        # perform simple filter
        item = QtWidgets.QListWidgetItem()
        item.setText("compute_tip_position")
        war.tab_preprocess.list_preproc_applied.addItem(item)
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(0)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        assert atab.item(0, 1).text() == "nan"
        assert itab.item(0, 1).text() == "3000"


def test_ancillary_update_preproc_change(qtbot):
    with MockModel(
        compute_ancillaries=lambda x: {
            # i.e. model works only if there are multiple preproc steps
            "E": np.nan if len(x.preprocessing) == 1 else 2345},
        parameter_anc_keys=["E"],
        parameter_anc_names=["ancillary E guess"],
        parameter_anc_units=["Pa"],
            model_key="test1"):

        main_window = pyjibe.head.PyJibe()
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.tab_preprocess.list_preproc_applied.clear()
        war.cb_autosave.setChecked(0)
        # perform simple filter
        item = QtWidgets.QListWidgetItem()
        item.setText("compute_tip_position")
        war.tab_preprocess.list_preproc_applied.addItem(item)
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(0)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        war.on_tab_changed(1)
        assert len(war.data_set[0].preprocessing) == 1
        assert war.tab_preprocess.list_preproc_applied.count() == 1
        assert atab.item(0, 1).text() == "nan"
        assert itab.item(0, 1).text() == "3000"
        # up until here this is the same as `test_update_ancillary_nan`
        # now change preprocessing
        war.tabs.setCurrentIndex(0)  # actually switch tabs like a user
        item = QtWidgets.QListWidgetItem()
        item.setText("correct_tip_offset")
        war.tab_preprocess.list_preproc_applied.addItem(item)
        war.tabs.setCurrentIndex(1)  # triggers recomputation of anc
        assert len(war.data_set[0].preprocessing) == 2
        assert war.tab_preprocess.list_preproc_applied.count() == 2
        assert atab.item(0, 1).text() == "2345"
        assert itab.item(0, 1).text() == "2345"


@pytest.mark.filterwarnings('ignore::UserWarning')
def test_apply_and_fit_all_with_bad_data(qtbot, monkeypatch):
    # setup data directory with two good and one invalid file
    td = pathlib.Path(tempfile.mkdtemp(prefix="pyjibe_test_apply_fit_all_"))
    shutil.copy2(data_path / "spot3-0192.jpk-force", td / "data1.jpk-force")
    shutil.copy2(data_path / "invalid_dataset.jpk-force",
                 td / "data2.jpk-force")
    shutil.copy2(data_path / "spot3-0192.jpk-force", td / "data3.jpk-force")
    files = sorted(td.glob("*.jpk-force"))
    # sanity checks
    assert len(files) == 3
    assert files[1].name == "data2.jpk-force"

    # monkeypatch message dialog
    message_list = []
    monkeypatch.setattr(
        QtWidgets.QMessageBox, "warning",
        lambda parent, title, message: message_list.append(message))

    # initialize
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=files)
    war = main_window.subwindows[0].widget()

    # Hit "apply model and fit all"
    qtbot.mouseClick(war.btn_fitall, QtCore.Qt.LeftButton, delay=200)

    # make sure that we got that message
    assert message_list
    assert "data2.jpk-force" in message_list[0]

    # make sure the curves got rated
    good1 = war.list_curves.topLevelItem(0)
    assert float(good1.data(2, 0)) > 0  # column 2 shows the rating
    bad = war.list_curves.topLevelItem(1)
    assert float(bad.data(2, 0)) == -1  # column 2 shows the rating
    good2 = war.list_curves.topLevelItem(2)
    assert float(good2.data(2, 0)) > 0  # column 2 shows the rating


def test_change_model_keep_parms(qtbot):
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # clear data
    war.tab_preprocess.list_preproc_applied.clear()
    war.cb_autosave.setChecked(0)
    # perform simple filter
    item = QtWidgets.QListWidgetItem()
    item.setText("compute_tip_position")
    war.tab_preprocess.list_preproc_applied.addItem(item)
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.tab_fit.table_parameters_initial
    # set value for contact point
    itab.item(3, 1).setText(str(12345))
    # change the model to pyramidal
    pyr_name = nmodel.model_hertz_three_sided_pyramid.model_name
    pyr_idx = war.tab_fit.cb_model.findText(pyr_name)
    war.tab_fit.cb_model.setCurrentIndex(pyr_idx)
    # check that contact point is still the same
    assert float(itab.item(3, 1).text()) == 12345


def test_remember_initial_params(qtbot):
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # clear data
    war.tab_preprocess.list_preproc_applied.clear()
    war.cb_autosave.setChecked(0)
    # perform simple filter
    item = QtWidgets.QListWidgetItem()
    item.setText("compute_tip_position")
    war.tab_preprocess.list_preproc_applied.addItem(item)
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.tab_fit.table_parameters_initial
    # disable weighting
    war.tab_fit.cb_weight_cp.setCheckState(0)
    # enable fitting of force offset
    itab.item(4, 0).setCheckState(0)
    # set better value for contact point
    itab.item(3, 1).setText(str(18000))
    # change standard tip radius from 10 to 5
    assert float(itab.item(1, 1).text()) == 10
    itab.item(1, 1).setText(str(5))
    cl1 = war.list_curves.currentItem()
    cl2 = war.list_curves.itemBelow(cl1)
    war.list_curves.setCurrentItem(cl2)
    assert float(itab.item(1, 1).text()) == 5
