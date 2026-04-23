from unittest import mock

from PyQt6 import QtCore, QtWidgets

import pyjibe.fd.main as fdmain


def test_autosave_override_remembered_across_instances(qtbot, tmp_path):
    # Ensure test isolation: this is a session-level value (class attribute),
    # so we must reset it explicitly at the start of the test.
    fdmain.UiForceDistance._autosave_override_session = -1

    adir = tmp_path / "data"
    adir.mkdir()
    existing = adir / "pyjibe_fit_results_leaf.tsv"
    # this file triggers the "override existing results file?" dialog.
    existing.write_text("existing\n", encoding="utf-8")

    class DummyCurve:
        # minimal stub matching the `UiForceDistance.autosave` attributes
        def __init__(self, path):
            self.path = str(path)
            self.fit_properties = {"success": True, "model_key": "dummy"}

    def build_fd(parent):
        widget = fdmain.UiForceDistance(parent)
        qtbot.addWidget(widget)
        widget.cb_autosave.setChecked(True)
        curve = DummyCurve(adir / "curve1.jpk-force")
        widget.data_set = [curve]
        # autosave() filters based on the "use" checkbox in column 3.
        item = QtWidgets.QTreeWidgetItem(widget.list_curves, ["", "", "", ""])
        item.setCheckState(3, QtCore.Qt.CheckState.Checked)
        return widget, curve

    class _Checked:
        # Simple stand-in for Qt checkable widgets used by the dialog UI.
        def __init__(self, checked):
            self._checked = checked

        def isChecked(self):
            return self._checked

    class StubDlgAutosave:
        # UI stub that selects "Override" and "Remember this choice for now".
        def setupUi(self, _dlgwin):
            self.btn_nothing = _Checked(False)
            self.btn_override = _Checked(True)
            self.btn_new = _Checked(False)
            self.cb_remember = _Checked(True)
            self.cb_disableauto = _Checked(False)

    parent1 = QtWidgets.QMdiSubWindow()
    fd1, curve1 = build_fd(parent1)

    with mock.patch.object(fdmain.export, "save_tsv_metadata_results"):
        with mock.patch.object(fdmain, "DlgAutosave", StubDlgAutosave):
            with mock.patch.object(QtWidgets.QDialog, "exec", lambda _self: 1):
                fd1.autosave(curve1)

    # The remembered choice is stored session-wide (across subwindows).
    assert fdmain.UiForceDistance._autosave_override_session == 1

    parent2 = QtWidgets.QMdiSubWindow()
    fd2, curve2 = build_fd(parent2)

    class RaiseDlgAutosave:
        # if we remembered the choice, autosave() won't construct the dialog.
        def __init__(self, *args, **kwargs):
            raise AssertionError("DlgAutosave should not be constructed")

    with mock.patch.object(fdmain.export, "save_tsv_metadata_results"):
        with mock.patch.object(fdmain, "DlgAutosave", RaiseDlgAutosave):
            fd2.autosave(curve2)
