import codecs
import hashlib
import pathlib
import pkg_resources

import afmformats
import h5py
from PyQt5 import uic, QtWidgets


class ConvertDialog(QtWidgets.QDialog):
    _instance_counter = 0

    def __init__(self, parent, *args, **kwargs):
        """Data conversion dialog"""
        super(ConvertDialog, self).__init__(parent=parent, *args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.head",
                                                  "dlg_tool_convert.ui")
        uic.loadUi(path_ui, self)

        self._file_list = []

        self.toolButton_browse.clicked.connect(self.on_browse)
        self.toolButton_clear.clicked.connect(self._file_list.clear)

    def _convert_merge(self):
        file, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.parent(),
            "Output file",
            "",
            "HDF5 file (*.h5)")
        if not file:
            return False
        if not file.endswith(".h5"):
            file += ".h5"
        # HDF5 format
        with h5py.File(file, "w") as h5:
            for path in self.file_list:
                fdlist = afmformats.load_data(path)
                for fdist in fdlist:
                    fdist.export(h5,
                                 metadata=self.get_metadata_keys(fdist),
                                 fmt="hdf5")
        return True

    def _convert_curve(self):
        out_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent(), "Select output directory", "")
        if out_dir:
            for path in self.file_list:
                path = pathlib.Path(path)
                epath = codecs.encode(str(path), encoding="utf-8",
                                      errors="ignore")
                stem = path.name + "_" + hashlib.md5(epath).hexdigest()[:5]
                fdlist = afmformats.load_data(path)
                for fdist in fdlist:
                    name = "{}_{}.{}".format(stem, fdist.enum, self.format)
                    opath = pathlib.Path(out_dir) / name
                    fdist.export(opath,
                                 metadata=self.get_metadata_keys(fdist),
                                 fmt=self.format)
            return True
        else:
            return False  # do not close the dialog

    def _convert_unaltered(self):
        out_dir = QtWidgets.QFileDialog.getExistingDirectory(
            self.parent(), "Select output directory", "")
        if out_dir:
            for path in self.file_list:
                path = pathlib.Path(path)
                epath = codecs.encode(str(path), encoding="utf-8",
                                      errors="ignore")
                name = "{}_{}.{}".format(path.name,
                                         hashlib.md5(epath).hexdigest()[:5],
                                         self.format)
                opath = pathlib.Path(out_dir) / name

                with h5py.File(opath, mode="w") as h5:
                    fdlist = afmformats.load_data(path)
                    for fdist in fdlist:
                        fdist.export(h5,
                                     metadata=self.get_metadata_keys(fdist),
                                     fmt=self.format)
            return True
        else:
            return False  # do not close the dialog

    @property
    def file_list(self):
        return sorted(self._file_list)

    @property
    def format(self):
        # file format
        if self.radioButton_hdf5.isChecked():
            fmt = "h5"
        else:
            fmt = "tab"
        return fmt

    def add_file(self, path):
        self.listWidget.addItem(path)
        self._file_list.append(path)

    def convert(self):
        # file grouping
        if self.radioButton_unaltered.isChecked():
            return self._convert_unaltered()
        elif self.radioButton_merge.isChecked():
            return self._convert_merge()
        else:
            return self._convert_curve()

    def done(self, r):
        if r:
            if self.listWidget.count():
                if not self.convert():
                    return
            else:
                QtWidgets.QMessageBox.information(
                    self, "No selection", "You did not select any data!")
                return  # do not close the dialog

        super(ConvertDialog, self).done(r)

    def dragEnterEvent(self, e):
        """Whether files are accepted"""
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()

    def dropEvent(self, e):
        """Add dropped files to view"""
        urls = e.mimeData().urls()
        pathlist = []
        for ff in urls:
            pp = pathlib.Path(ff.toLocalFile())
            if pp.is_dir():
                for ext in afmformats.supported_extensions:
                    pathlist += list(pp.rglob("*" + ext))
            elif pp.suffix in afmformats.supported_extensions:
                pathlist.append(pp)
        for pp in pathlist:
            self.add_file(str(pp))

    def get_metadata_keys(self, fdist):
        metadata = fdist.metadata
        if not self.checkBox_storage.isChecked():
            for key in metadata.get_summary()["storage"]:
                if key in metadata:
                    metadata.pop(key)
        return list(metadata.keys())

    def on_browse(self):
        ext = " ".join(["*"+e for e in afmformats.supported_extensions])
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(
            self.parent(),
            "Select data files",
            "",
            "All supported files ({})".format(ext))

        for ff in files:
            self.add_file(ff)
