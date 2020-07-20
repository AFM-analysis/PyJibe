"""Test of data set functionalities"""
import pathlib

import lmfit
import numpy as np
from PyQt5 import QtWidgets
import pytest

import nanite.model
from nanite.model import weight
import pyjibe.head


here = pathlib.Path(__file__).parent
jpkfile = here / "data" / "spot3-0192.jpk-force"


class MockModelExpr():
    def __init__(self, **kwargs):
        """E and E1 add up to the actual emodulus. E1 is varied indirectly"""
        self.model_doc = """Mock model with constraint"""
        self.model_func = MockModelExpr.hertz_constraint
        self.model_key = "hertz_constraint"
        self.model_name = "Hertz with constraint "
        self.parameter_keys = ["E", "R", "nu", "virtual_parameter",
                               "E1", "contact_point", "baseline"]
        self.parameter_names = ["Young's Modulus", "Tip Radius",
                                "Poisson's Ratio", "Virtual Parameter",
                                "Another Modulus", "Contact Point",
                                "Force Baseline"]
        self.parameter_units = ["Pa", "m", "", "Pa", "Pa", "m", "N"]
        self.valid_axes_x = ["tip position"]
        self.valid_axes_y = ["force"]

    @staticmethod
    def get_parameter_defaults():
        # The order of the parameters must match the order
        # of ´parameter_names´ and ´parameter_keys´.
        params = lmfit.Parameters()
        params.add("E", value=1e3, min=0, vary=False)
        params.add("R", value=10e-6, vary=False)
        params.add("nu", value=.5, vary=False)
        params.add("virtual_parameter", value=10, min=0, vary=True)
        params.add("E1", expr="virtual_parameter+E")
        params.add("contact_point", value=0)
        params.add("baseline", value=0)
        return params

    @staticmethod
    def hertz_constraint(delta, E, R, nu, virtual_parameter, E1,
                         contact_point=0, baseline=0):
        aa1 = 4 / 3 * E1 / (1 - nu ** 2) * np.sqrt(R)

        root = contact_point - delta
        pos = root > 0
        bb = np.zeros_like(delta)
        bb[pos] = (root[pos]) ** (3 / 2)
        cc = np.zeros_like(delta)
        cc[pos] = 1 - 0.15 * root[pos] / R
        return aa1 * bb * cc + baseline

    @staticmethod
    def model(params, x):
        if x[0] < x[-1]:
            revert = True
        else:
            revert = False
        if revert:
            x = x[::-1]
        mf = MockModelExpr.hertz_constraint(
            E=params["E"].value,
            delta=x,
            R=params["R"].value,
            nu=params["nu"].value,
            virtual_parameter=params["virtual_parameter"].value,
            E1=params["E1"].value,
            contact_point=params["contact_point"].value,
            baseline=params["baseline"].value)
        if revert:
            return mf[::-1]
        return mf

    @staticmethod
    def residual(params, delta, force, weight_cp=5e-7):
        """ Compute residuals for fitting

        Parameters
        ----------
        params: lmfit.Parameters
            The fitting parameters for `model`
        delta: 1D ndarray of lenght M
            The indentation distances
        force: 1D ndarray of length M
            The corresponding force data
        weight_cp: positive float or zero/False
            The distance from the contact point until which
            linear weights will be applied. Set to zero to
            disable weighting.
        """
        md = MockModelExpr.model(params, delta)
        resid = force - md

        if weight_cp:
            # weight the curve so that the data around the contact_point do
            # not affect the fit so much.
            weights = weight.weight_cp(
                cp=params["contact_point"].value,
                delta=delta,
                weight_dist=weight_cp)
            resid *= weights
        return resid

    def __enter__(self):
        nanite.model.register_model(self, self.__repr__())
        return self

    def __exit__(self, a, b, c):
        nanite.model.models_available.pop(self.model_key)


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


@pytest.fixture(autouse=True)
def run_around_tests():
    # Code that will run before your test, for example:
    cleanup_autosave(jpkfile)
    # A test function will be run at this point
    yield
    # Code that will run after your test, for example:
    cleanup_autosave(jpkfile)


def test_model_expr_base(qtbot):
    """Expressions sanity check

    This test is just to make sure that parameters that have an
    expression are not overridden by the UI.
    """
    with MockModelExpr() as mod:
        main_window = pyjibe.head.PyJibe()
        main_window.load_data(files=[jpkfile, jpkfile])
        war = main_window.subwindows[0].widget()
        # clear data
        war.tab_preprocess.list_preproc_applied.clear()
        war.cb_autosave.setChecked(0)
        # perform simple filter
        item = QtWidgets.QListWidgetItem()
        item.setText("compute_tip_position")
        war.tab_preprocess.list_preproc_applied.addItem(item)
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
        assert np.allclose(parmsf["E1"].value, 15388.14166)


if __name__ == "__main__":
    with MockModelExpr() as mod:
        from pyjibe.__main__ import main
        main()
