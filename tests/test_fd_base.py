"""Test of data set functionalities"""
import pathlib

from PyQt5 import QtWidgets

import pyjibe.head


here = pathlib.Path(__file__).parent
jpkfile = here / "data" / "spot3-0192.jpk-force"


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


def test_simple(qtbot):
    """Open the main window and close it again"""
    main_window = pyjibe.head.PyJibe()
    main_window.close()


def test_clear_and_verify_data(qtbot):
    cleanup_autosave(jpkfile)
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=[jpkfile])
    war = main_window.subwindow_data[0]
    # clear data
    war.list_preproc_applied.clear()
    war.cb_autosave.setChecked(0)
    # perform simple filter
    item = QtWidgets.QListWidgetItem()
    item.setText("compute_tip_position")
    war.list_preproc_applied.addItem(item)
    # perform fitting with standard parameters
    # set initial parameters in user interface
    itab = war.table_parameters_initial
    # disable weighting
    war.cb_weight_cp.setCheckState(0)
    # enable fitting of force offset
    itab.item(4, 0).setCheckState(0)
    # set better value for contact point
    itab.item(3, 1).setText(str(18000))
    apret = war.data_set[0]
    war.fit_approach_retract(apret)
    # Now check something
    ftab = war.table_parameters_fitted
    # E
    assert float(ftab.item(0, 0).text()) == 14741.958
    # contact_point
    assert float(ftab.item(1, 0).text()) == 18029.310
    # baseline_offset
    assert float(ftab.item(2, 0).text()) == -480.669
    cleanup_autosave(jpkfile)


def test_fit_all(qtbot):
    """Perform a simple fit with the standard parameters"""
    cleanup_autosave(jpkfile)
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=[jpkfile, jpkfile])
    war = main_window.subwindow_data[0]
    war.cb_autosave.setChecked(0)
    war.on_fit_all()
    a1 = war.data_set[0]
    a2 = war.data_set[1]
    assert a1.fit_properties == a2.fit_properties
    cleanup_autosave(jpkfile)
