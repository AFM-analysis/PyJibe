"""Test of data set functionalities"""
import pathlib
import shutil
import tempfile

import nanite.model as nmodel
import numpy as np
import pytest
from PyQt6 import QtCore, QtWidgets

import pyjibe.head

from helpers import MockModelModule, make_directory_with_data

data_path = pathlib.Path(__file__).parent / "data"


def test_ancillary_update_init(qtbot):
    with MockModelModule(
            compute_ancillaries=lambda x: {
                # take initial fit parameter of E
                "E": x.get_initial_fit_parameters(
                    model_ancillaries=False)["E"].value},
            parameter_anc_keys=["E"],
            parameter_anc_names=["ancillary E guess"],
            parameter_anc_units=["Pa"],
            model_key="test1"):
        main_window = pyjibe.head.PyJibe()
        qtbot.addWidget(main_window)
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        war.on_tab_changed()
        assert len(war.data_set[0].preprocessing) == 1
        assert len(war.tab_preprocess.current_preprocessing()[0]) == 1
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
        main_window.close()


def test_ancillary_update_nan(qtbot):
    with MockModelModule(
            compute_ancillaries=lambda x: {"E": np.nan},
            parameter_anc_keys=["E"],
            parameter_anc_names=["ancillary E guess"],
            parameter_anc_units=["Pa"],
            model_key="test1"):
        main_window = pyjibe.head.PyJibe()
        qtbot.addWidget(main_window)
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        assert atab.item(0, 1).text() == "nan"
        assert itab.item(0, 1).text() == "3000"
        main_window.close()


def test_ancillary_update_preproc_change(qtbot):
    with MockModelModule(
            compute_ancillaries=lambda x: {
                # i.e. model works only if there are multiple preproc steps
                "E": np.nan if len(x.preprocessing) == 1 else 2345},
            parameter_anc_keys=["E"],
            parameter_anc_names=["ancillary E guess"],
            parameter_anc_units=["Pa"],
            model_key="test1"):

        main_window = pyjibe.head.PyJibe()
        qtbot.addWidget(main_window)
        main_window.load_data(files=make_directory_with_data(2))
        war = main_window.subwindows[0].widget()
        # clear data
        war.cb_autosave.setChecked(0)
        # perform simple filter
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        # disable weighting
        war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
        # set mock model
        idx = war.tab_fit.cb_model.findData("test1")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        # perform fitting with standard parameters
        # set initial parameters in user interface
        itab = war.tab_fit.table_parameters_initial
        atab = war.tab_fit.table_parameters_anc
        war.on_tab_changed()
        assert len(war.data_set[0].preprocessing) == 1
        assert len(war.tab_preprocess.current_preprocessing()[0]) == 1
        assert atab.item(0, 1).text() == "nan"
        assert itab.item(0, 1).text() == "3000"
        # up until here this is the same as `test_update_ancillary_nan`
        # now change preprocessing
        war.tabs.setCurrentIndex(0)  # actually switch tabs like a user
        # manually check the "correct_tip_offset" widget
        for pwid, k in war.tab_preprocess._map_widgets_to_preproc_ids.items():
            if k == "correct_tip_offset":
                pwid.setChecked(True)
        war.tabs.setCurrentIndex(1)  # triggers recomputation of anc
        assert len(war.data_set[0].preprocessing) == 2
        assert len(war.tab_preprocess.current_preprocessing()[0]) == 2
        assert atab.item(0, 1).text() == "2345"
        assert itab.item(0, 1).text() == "2345"
        main_window.close()


def test_anc_update_does_not_recurse_via_itab_signal(qtbot):
    """Writing an ancillary value into itab must not re-trigger itself."""
    calls = []

    def compute_anc(x):
        calls.append(1)
        return {"E": 4242}

    with MockModelModule(
            compute_ancillaries=compute_anc,
            parameter_anc_keys=["E"],
            parameter_anc_names=["ancillary E guess"],
            parameter_anc_units=["Pa"],
            model_key="test_recursion"):
        main_window = pyjibe.head.PyJibe()
        qtbot.addWidget(main_window)
        main_window.load_data(files=make_directory_with_data(1))
        war = main_window.subwindows[0].widget()
        war.cb_autosave.setChecked(0)
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        idx = war.tab_fit.cb_model.findData("test_recursion")
        war.tab_fit.cb_model.setCurrentIndex(idx)

        fdist = war.data_set[0]
        itab = war.tab_fit.table_parameters_initial
        itab.blockSignals(True)
        itab.item(0, 1).setText("0")  # real change, not a no-op
        itab.blockSignals(False)

        calls.clear()
        war.tab_fit.anc_update_parameters(fdist)
        assert len(calls) == 1, (
            f"anc_update_parameters recursed via itab's itemChanged "
            f"signal ({len(calls)} calls instead of 1)")
        main_window.close()


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
    qtbot.addWidget(main_window)
    main_window.load_data(files=files)
    war = main_window.subwindows[0].widget()
    war.tab_preprocess.set_preprocessing(
        ["compute_tip_position", "correct_force_offset", "correct_tip_offset"])

    # Hit "apply model and fit all"
    qtbot.mouseClick(war.btn_fitall, QtCore.Qt.MouseButton.LeftButton,
                     delay=200)

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
    main_window.close()


