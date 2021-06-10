"""Test of data set functionalities"""
import numpy as np
from PyQt5 import QtWidgets

import pyjibe.head

from helpers import make_directory_with_data


def test_simple(qtbot):
    """Open the main window and close it again"""
    main_window = pyjibe.head.PyJibe()
    main_window.close()


def test_clear_and_verify_data(qtbot):
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data())
    war = main_window.subwindows[0].widget()
    # clear data
    tpp = war.tab_preprocess
    tpp.list_preproc_applied.clear()
    war.cb_autosave.setChecked(0)
    # perform simple filter
    item = QtWidgets.QListWidgetItem()
    item.setText("compute_tip_position")
    tpp.list_preproc_applied.addItem(item)
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.tab_fit.table_parameters_initial
    # disable weighting
    war.tab_fit.cb_weight_cp.setCheckState(0)
    # enable fitting of force offset
    itab.item(4, 0).setCheckState(0)
    # set better value for contact point
    itab.item(3, 1).setText(str(18000))
    apret = war.data_set[0]
    war.tab_fit.fit_approach_retract(apret)
    # Now check something
    ftab = war.tab_fit.table_parameters_fitted
    # E
    assert np.allclose(apret.fit_properties["params_fitted"]["E"].value,
                       14741.958242422093,
                       atol=1e-4,
                       rtol=0)
    assert float(ftab.item(0, 0).text()) == 14742
    # contact_point
    assert float(ftab.item(1, 0).text()) == 18029
    # baseline_offset
    assert float(ftab.item(2, 0).text()) == -480.67


def test_fit_all(qtbot):
    """Perform a simple fit with the standard parameters"""
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(0)
    war.on_fit_all()
    a1 = war.data_set[0]
    a2 = war.data_set[1]
    assert a1.fit_properties == a2.fit_properties
