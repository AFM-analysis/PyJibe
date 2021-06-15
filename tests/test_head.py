import io
import pathlib
import shutil
import tempfile
from unittest import mock

import pyjibe
import pyjibe.head


data_path = pathlib.Path(__file__).parent / "data"


def test_init_print_version(qtbot):
    """I just wanted to show off how good I am with mock and pytest"""
    mock_stdout = io.StringIO()
    mock_exit = mock.Mock()

    with mock.patch("sys.argv", ["", "--version"]):
        with mock.patch("sys.exit", mock_exit):
            with mock.patch('sys.stdout', mock_stdout):
                mw = pyjibe.head.PyJibe()
                mw.close()

    assert mock_exit.call_args.args[0] == 0
    assert mock_stdout.getvalue().strip() == pyjibe.__version__


def test_on_about(qtbot):
    mock_about = mock.Mock()
    with mock.patch("PyQt5.QtWidgets.QMessageBox.about", mock_about):
        mw = pyjibe.head.PyJibe()
        mw.on_about()
        mw.close()

    assert mock_about.call_args.args[1] == f"PyJibe {pyjibe.__version__}"
    assert "PyJibe" in mock_about.call_args.args[2]


def test_on_documentation(qtbot):
    mock_wbopen = mock.Mock()
    with mock.patch("webbrowser.open", mock_wbopen):
        mw = pyjibe.head.PyJibe()
        mw.on_documentation()
        mw.close()

    assert mock_wbopen.call_args.args[0] == "https://pyjibe.readthedocs.io"


def test_on_open_bulk(qtbot):
    def mock_selected_files(self):
        tdir = tempfile.mkdtemp(prefix="pyjibe_test_open_bulk_")
        t2 = pathlib.Path(tdir) / "spot1.jpk-force"
        t3 = pathlib.Path(tdir) / "spot2.jpk-force"
        t4 = pathlib.Path(tdir) / "spot3.jpk-force"
        shutil.copy2(data_path / "spot3-0192.jpk-force", t2)
        shutil.copy2(data_path / "spot3-0192.jpk-force", t3)
        shutil.copy2(data_path / "spot3-0192.jpk-force", t4)
        return [t2, t3, t4]

    mw = pyjibe.head.PyJibe()

    with mock.patch("pyjibe.head.custom_widgets."
                    "DirectoryDialogMultiSelect.selectedFiles",
                    mock_selected_files):
        with mock.patch("pyjibe.head.custom_widgets."
                        "DirectoryDialogMultiSelect.exec_"):
            mw.on_open_bulk()

    assert len(mw.subwindows) == 1
    war = mw.subwindows[0].widget()
    assert war.list_curves.topLevelItemCount() == 3
    mw.close()


def test_on_open_multiple(qtbot):
    def mock_selected_files(self):
        tdir = tempfile.mkdtemp(prefix="pyjibe_test_open_bulk_")
        t2 = pathlib.Path(tdir) / "1" / "spot1.jpk-force"
        t3 = pathlib.Path(tdir) / "2" / "spot2.jpk-force"
        t4 = pathlib.Path(tdir) / "3" / "spot3.jpk-force"
        t2.parent.mkdir()
        t3.parent.mkdir()
        t4.parent.mkdir()
        shutil.copy2(data_path / "spot3-0192.jpk-force", t2)
        shutil.copy2(data_path / "spot3-0192.jpk-force", t3)
        shutil.copy2(data_path / "spot3-0192.jpk-force", t4)
        return [t2, t3, t4]

    mw = pyjibe.head.PyJibe()

    with mock.patch("pyjibe.head.custom_widgets."
                    "DirectoryDialogMultiSelect.selectedFiles",
                    mock_selected_files):
        with mock.patch("pyjibe.head.custom_widgets."
                        "DirectoryDialogMultiSelect.exec_"):
            mw.on_open_multiple()

    assert len(mw.subwindows) == 3
    war = mw.subwindows[0].widget()
    assert war.list_curves.topLevelItemCount() == 1
    mw.close()


def test_on_open_single(qtbot):
    def mock_get_open_filenames(*args, **kwargs):
        tdir = tempfile.mkdtemp(prefix="pyjibe_test_open_bulk_")
        t2 = pathlib.Path(tdir) / "spot1.jpk-force"
        shutil.copy2(data_path / "spot3-0192.jpk-force", t2)
        return [t2], None

    mw = pyjibe.head.PyJibe()

    with mock.patch("PyQt5.QtWidgets.QFileDialog.getOpenFileNames",
                    mock_get_open_filenames):
        mw.on_open_single()

    assert len(mw.subwindows) == 1
    war = mw.subwindows[0].widget()
    assert war.list_curves.topLevelItemCount() == 1
    mw.close()