def test_change_model_keep_parms(qtbot):
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # clear data
    war.cb_autosave.setChecked(0)
    # perform simple filter
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
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
    main_window.close()


def test_fit_all_matches_single_fit(qtbot):
    """on_fit_all must produce the same TSV output as fitting one-by-one."""
    files = make_directory_with_data(2)
    tsv_path = files[0].parent / "pyjibe_fit_results_leaf.tsv"

    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=files)
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(True)
    war._autosave_override = 1  # always overwrite, avoid dialog
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)

    # Click through both files via the single-curve path
    cl1 = war.list_curves.currentItem()
    cl2 = war.list_curves.itemBelow(cl1)
    war.list_curves.setCurrentItem(cl1)
    war.list_curves.setCurrentItem(cl2)
    assert tsv_path.exists(), "autosave TSV not created after single-fit"
    single_tsv = tsv_path.read_text()

    # Re-fit everything via fit-all; TSV must be byte-for-byte identical
    war.on_fit_all()
    fitall_tsv = tsv_path.read_text()

    assert single_tsv == fitall_tsv
    main_window.close()


def test_fit_all_matches_single_fit_kvm(qtbot):
    """fit-all must produce the same TSV as single-fit for the KVM model.

    KVM has ancillary parameters (eta, time_ind) that are derived by fitting
    a preliminary Hertz model to each curve. The KVM model is loaded via
    PyJibe's extension system at startup.
    """
    files = make_directory_with_data(2)
    tsv_path = files[0].parent / "pyjibe_fit_results_leaf.tsv"

    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=files)
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(True)
    war._autosave_override = 1  # always overwrite, avoid dialog
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)

    # Switch to the KVM model (loaded via PyJibe's extension system)
    idx = war.tab_fit.cb_model.findData("hertz_corr_visco_KVM")
    if idx < 0:
        pytest.skip("KVM model extension not installed in this environment")
    war.tab_fit.cb_model.setCurrentIndex(idx)

    # Click through both files via the single-curve path
    cl1 = war.list_curves.currentItem()
    cl2 = war.list_curves.itemBelow(cl1)
    war.list_curves.setCurrentItem(cl1)
    war.list_curves.setCurrentItem(cl2)
    assert tsv_path.exists(), "autosave TSV not created after single-fit"
    single_tsv = tsv_path.read_text()

    # Re-fit everything via fit-all; TSV must be byte-for-byte identical
    war.on_fit_all()
    fitall_tsv = tsv_path.read_text()

    assert single_tsv == fitall_tsv


def test_fit_all_rates_last_curve_before_final_autosave(qtbot):
    """on_fit_all must not leave the last curve's rating as nan"""
    files = make_directory_with_data(2)
    tsv_path = files[0].parent / "pyjibe_fit_results_leaf.tsv"

    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=files)
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(True)
    war._autosave_override = 1
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)

    # call fit-all directly on freshly-loaded curves - no prior
    # single-click pass
    war.on_fit_all()

    rows = tsv_path.read_text().splitlines()
    header = rows[0].split("\t")
    regressor_col = header.index("Regressor")
    rating_col = header.index("Rating")
    assert len(rows) == 3  # header + 2 curves
    for row in rows[1:]:
        cells = row.split("\t")
        assert cells[regressor_col] != "nan"
        assert cells[rating_col] != "nan"
    main_window.close()


def test_remember_initial_params(qtbot):
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # clear data
    war.cb_autosave.setChecked(0)
    # perform simple filter
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.tab_fit.table_parameters_initial
    # disable weighting
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
    # enable fitting of force offset
    itab.item(4, 0).setCheckState(QtCore.Qt.CheckState.Unchecked)
    # set better value for contact point
    itab.item(3, 1).setText(str(18000))
    # change standard tip radius from 10 to 5
    assert float(itab.item(1, 1).text()) == 10
    itab.item(1, 1).setText(str(5))
    cl1 = war.list_curves.currentItem()
    cl2 = war.list_curves.itemBelow(cl1)
    war.list_curves.setCurrentItem(cl2)
    assert float(itab.item(1, 1).text()) == 5
    main_window.close()


