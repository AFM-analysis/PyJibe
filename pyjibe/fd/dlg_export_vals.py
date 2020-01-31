import pkg_resources

from PyQt5 import uic, QtWidgets

from . import export


class ExportDialog(QtWidgets.QDialog):
    _instance_counter = 0

    def __init__(self, parent, fdist_list, identifier, *args, **kwargs):
        """Base class for force-indentation analysis"""
        super(ExportDialog, self).__init__(parent=parent, *args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "dlg_export_vals.ui")
        uic.loadUi(path_ui, self)

        self.fdist_list = fdist_list
        self.identifier = identifier

    def done(self, r):
        if r:
            fname, _e = QtWidgets.QFileDialog.getSaveFileName(
                self.parent(),
                "Save metadata and results",
                "pyjibe_export_{:03d}.tsv".format(self.identifier),
                "Tab Separated Values (*.tsv)"
            )

            if fname:
                if not fname.endswith(".tsv"):
                    fname += ".tsv"
                user_choices = {
                    "acquisition": self.checkBox_acquisition,
                    "dataset": self.checkBox_dataset,
                    "qmap": self.checkBox_qmap,
                    "setup": self.checkBox_setup,
                    "storage": self.checkBox_storage,
                    "params_initial": self.checkBox_initial,
                    "params_fitted": self.checkBox_fitted,
                    "params_ancillary": self.checkBox_ancillary,
                    "rating": self.checkBox_rating,
                }
                which = []
                for mdat in user_choices:
                    if user_choices[mdat].isChecked():
                        which.append(mdat)

                export.save_tsv_metadata_results(filename=fname,
                                                 fdist_list=self.fdist_list,
                                                 which=which)
        super(ExportDialog, self).done(r)
