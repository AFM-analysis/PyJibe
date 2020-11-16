import hashlib
import io
import os
import pkg_resources
import time

import afmformats
import nanite
import nanite.fit as nfit
import numpy as np
from PyQt5 import uic, QtCore, QtGui, QtWidgets

from .. import colormap

from . import dlg_export_vals
from . import export
from . import rating_base
from . import rating_iface


# load QWidget from ui file
dlg_autosave_path = pkg_resources.resource_filename("pyjibe.fd",
                                                    "dlg_autosave_design.ui")
DlgAutosave = uic.loadUiType(dlg_autosave_path)[0]


class UiForceDistance(QtWidgets.QWidget):
    _instance_counter = 0

    def __init__(self, *args, **kwargs):
        """Base class for force-indentation analysis"""
        super(UiForceDistance, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd", "main.ui")
        uic.loadUi(path_ui, self)

        UiForceDistance._instance_counter += 1
        title = "Force-Distance #{}".format(self._instance_counter)
        self.parent().setWindowTitle(title)

        self.data_set = nanite.IndentationGroup()

        # rating scheme
        self.rating_scheme_setup()

        # Signals
        # tabs
        self.tabs.currentChanged.connect(self.on_tab_changed)
        # fitting / parameters
        self.tab_edelta.sp_delta_num_samples.valueChanged.connect(
            self.on_params_init)
        self.btn_fitall.clicked.connect(self.on_fit_all)
        self.tab_fit.cb_delta_select.currentIndexChanged.connect(
            self.tab_edelta.cb_delta_select.setCurrentIndex)
        self.tab_edelta.cb_delta_select.currentIndexChanged.connect(
            self.tab_fit.cb_delta_select.setCurrentIndex)
        self.tab_fit.sp_range_1.valueChanged["double"].connect(
            self.tab_edelta.on_delta_change_spin)
        self.tab_fit.sp_range_1.valueChanged.connect(self.on_params_init)
        self.tab_fit.sp_range_2.valueChanged.connect(self.on_params_init)
        # rating
        self.btn_rating_filter.clicked.connect(self.on_rating_threshold)
        self.cb_rating_scheme.currentTextChanged.connect(
            self.on_cb_rating_scheme)
        self.btn_rater.clicked.connect(self.on_user_rate)
        # plotting parameters
        self.cb_mpl_rescale_plot_x.stateChanged.connect(
            self.on_mpl_curve_update)
        self.cb_mpl_rescale_plot_x_min.valueChanged.connect(
            self.on_mpl_curve_update)
        self.cb_mpl_rescale_plot_x_max.valueChanged.connect(
            self.on_mpl_curve_update)
        self.cb_mpl_rescale_plot_y.stateChanged.connect(
            self.on_mpl_curve_update)
        self.cb_mpl_rescale_plot_y_min.valueChanged.connect(
            self.on_mpl_curve_update)
        self.cb_mpl_rescale_plot_y_max.valueChanged.connect(
            self.on_mpl_curve_update)

        # Random string for identification of autosaved results
        self._autosave_randstr = hashlib.md5(time.ctime().encode("utf-8")
                                             ).hexdigest()[:5]
        # Initialize `override` parameter:
        # -1: not decided
        #  0: do not override existing files
        #  1: override existing files
        #  2: create additional file with date
        self._autosave_override = -1
        # Filenames that were created by this instance
        self._autosave_original_files = []

    @property
    def current_curve(self):
        idx = self.current_index
        fdist = self.data_set[idx]
        return fdist

    @property
    def current_index(self):
        item = self.list_curves.currentItem()
        idx = self.list_curves.indexOfTopLevelItem(item)
        return idx

    @property
    def selected_curves(self):
        """Return an IndentationGroup with all curves selected by the user"""
        curves = nanite.IndentationGroup()
        for ar in self.data_set:
            idx = self.data_set.index(ar)
            item = self.list_curves.topLevelItem(idx)
            if item.checkState(3) == QtCore.Qt.Checked:
                curves.append(ar)
        return curves

    def add_files(self, files):
        """ Populate self.data_set and display the first curve """
        # The `mult` parameter is used to chunk the progress bar,
        # because we cannot use floats with `QProgressDialog`, but
        # we want to be able to show progress for files that contain
        # multiple force curves.
        mult = 100
        bar = QtWidgets.QProgressDialog("Loading data files...",
                                        "Stop", 1, len(files)*mult)
        bar.setWindowTitle("Loading data files")
        bar.setMinimumDuration(1000)
        for ii, f in enumerate(files):
            label = "Loading file\n{}".format(os.path.basename(f))
            bar.setLabelText(label)

            def callback(partial):
                """Call back method for a progress dialog

                This method updates `bar` with the current file index
                `ii` and a partial file value `partial`.

                Parameters
                ----------
                partial: float in [0,1]
                    The progress for a single file
                """
                bar.setValue(int((ii+partial)*mult))
                QtCore.QCoreApplication.instance().processEvents()
                if bar.wasCanceled():
                    # Raise a custom `AbortProgress` error, such that
                    # we can exit the parent for-loop.
                    raise AbortProgress
            try:
                grp = nanite.IndentationGroup(f, callback=callback)
                callback(1)
            except afmformats.errors.FileFormatMetaDataError:
                # ignore e.g. JPK callibration curves
                callback(1)
                continue
            except AbortProgress:
                # The custom error `AbortProgress` was called, because
                # the user wants to stop loading the data.
                break
            self.data_set += grp
        bar.reset()
        bar.close()
        self.curve_list_setup()
        # Select first item
        it = self.list_curves.topLevelItem(0)
        self.list_curves.setCurrentItem(it)

    def autosave(self, fdist):
        """Performs autosaving for all files"""
        if (self.cb_autosave.checkState() == QtCore.Qt.Checked and
            fdist.fit_properties and
                fdist.fit_properties["success"]):
            # Determine the directory of the current curve
            adir = os.path.dirname(fdist.path)
            model_key = fdist.fit_properties["model_key"]
            # Determine all other curves with the same path
            exp_curv = []
            for ii, ar in enumerate(self.data_set):
                it = self.list_curves.topLevelItem(ii)
                if (
                    # same directory
                    os.path.dirname(ar.path) == adir and
                    # fdist was fitted
                    ar.fit_properties and
                    # fit was successful
                    ar.fit_properties["success"] and
                    # fdist was fitted with same model
                    ar.fit_properties["model_key"] == model_key and
                    # user selected curve for export ("use")
                    it.checkState(3) == QtCore.Qt.Checked
                ):
                    exp_curv.append(ar)
            # The file to export
            fname = os.path.join(adir, "pyjibe_fit_results_leaf.tsv")

            # Only export if we have curves to export
            if exp_curv:
                if (os.path.exists(fname) and
                        fname not in self._autosave_original_files):
                    # File already exists
                    oride = self._autosave_override
                    if oride == -1:
                        # Ask user what to do
                        dlgwin = QtWidgets.QDialog(self)
                        dlgwin.setWindowModality(QtCore.Qt.ApplicationModal)
                        dlgui = DlgAutosave()
                        dlgui.setupUi(dlgwin)
                        if dlgwin.exec_():
                            if dlgui.btn_nothing.isChecked():
                                oride = 0
                            elif dlgui.btn_override.isChecked():
                                oride = 1
                            elif dlgui.btn_new.isChecked():
                                oride = 2
                            if dlgui.cb_remember.isChecked():
                                self._autosave_override = oride
                            if dlgui.cb_disableauto.isChecked():
                                self.cb_autosave.setChecked(0)
                    if oride == 0:
                        # Do not override
                        return
                    elif oride == 1:
                        # Override existing file
                        pass
                    elif oride == 2:
                        # Create new filename
                        now = time.strftime("%Y-%m-%d")
                        newbase = "pyjibe_fit_results_leaf_{}_{}.tsv".format(
                            now,
                            self._autosave_randstr
                        )
                        fname = os.path.join(adir, newbase)
                # Export data
                which = ["params_fitted", "rating"]
                export.save_tsv_metadata_results(filename=fname,
                                                 fdist_list=exp_curv,
                                                 which=which)
                self._autosave_original_files.append(fname)

    def curve_list_setup(self):
        """Add items to the tree widget"""
        header = self.list_curves.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.list_curves.setColumnWidth(1, 70)
        self.list_curves.setColumnWidth(2, 70)
        self.list_curves.setColumnWidth(3, 40)
        for ar in self.data_set:
            it = QtWidgets.QTreeWidgetItem(self.list_curves,
                                           ["..."+str(ar.path)[-62:],
                                            str(ar.enum),
                                            "{:.1f}".format(-1)])
            self.list_curves.addTopLevelItem(it)
            it.setCheckState(3, QtCore.Qt.Checked)
        # Connect signals:
        # Selection of curves
        self.list_curves.itemSelectionChanged.connect(self.on_curve_list)
        self.list_curves.model().dataChanged.connect(
            self.on_curve_list_item_changed)

    def curve_list_update(self, item=None):
        """Update the curve list display with all ratings"""
        if item is None:
            indices = np.arange(len(self.data_set))
        else:
            indices = [item]
        for ii in indices:
            ar = self.data_set[ii]
            rating = self.rate_data(ar)
            it = self.list_curves.topLevelItem(ii)
            it.setText(2, "{:.1f}".format(rating))
            cm = colormap.cm_rating
            color = np.array(np.array(cm(rating/10))*255, dtype=int)
            it.setBackground(2, QtGui.QColor(*color))

    @staticmethod
    def get_export_choices():
        """Choices for file menu export

        Returns
        -------
        choices: list
            [[menu label 1, method name 1],
             ...
             ]
        """
        choices = [["metadata and results", "on_export_fit_results"],
                   ["E(δ) curves", "on_export_edelta"]
                   ]
        return choices

    def info_update(self, fdist=None):
        """Updates the info tab"""
        if fdist is None:
            fdist = self.current_curve
        self.tab_info.update_info(fdist)

    def on_cb_rating_scheme(self):
        """Switch rating scheme or import a new one"""
        scheme_id = self.cb_rating_scheme.currentIndex()
        schemes = rating_base.get_rating_schemes()
        if len(schemes) == scheme_id:
            search_dir = ""
            exts_str = "Training set zip file (*.zip)"
            tsz, _e = QtWidgets.QFileDialog.getOpenFileName(
                self.parent(), "Import a training set",
                search_dir, exts_str)
            if tsz:
                idx = rating_base.import_training_set(tsz)
                self.rating_scheme_setup()
                self.cb_rating_scheme.setCurrentIndex(idx)
            else:
                self.cb_rating_scheme.setCurrentIndex(0)
        else:
            self.on_params_init()

    def on_curve_list(self):
        """Called when a new curve is selected"""
        fdist = self.current_curve
        idx = self.current_index
        # perform preprocessing
        self.tab_preprocess.fit_apply_preprocessing(fdist)
        # update user interface with initial parameters
        self.tab_fit.fit_update_parameters(fdist)
        # fit data
        self.tab_fit.fit_approach_retract(fdist)
        # set plot data (time consuming)
        self.widget_fdist.mpl_curve_update(fdist)
        # update info
        self.info_update(fdist)
        # Display new rating
        self.curve_list_update(item=idx)
        # Display map
        self.tab_qmap.mpl_qmap_update()
        # Display edelta
        self.tab_edelta.mpl_edelta_update()
        # Autosave
        self.autosave(fdist)

    def on_curve_list_item_changed(self, item):
        """An item in the curve list was changed

        - update the qmap
        - autosave the results
        """
        # The data set index:
        idx = item.row()
        fdist = self.data_set[idx]
        if item.column() == 3:
            # The checkbox has been changed
            self.tab_qmap.mpl_qmap_update()
            self.autosave(fdist)

    def on_export_edelta(self):
        """Saves all edelta curves"""
        fname, _e = QtWidgets.QFileDialog.getSaveFileName(
            self.parent(),
            "Save E(δ) curves",
            "",
            "Tab Separated Values (*.tsv)"
        )
        if fname:
            if not fname.endswith(".tsv"):
                fname += ".tsv"
            # Make sure all curves have correct fit properties
            self.on_fit_all()
            # Proceed computing edelta curves with progress bar
            curves = self.selected_curves
            bar = QtWidgets.QProgressDialog("Computing  E(δ) curves...",
                                            "Stop", 1, len(curves))
            bar.setWindowTitle("Please wait...")
            bar.setMinimumDuration(1000)

            res = []
            for ii, ar in enumerate(curves):
                if bar.wasCanceled():
                    return
                # TODO:
                # - Use the callback method in `compute_emodulus_mindelta`
                #   to prevent "freezing" of the GUI?
                try:
                    e, d = ar.compute_emodulus_mindelta()
                except nfit.FitDataError:
                    pass
                else:
                    res += [d, e]
                QtCore.QCoreApplication.instance().processEvents()
                bar.setValue(ii+1)

            # export curves with numpy
            with io.open(fname, "w") as fd:
                header = ["# Indentation [m] and elastic modulus [Pa]\n",
                          "# are stored as alternating rows.\n",
                          ]
                fd.writelines(header)

            with io.open(fname, "ab") as fd:
                np.savetxt(fd, np.array(res))

    def on_export_fit_results(self):
        """Save metadata and fit results"""
        fdist_list = [fdist for fdist in self.selected_curves]
        dlg = dlg_export_vals.ExportDialog(parent=self,
                                           fdist_list=fdist_list,
                                           identifier=self._instance_counter)
        dlg.show()

    def on_fit_all(self):
        """Apply initial parameters to all curves and fit"""
        # We will fit all curves with the currently visible settings
        bar = QtWidgets.QProgressDialog("Fitting all curves...",
                                        "Stop", 1, len(self.data_set))
        bar.setWindowTitle("Loading data files")
        bar.setMinimumDuration(1000)
        for ii, fdist in enumerate(self.data_set):
            QtCore.QCoreApplication.instance().processEvents()
            if bar.wasCanceled():
                break
            self.tab_preprocess.fit_apply_preprocessing(fdist)
            self.tab_fit.fit_approach_retract(fdist, update_ui=False)
            bar.setValue(ii+1)
            self.curve_list_update(item=ii)
        # Display map
        self.tab_qmap.mpl_qmap_update()

    def on_model(self):
        """Called when the fitting model is changed"""
        # The difference to "on_params_init" is that we
        # have to `fit_update_parameters` in order to display
        # potential new parameter names of the new model.
        fdist = self.current_curve
        self.tab_preprocess.fit_apply_preprocessing(fdist)
        self.tab_fit.fit_update_parameters(fdist)
        self.tab_fit.fit_approach_retract(fdist)
        self.widget_fdist.mpl_curve_update(fdist)
        self.curve_list_update()
        self.tab_qmap.mpl_qmap_update()

    def on_mpl_curve_update(self):
        fdist = self.current_curve
        self.widget_fdist.mpl_curve_update(fdist)

    def on_params_init(self):
        """Called when the initial parameters are changed"""
        fdist = self.current_curve
        idx = self.current_index
        self.tab_preprocess.fit_apply_preprocessing(fdist)
        self.tab_fit.anc_update_parameters(fdist)
        self.tab_fit.fit_approach_retract(fdist)
        self.widget_fdist.mpl_curve_update(fdist)
        self.curve_list_update(item=idx)
        self.tab_qmap.mpl_qmap_update()

    def on_rating_threshold(self):
        """(De)select curves according to threshold rating"""
        thresh = self.sp_rating_thresh.value()
        self.list_curves.blockSignals(True)
        for ii, fdist in enumerate(self.data_set):
            rtd = fdist.get_rating_parameters()
            rating = rtd["Rating"]
            it = self.list_curves.topLevelItem(ii)
            if not np.isnan(rating):
                if rating >= thresh:
                    it.setCheckState(3, QtCore.Qt.Checked)
                else:
                    it.setCheckState(3, QtCore.Qt.Unchecked)
        self.list_curves.blockSignals(False)
        # TODO:
        # - make this more efficient. There is a lot written to disk here.
        for fdist in self.data_set:
            self.autosave(fdist)

    def on_tab_changed(self, index):
        """Called when the tab on the right hand is changed"""
        if hasattr(self, "user_tab_selected"):
            prevtab = self.user_tab_selected
        else:
            prevtab = self.tabs.currentWidget()

        curtab = self.tabs.currentWidget()
        if curtab == self.tab_fit and prevtab == self.tab_preprocess:
            self.on_params_init()
        elif curtab == self.tab_qmap:
            # Redraw the current map
            self.tab_qmap.mpl_qmap_update()
        elif curtab == self.tab_edelta:
            # Compute edelta plot
            self.tab_edelta.mpl_edelta_update()
        elif curtab == self.tab_info:
            # Updat info (e.g. ancillaries)
            self.info_update()

        self.user_tab_selected = curtab

    def on_user_rate(self):
        """Start the curve rater"""
        cont = QtWidgets.QFileDialog.getSaveFileName(
            parent=None,
            caption="Please select a rating container",
            directory="",
            filter="Rating containers (*.h5)",
            options=QtWidgets.QFileDialog.DontConfirmOverwrite
                    | QtWidgets.QFileDialog.DontUseNativeDialog)

        path = cont[0]
        if path:
            rt = rating_iface.Rater(fdui=self, path=path)
            self.curve_rater = rt
            rt.show()

    def rate_data(self, data):
        """Apply rating to a force-distance curves (or a list of curves)"""
        scheme_id = self.cb_rating_scheme.currentIndex()
        return rating_base.rate_fdist(data, scheme_id)

    def rating_scheme_setup(self):
        self.cb_rating_scheme.clear()
        schemes = rating_base.get_rating_schemes()
        self.cb_rating_scheme.addItems(list(schemes.keys()))
        self.cb_rating_scheme.addItem("Add...")


class AbortProgress(BaseException):
    pass