def test_set_indentation_depth_manually_infdoublespinbox(qtbot):
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.tab_fit.table_parameters_initial
    # set value for contact point
    itab.item(3, 1).setText(str(12345))
    # change the model to pyramidal
    pyr_name = nmodel.model_hertz_three_sided_pyramid.model_name
    pyr_idx = war.tab_fit.cb_model.findText(pyr_name)
    war.tab_fit.cb_model.setCurrentIndex(pyr_idx)
    # set left fitting range
    for text_entered, resulting_value in [
        ["-1.40", -1.4],
        ["1...2", 1.2],
        ["1.0e-4", 1e-4],
        ["inf", np.inf],
        ["1.10201", 1.10201],
        ["1.001", 1.001],
        ["-1.04", -1.04]
    ]:
        war.tab_fit.sp_range_1.clear()
        qtbot.keyClicks(war.tab_fit.sp_range_1, text_entered)
        assert war.tab_fit.sp_range_1.value() == resulting_value
    main_window.close()


def test_show_fit_line_toggle(qtbot):
    """Toggle cb_show_fit_line hides/shows the fit line on the plot."""
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(0)
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
    war.on_tab_changed()

    mpl = war.widget_plot_fd.mpl_curve
    # fit line should be visible by default
    assert mpl.plots["fit"].get_visible()

    # uncheck the toggle — fit line should disappear
    war.cb_show_fit_line.setChecked(False)
    war.on_mpl_curve_update()
    assert not mpl.plots["fit"].get_visible()

    # re-check — fit line should reappear
    war.cb_show_fit_line.setChecked(True)
    war.on_mpl_curve_update()
    assert mpl.plots["fit"].get_visible()
    main_window.close()


def test_show_chi_sqr_annotation_after_fit(qtbot):
    """Chi^2 annotation should be visible after a successful fit."""
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(2))
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(0)
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.CheckState.Unchecked)
    war.on_tab_changed()

    mpl = war.widget_plot_fd.mpl_curve
    assert mpl.ann_chi2.get_visible()
    text = mpl.ann_chi2.get_text()
    assert text.startswith(r"$\chi^2$")
    chi2_value = float(text.split("=")[1].strip())
    assert 0.0 <= chi2_value <= 1.0
    main_window.close()


def test_swap_model_does_not_raise_and_updates_labels(qtbot):
    """Model swap must not crash and itab must show new model params.

    Notes
    -----
    In nanite>=4.2.3, FitProperties.__setitem__ already resets
    "params_initial" whenever "model_key" changes (see nanite/fit.py),
    so the stale-params KeyError from 8140997 is not reproducible via
    normal UI actions here. This guards against a crash/label
    regression during model swap instead.
    """
    main_window = pyjibe.head.PyJibe()
    qtbot.addWidget(main_window)
    main_window.load_data(files=make_directory_with_data(1))
    war = main_window.subwindows[0].widget()
    war.cb_autosave.setChecked(0)
    war.tab_preprocess.set_preprocessing(["compute_tip_position"])

    fdist = war.data_set[0]
    assert fdist.fit_properties["model_key"] == "hertz_para"
    assert "R" in fdist.fit_properties["params_initial"]

    pyr_name = nmodel.model_hertz_three_sided_pyramid.model_name
    pyr_idx = war.tab_fit.cb_model.findText(pyr_name)
    war.tab_fit.cb_model.setCurrentIndex(pyr_idx)  # must not raise

    itab = war.tab_fit.table_parameters_initial
    labels = [itab.verticalHeaderItem(rr).text()
              for rr in range(itab.rowCount())]
    assert any("Face Angle" in lb for lb in labels)
    assert fdist.fit_properties["model_key"] == "hertz_pyr3s"
    main_window.close()


