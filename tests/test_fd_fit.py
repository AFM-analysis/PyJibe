"""Test of data set functionalities"""
import pathlib

from PyQt5 import QtWidgets

import nanite.model as nmodel
import pyjibe.head


here = pathlib.Path(__file__).parent
jpkfile = here / "data" / "spot3-0192.jpk-force"


def cleanup_autosave(jpkfile):
    """Remove autosave files"""
    path = jpkfile.parent
    files = path.glob("*.tsv")
    files = [f for f in files if f.name.startswith("pyjibe_")]
    [f.unlink() for f in files]


def test_remember_initial_params(qtbot):
    cleanup_autosave(jpkfile)
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=[jpkfile, jpkfile])
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
    # change standard tip radius from 10 to 5
    assert float(itab.item(1, 1).text()) == 10
    itab.item(1, 1).setText(str(5))
    cl1 = war.list_curves.currentItem()
    cl2 = war.list_curves.itemBelow(cl1)
    war.list_curves.setCurrentItem(cl2)
    assert float(itab.item(1, 1).text()) == 5
    cleanup_autosave(jpkfile)


def test_change_model_keep_parms(qtbot):
    cleanup_autosave(jpkfile)
    main_window = pyjibe.head.PyJibe()
    main_window.load_data(files=[jpkfile, jpkfile])
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
    # set value for contact point
    itab.item(3, 1).setText(str(12345))
    # change the model to pyramidal
    pyr_name = nmodel.model_hertz_three_sided_pyramid.model_name
    pyr_idx = war.cb_model.findText(pyr_name)
    war.cb_model.setCurrentIndex(pyr_idx)
    # check that contact point is still the same
    assert float(itab.item(3, 1).text()) == 12345
    cleanup_autosave(jpkfile)
