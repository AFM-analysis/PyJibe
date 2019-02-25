import hashlib
import os
import time

import numpy as np
from PyQt5 import QtCore, QtWidgets, QtGui

import nanite
import nanite.model as nmodel
import nanite.read as nread

from .. import colormap
from .. import units

from .base import UiForceDistanceBase, DlgAutosave
from . import export
from . import user_rating


class UiForceDistance(UiForceDistanceBase):
    def __init__(self, parent_widget):
        """Base class derived from Qt designer

        To reduce the number of lines in a file, the UI for
        force-indentation measurements is split into two classes:
        - `UiIndentationBase` completes the (dynamic) design of the UI and
          provides convenience properties.
        - `UiIndentation` contains logic parts of the code that are not
          part of the UI.
        """
        super(UiForceDistance, self).__init__(parent_widget)
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
            except nread.read_jpk_meta.ReadJPKMetaKeyError:
                # ignore callibration curves
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
        if (self.cb_autosave.checkState() == 2 and
            fdist.fit_properties and
                fdist.fit_properties["success"]):
            # Determine the directory of the current curve
            adir = os.path.dirname(fdist.path)
            model_key = fdist.fit_properties["model_key"]
            # Determine all other curves with the same path
            exp_curv = []
            for ii, ar in enumerate(self.data_set):
                it = self.list_curves.topLevelItem(ii)
                if (  # same directory
                    os.path.dirname(ar.path) == adir and
                    # fdist was fitted
                    ar.fit_properties and
                    # fit was successful
                    ar.fit_properties["success"] and
                    # fdist was fitted with same model
                    ar.fit_properties["model_key"] == model_key and
                    # user selected curve for export ("use")
                    it.checkState(3) == 2
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
                        dlgwin = QtWidgets.QDialog()
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
                ratings = self.rate_data(exp_curv)
                export.save_tsv_approach_retract(filename=fname,
                                                 fdist_list=exp_curv,
                                                 ratings=ratings)
                self._autosave_original_files.append(fname)

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
            color = np.array(cm(rating/10))*255
            it.setBackground(2, QtGui.QColor(*color))

    def fit_apply_preprocessing(self, fdist):
        """Apply the preprocessing steps if required"""
        # Note: Preprocessing is cached once in `fdist`.
        # Thus calling this method a second time without any
        # change in the GUI is free.
        num = self.list_preproc_applied.count()
        preprocessing = []
        for ii in range(num):
            item = self.list_preproc_applied.item(ii)
            preprocessing.append(item.text())
        # Perform preprocessing
        fdist.apply_preprocessing(preprocessing)

    def fit_approach_retract(self, fdist, update_ui=True):
        """Perform preprocessing and fit data

        Parameters
        ----------
        fdist: afmlib.indentaion.Indentaion
            Indentation curve to fit.
        update_ui: bool
            Update the user interface after fitting,
            i.e. displaying the results in
            `self.table_parameters_fitted`.
        """
        # segment
        segment = self.cb_segment.currentText().lower()
        # x axis
        x_axis = self.cb_xaxis.currentText()
        # y axis
        y_axis = self.cb_yaxis.currentText()
        # Get model key from dropdown list
        model = nmodel.get_model_by_name(self.cb_model.currentText())
        model_key = model.model_key
        # Determine range type
        if self.cb_range_type.currentText() == "absolute":
            range_type = "absolute"
        else:
            range_type = "relative cp"
        # Determine range
        range_x = [self.sp_range_1.value() * units.scales["µ"],
                   self.sp_range_2.value() * units.scales["µ"]]
        # Determine if we want to weight the contact point
        self.on_update_weights(on_params_init=False)
        if self.cb_weight_cp.checkState() == 2:
            weight_cp = self.sp_weight_cp_um.value() * units.scales["µ"]
        else:
            weight_cp = False
        # Determine if we want to autodetect the optimal indentation depth
        if self.cb_delta_select_1.currentIndex() == 2:
            optimal_fit_edelta = True
        else:
            optimal_fit_edelta = False
        # number of samples for edelta plot
        optimal_fit_num_samples = self.sp_delta_num_samples.value()
        # fit parameters
        params = self.fit_parameters()
        # Perform fitting
        fdist.fit_model(model_key=model_key,
                        params_initial=params,
                        range_x=range_x,
                        range_type=range_type,
                        x_axis=x_axis,
                        y_axis=y_axis,
                        weight_cp=weight_cp,
                        segment=segment,
                        optimal_fit_edelta=optimal_fit_edelta,
                        optimal_fit_num_samples=optimal_fit_num_samples,
                        )
        ftab = self.table_parameters_fitted
        if fdist.fit_properties["success"]:
            # Perform automatic saving of results
            self.autosave(fdist)
            # Display automatically detected optimal indentation depth
            if optimal_fit_edelta:
                # Set guessed indentation depth in GUI
                val = fdist.fit_properties["optimal_fit_delta"]
                self.sp_range_1.setValue(val/units.scales["µ"])
            if update_ui:
                # Display results in `self.table_parameters_fitted`
                fitpar = fdist.fit_properties["params_fitted"]
                varps = [p[1] for p in fitpar.items() if p[1].vary]
                self.assert_parameter_table_rows(ftab, len(varps))
                for ii, p in enumerate(varps):
                    # Get the human readable name of the parameter
                    name = model.parameter_keys.index(p.name)
                    hrnam = model.parameter_names[name]
                    # Determine unit scale, e.g. 1e6 [sic] for µm
                    scale = units.hrscale(hrnam)
                    ftab.verticalHeaderItem(ii).setText(units.hrscname(hrnam))
                    ftab.item(ii, 0).setText("{:.3f}".format(p.value*scale))
        else:
            if update_ui:
                inipar = fdist.fit_properties["params_initial"]
                varps = [p[1] for p in inipar.items() if p[1].vary]
                self.assert_parameter_table_rows(ftab, len(varps))
                for ii, p in enumerate(varps):
                    # Get the human readable name of the parameter
                    name = model.parameter_keys.index(p.name)
                    hrnam = model.parameter_names[name]
                    ftab.verticalHeaderItem(ii).setText(units.hrscname(hrnam))
                    ftab.item(ii, 0).setText("nan")

    def info_update(self, fdist):
        """Updates the info tab"""
        text = []
        text.append("filename: {}".format(fdist.path))
        text.append("position index/enum: {}".format(fdist.enum))
        text.append("")
        keys = list(fdist.metadata.keys())
        keys.sort()
        for k in keys:
            text.append("{}: {}".format(k, fdist.metadata[k]))
        textstring = "\n".join(text)
        self.info_text.setPlainText(textstring)

    def mpl_curve_update(self, fdist):
        """Update the force-indentation curve"""
        autoscale_x = self.cb_mpl_rescale_plot_x.checkState() == 2
        autoscale_y = self.cb_mpl_rescale_plot_y.checkState() == 2
        if autoscale_x:
            rescale_x = None
        else:
            rescale_x = (self.cb_mpl_rescale_plot_x_min.value(),
                         self.cb_mpl_rescale_plot_x_max.value())

        if autoscale_y:
            rescale_y = None
        else:
            rescale_y = (self.cb_mpl_rescale_plot_y_min.value(),
                         self.cb_mpl_rescale_plot_y_max.value())

        self.mpl_curve.update(fdist,
                              rescale_x=rescale_x,
                              rescale_y=rescale_y)

    def mpl_edelta_update(self):
        """Update the E(delta) plot"""
        if self.tabs.currentWidget() == self.tab_edelta:
            fdist = self.current_curve
            delta_opt = self.sp_range_1.value()
            # Update slider range
            xaxis = self.cb_xaxis.currentText()
            segment = self.cb_segment.currentText().lower()
            segment_bool = segment == "retract"
            segid = (fdist["segment"] == segment_bool).as_matrix()
            xdata = fdist[xaxis].as_matrix()
            xscale = units.hrscale(xaxis)
            minx = np.min(xdata[segid])*xscale
            self.delta_slider.blockSignals(True)
            self.delta_slider.setMinimum(minx)
            self.delta_slider.setValue(delta_opt)
            self.delta_slider.blockSignals(False)
            # Update E(delta) plot
            self.fit_approach_retract(fdist)
            self.mpl_edelta.update(fdist, delta_opt)

    def mpl_qmap_update(self):
        fdist = self.current_curve
        # Only update if we are on the right tab
        if self.tabs.currentWidget() == self.tab_qmap:
            # Build list of possible selections
            selist = nanite.qmap.available_features

            # Get plotting parameter and check if it makes sense
            feature = self.qmap_data_cb.currentText()
            if not feature or feature not in selist:
                # Use a default plotting map
                feature = "data min height"

            # Make sure that we have a valid property to plot
            assert feature in selist

            # Update dropdown menu with possible selections
            # disable signals while updating the combobox
            self.qmap_data_cb.blockSignals(True)
            # remove all items
            for _i in range(self.qmap_data_cb.count()):
                self.qmap_data_cb.removeItem(0)
            # add new items
            for item in selist:
                self.qmap_data_cb.addItem(item)
            self.qmap_data_cb.setCurrentIndex(selist.index(feature))
            self.qmap_data_cb.blockSignals(False)

            # Get all selected curves with the same path
            curves = self.selected_curves.subgroup_with_path(fdist.path)

            if len(curves) > 1:
                # Get map data
                qmap = nanite.QMap(curves)
                # update plot
                self.mpl_qmap.update(qmap=qmap,
                                     feature=feature,
                                     cmap=self.qmpa_cmap_cb.currentText(),
                                     vmin=self.qmap_sp_range1.value(),
                                     vmax=self.qmap_sp_range2.value())
                self.mpl_qmap.set_selection_by_index(curves.index(fdist))
            else:
                self.mpl_qmap.reset()

    def on_curve_list(self):
        """Called when a new curve is selected"""
        fdist = self.current_curve
        idx = self.current_index
        # perform preprocessing
        self.fit_apply_preprocessing(fdist)
        # update user interface with initial parameters
        self.fit_update_parameters(fdist)
        # fit data
        self.fit_approach_retract(fdist)
        # set plot data (time consuming)
        self.mpl_curve_update(fdist)
        # update info
        self.info_update(fdist)
        # Display new rating
        self.curve_list_update(item=idx)
        # Display map
        self.mpl_qmap_update()
        # Display edelta
        self.mpl_edelta_update()

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
            self.mpl_qmap_update()
            self.autosave(fdist)

    def on_model(self):
        """Called when the fitting model is changed"""
        # The difference to "on_params_init" is that we
        # have to `fit_update_parameters` in order to display
        # potential new parameter names of the new model.
        fdist = self.current_curve
        self.fit_apply_preprocessing(fdist)
        self.fit_update_parameters(fdist)
        self.fit_approach_retract(fdist)
        self.mpl_curve_update(fdist)
        self.curve_list_update()
        self.mpl_qmap_update()

    def on_params_init(self):
        """Called when the initial parameters are changed"""
        fdist = self.current_curve
        idx = self.current_index
        self.fit_apply_preprocessing(fdist)
        self.fit_approach_retract(fdist)
        self.mpl_curve_update(fdist)
        self.curve_list_update(item=idx)
        self.mpl_qmap_update()

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
            self.mpl_qmap_update()
        elif curtab == self.tab_edelta:
            # Compute edelta plot
            self.mpl_edelta_update()

        self.user_tab_selected = curtab

    def on_user_rate(self):
        cont = QtWidgets.QFileDialog.getSaveFileName(
            parent=None,
            caption="Please select a rating container",
            directory="",
            filter="Rating containers (*.h5)",
            options=QtWidgets.QFileDialog.DontConfirmOverwrite
                    | QtWidgets.QFileDialog.DontUseNativeDialog)

        path = cont[0]
        if path:
            rt = user_rating.Rater(fdui=self, path=path)
            self.curve_rater = rt
            rt.show()


class AbortProgress(BaseException):
    pass