def test_swap_model_recomputes_ancillary_not_cached(qtbot):
    """Ancillary cache must be cleared (not reused) across a model swap."""
    with MockModelModule(
            compute_ancillaries=lambda x: {"E": 1000},
            parameter_anc_keys=["E"],
            parameter_anc_names=["ancillary E guess"],
            parameter_anc_units=["Pa"],
            model_key="test_anc_a"):
        with MockModelModule(
                compute_ancillaries=lambda x: {"E": 9999},
                parameter_anc_keys=["E"],
                parameter_anc_names=["ancillary E guess"],
                parameter_anc_units=["Pa"],
                model_key="test_anc_b"):
            main_window = pyjibe.head.PyJibe()
            qtbot.addWidget(main_window)
            main_window.load_data(files=make_directory_with_data(1))
            war = main_window.subwindows[0].widget()
            war.cb_autosave.setChecked(0)
            war.tab_preprocess.set_preprocessing(
                ["compute_tip_position"])
            war.tab_fit.cb_weight_cp.setCheckState(
                QtCore.Qt.CheckState.Unchecked)

            idx_a = war.tab_fit.cb_model.findData("test_anc_a")
            war.tab_fit.cb_model.setCurrentIndex(idx_a)
            fdist = war.data_set[0]

            # real successful fit under model A populates _anc_cache
            war.tab_fit.fit_approach_retract(fdist)
            assert fdist.fit_properties.get("success")
            war.tab_fit.anc_update_parameters(fdist)
            assert fdist._anc_cache  # sanity: cache now populated

            idx_b = war.tab_fit.cb_model.findData("test_anc_b")
            war.tab_fit.cb_model.setCurrentIndex(idx_b)  # must recompute

            atab = war.tab_fit.table_parameters_anc
            assert atab.item(0, 1).text() == "9999"  # fresh, not "1000"
            main_window.close()


def test_swap_to_kvm_output_matches_unswapped_fit(qtbot):
    """A confirmed fit under the default model, followed by a swap to
    KVM, must not change KVM's ancillary-seeded initial defaults or
    its fit output compared to swapping without that extra prior fit.

    KVM's "eta"/"time_ind" are fixed (non-varying) parameters seeded
    from a real auxiliary fit (see compute_ancillaries in the KVM
    extension) - unlike hertz_para/hertz_pyr3s used elsewhere in this
    file, a stale ancillary cache here does not just cosmetically
    mislabel the UI: it silently falls back to KVM's own hard-coded
    literal defaults (eta=0.5, time_ind=1), which are baked into the
    fitted model equation and change the final numeric fit output.
    """
    tsv_name = "pyjibe_fit_results_leaf.tsv"

    def setup_window(files):
        main_window = pyjibe.head.PyJibe()
        qtbot.addWidget(main_window)
        main_window.load_data(files=files)
        war = main_window.subwindows[0].widget()
        war.cb_autosave.setChecked(True)
        war._autosave_override = 1
        war.tab_preprocess.set_preprocessing(["compute_tip_position"])
        war.tab_fit.cb_weight_cp.setCheckState(
            QtCore.Qt.CheckState.Unchecked)
        return main_window, war

    def swap_to_kvm_and_export(war, files):
        idx = war.tab_fit.cb_model.findData("hertz_corr_visco_KVM")
        if idx < 0:
            pytest.skip(
                "KVM model extension not installed in this environment")
        war.tab_fit.cb_model.setCurrentIndex(idx)
        fdist = war.data_set[0]
        assert fdist.fit_properties.get("success")
        kvm_defaults = war.tab_fit.fit_model.get_parameter_defaults()

        # eta/time_ind must be the freshly computed ancillary guesses,
        # not KVM's own hard-coded literal defaults (which is what a
        # stale/mismatched ancillary cache would silently fall back to)
        itab = war.tab_fit.table_parameters_initial
        eta_row = next(
            rr for rr in range(itab.rowCount())
            if itab.verticalHeaderItem(rr).text().startswith("viscosity"))
        time_row = next(
            rr for rr in range(itab.rowCount())
            if itab.verticalHeaderItem(rr).text().startswith(
                "Time to indent"))
        assert (float(itab.item(eta_row, 1).text())
                != kvm_defaults["eta"].value)
        assert (float(itab.item(time_row, 1).text())
                != kvm_defaults["time_ind"].value)

        return (files[0].parent / tsv_name).read_text()

    # path A: fit under the default model first, then swap to KVM
    files_a = make_directory_with_data(1)
    main_window_a, war_a = setup_window(files_a)
    fdist_a = war_a.data_set[0]
    war_a.tab_fit.fit_approach_retract(fdist_a)  # confirmed hertz_para fit
    assert fdist_a.fit_properties.get("success")
    tsv_a = swap_to_kvm_and_export(war_a, files_a)
    main_window_a.close()

    # path B: identical, but without the extra prior fit
    files_b = make_directory_with_data(1)
    main_window_b, war_b = setup_window(files_b)
    tsv_b = swap_to_kvm_and_export(war_b, files_b)
    main_window_b.close()

    assert tsv_a == tsv_b
