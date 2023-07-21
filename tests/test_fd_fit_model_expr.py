"""Test model with expression parameters"""
import numpy as np

import pyjibe.head

from helpers import MockModelModuleExpr, make_directory_with_data


def test_model_expr_base(qtbot):
    """Expressions sanity check

    This test is just to make sure that parameters that have an
    expression are not overridden by the UI.
    """
    with MockModelModuleExpr() as mod:
        main_window = pyjibe.head.PyJibe()
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # set mock model
        idx = war.tab_fit.cb_model.findData(mod.model_key)
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # Now there should be fit results
        itab = war.tab_fit.table_parameters_initial
        # set better value for contact point
        itab.item(5, 1).setText(str(18000))
        fdist = war.data_set[0]
        parmsi = fdist.fit_properties["params_initial"]
        parmsf = fdist.fit_properties["params_fitted"]
        assert parmsi["E1"].expr == "virtual_parameter+E"
        assert parmsf["E1"].expr == "virtual_parameter+E"
        assert np.allclose(parmsf["E1"].value, 15388.787369767488,
                           atol=10)  # this fit is not very stable
