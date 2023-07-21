"""Test of data set functionalities"""
import numpy as np
import pytest

import lmfit
from nanite.model import model_hertz_paraboloidal

import nanite.model.residuals as nres
import pyjibe.head

from helpers import MockModelModule, make_directory_with_data


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
    war.cb_autosave.setChecked(0)
    # perform simple filter
    tpp.set_preprocessing(["compute_tip_position"])
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
                       14741.256863072116,
                       atol=1,
                       rtol=0)
    assert float(ftab.item(0, 0).text()) == 14741
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


def test_hidden_parameters(qtbot):
    def get_parameter_defaults():
        params = lmfit.Parameters()
        params.add("E", value=3e3, min=0)
        params.add("R", value=10e-6, min=0, vary=False)
        params.add("_nu", value=.5, min=0, max=0.5, vary=False)
        params.add("contact_point", value=0)
        params.add("baseline", value=0)
        return params

    def model_func(delta, E, R, _nu, contact_point=0, baseline=0):
        return model_hertz_paraboloidal.hertz_paraboloidal(
            delta=delta,
            E=E,
            R=R,
            nu=_nu,
            contact_point=contact_point,
            baseline=baseline)
    with MockModelModule(
            model_key="petperpan",
            parameter_keys=["E", "R", "_nu", "contact_point", "baseline"],
            model_func=model_func,
            model=nres.get_default_modeling_wrapper(model_func),
            residual=nres.get_default_residuals_wrapper(model_func),
            get_parameter_defaults=get_parameter_defaults) as mod:
        main_window = pyjibe.head.PyJibe()
        # disable developer mode
        main_window.settings.setValue("advanced/developer mode", 0)
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # set mock model
        idx = war.tab_fit.cb_model.findData(mod.model_key)
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # Check visibility of Poisson's ratio
        itab = war.tab_fit.table_parameters_initial
        assert itab.rowCount() == 4


def test_hidden_parameters_control_in_dev_mode(qtbot):
    def get_parameter_defaults():
        params = lmfit.Parameters()
        params.add("E", value=3e3, min=0)
        params.add("R", value=10e-6, min=0, vary=False)
        params.add("_nu", value=.5, min=0, max=0.5, vary=False)
        params.add("contact_point", value=0)
        params.add("baseline", value=0)
        return params

    def model_func(delta, E, R, _nu, contact_point=0, baseline=0):
        return model_hertz_paraboloidal.hertz_paraboloidal(
            delta=delta,
            E=E,
            R=R,
            nu=_nu,
            contact_point=contact_point,
            baseline=baseline)
    with MockModelModule(
            model_key="petperpan",
            parameter_keys=["E", "R", "_nu", "contact_point", "baseline"],
            model_func=model_func,
            model=nres.get_default_modeling_wrapper(model_func),
            residual=nres.get_default_residuals_wrapper(model_func),
            get_parameter_defaults=get_parameter_defaults) as mod:
        main_window = pyjibe.head.PyJibe()
        # disable developer mode
        main_window.settings.setValue("advanced/developer mode", 1)
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # set mock model
        idx = war.tab_fit.cb_model.findData(mod.model_key)
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # Check visibility of Poisson's ratio
        itab = war.tab_fit.table_parameters_initial
        assert itab.rowCount() == 5


@pytest.mark.parametrize("method,contact_point", [
    ["gradient_zero_crossing", 1895],
    ["fit_constant_line", 1919],
    ["deviation_from_baseline", 1908],
    ])
def test_preprocessing_poc_estimation(method, contact_point):
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # clear data
    war.cb_autosave.setChecked(0)
    war.tabs.setCurrentIndex(0)
    # perform simple filter
    war.tab_preprocess.set_preprocessing(
        preprocessing=["compute_tip_position", "correct_tip_offset"],
        options={"correct_tip_offset": {"method": method}}
    )
    war.tabs.setCurrentIndex(1)
    fd = war.data_set[0]
    assert np.argmin(np.abs(fd["tip position"])) == contact_point
