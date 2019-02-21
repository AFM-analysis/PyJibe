import collections
import inspect
import io
import pkg_resources

import numpy as np
from PyQt5 import uic, QtCore, QtWidgets

import nanite
import nanite.fit as nfit
import nanite.model as nmodel
import nanite.indent as nindent
import nanite.preproc as npreproc

from .. import units

from . import export
from .mpl_indent import MPLIndentation
from .mpl_edelta import MPLEDelta
from .mpl_qmap import MPLQMap


RATING_SCHEMES = collections.OrderedDict()
RATING_SCHEMES["Default (zef18 & Extra Trees)"] = ["zef18", "Extra Trees"]
RATING_SCHEMES["Disabled"] = ["none", "none"]


# load QWidget from ui file
ui_path = pkg_resources.resource_filename("pyjibe.fd",
                                          "base_design.ui")
UiForceDistanceCore = uic.loadUiType(ui_path)[0]

dlg_autosave_path = pkg_resources.resource_filename("pyjibe.fd",
                                                    "dlg_autosave_design.ui")
DlgAutosave = uic.loadUiType(dlg_autosave_path)[0]


class UiForceDistanceBase(UiForceDistanceCore):
    _instance_counter = 0

    def __init__(self, parent_widget):
        """Base class derived from Qt designer

        To reduce the number of lines in a file, the UI for
        force-indentation measurements is split into two classes:
        - `UiIndentationBase` completes the (dynamic) design of the UI and
          provides convenience properties.
        - `UiIndentation` contains logic parts of the code that are not
          part of the UI.
        """
        super(UiForceDistanceCore, self).__init__()
        self.setupUi(parent_widget)
        self.parent_widget = parent_widget

        UiForceDistanceBase._instance_counter += 1
        title = "{} #{}".format(self.parent_widget.windowTitle(),
                                self._instance_counter)
        self.parent_widget.setWindowTitle(title)

        self.mpl_curve_setup()
        self.mpl_edelta_setup()
        self.mpl_qmap_setup()
        self.data_set = nanite.IndentationGroup()

        # initial values, sources, drains for indentation depth
        self.indentation_depth_setup()

        # preprocessing setup
        self.preproc_setup()

        # fitting setup
        self.fit_setup()

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.signal_slot(True)
        self.btn_rater.clicked.connect(self.on_user_rate)

    def assert_parameter_table_rows(self, table, rows, cb_first=False):
        """Make sure a QTableWidget has enough rows

        Parameters
        ----------
        table: instance of QtWidgets.QTableWidget
            The table that will be edited
        rows: int
            Number of rows
        cb_first: bool
            Set first column values as check-boxes.
            (This is used for fixing fit parameters in PyJibe)
        """
        table.setRowCount(rows)
        cols = table.columnCount()
        for rr in range(rows):
            hitem = QtWidgets.QTableWidgetItem()
            table.setVerticalHeaderItem(rr, hitem)
            for cc in range(cols):
                item = QtWidgets.QTableWidgetItem()
                if cc == 0 and cb_first:
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable |
                                  QtCore.Qt.ItemIsEnabled)
                    item.setCheckState(QtCore.Qt.Unchecked)
                table.setItem(rr, cc, item)

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

    def fit_parameters(self):
        """Returns parameters currently set in the GUI

        The parameter data is read out from
        `self.table_parameters_initial`. If the model that was
        previously set does not match the current model, only the
        parameters with the same name (existing in both models) are
        updated.
        """
        # Get model key from dropdown list
        model = nmodel.get_model_by_name(self.cb_model.currentText())
        model_key = model.model_key
        # Get parameters from `self.table_parameters_initial`
        model = nmodel.models_available[model_key]
        params = model.get_parameter_defaults()
        itab = self.table_parameters_initial
        if itab.verticalHeaderItem(0):
            # Only update if there is already something set
            for ii, key in enumerate(list(params.keys())):
                p = params[key]
                # Determine the scale for which we need to revert
                # the multiplications.
                # performed in `fit_update_parameters`.
                hrname = model.parameter_names[ii]
                scale = units.hrscale(hrname)
                for rr in range(itab.rowCount()):
                    # search for a row matching the parameter `p`
                    if itab.verticalHeaderItem(rr).text().startswith(hrname):
                        # update parameter `p`
                        state = itab.item(rr, 0).checkState()
                        if state == QtCore.Qt.Unchecked:
                            p.vary = True
                        else:
                            p.vary = False
                        p.set(float(itab.item(rr, 1).text())/scale)
                        p.min = float(itab.item(rr, 2).text())/scale
                        p.max = float(itab.item(rr, 3).text())/scale
                        break
        return params

    def fit_setup(self):
        """Setup the fitting tab"""
        id_para = 0
        # Model selection
        models_av = list(nmodel.models_available.keys())
        models_av.sort(key=lambda x: nmodel.models_available[x].model_name)
        for ii, key in enumerate(models_av):
            model = nmodel.models_available[key]
            self.cb_model.addItem(model.model_name)
            if key == "hertz_para":
                id_para = ii
        # Setz Hertz Parabolic as default
        self.cb_model.setCurrentIndex(id_para)
        # Axis selection
        self.cb_xaxis.addItem("tip position")
        self.cb_yaxis.addItem("force")

    def fit_update_parameters(self, fdist):
        """Update the initial and fitting parameters"""
        model = nmodel.get_model_by_name(self.cb_model.currentText())
        model_key = model.model_key
        if ("params_initial" in fdist.fit_properties and
            "model_key" in fdist.fit_properties and
                fdist.fit_properties["model_key"] == model_key):
            # set the parameters of the previous fit
            params = fdist.fit_properties["params_initial"]
        else:
            # use the initial model parameters
            params = self.fit_parameters()
        # parameter table
        itab = self.table_parameters_initial

        itab.setColumnWidth(0, 30)
        itab.setColumnWidth(1, 100)
        itab.setColumnWidth(2, 70)
        itab.setColumnWidth(3, 70)
        itab.blockSignals(True)

        self.assert_parameter_table_rows(itab, len(params), cb_first=True)
        for ii, key in enumerate(list(params.keys())):
            p = params[key]
            # Get the human readable name of the parameter
            hrname = model.parameter_names[ii]
            # Determine unit scale, e.g. 1e6 [sic] for µm
            scale = units.hrscale(hrname)
            itab.verticalHeaderItem(ii).setText(units.hrscname(hrname))
            if p.vary:
                state = QtCore.Qt.Unchecked
            else:
                state = QtCore.Qt.Checked
            itab.item(ii, 0).setCheckState(state)
            itab.item(ii, 1).setText("{:.2f}".format(p.value*scale))
            itab.item(ii, 2).setText(str(p.min*scale))
            itab.item(ii, 3).setText(str(p.max*scale))

        itab.blockSignals(False)

        # indentation depth
        if self.cb_delta_select_1.currentIndex() == 1:
            # Set indentation depth individually
            if fdist in self._indentation_depth_individual:
                value = self._indentation_depth_individual[fdist]
                self.delta_spin.setValue(value)
            else:
                value = self.delta_spin.value()
                self._indentation_depth_individual[fdist] = value

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
        choices = [["fit results", "on_export_fit_results"],
                   ["E(δ) curves", "on_export_edelta"]
                   ]
        return choices

    def indentation_depth_setup(self):
        """Initiate ranges (spin/slider) that allow inf values"""
        # Initialize individual indentation depth dictionary
        self._indentation_depth_individual = {}
        # Left
        self.sp_range_1.setValue(-np.inf)
        # Right
        self.sp_range_2.setValue(np.inf)
        # Left on edelta plot
        self.delta_spin.setValue(-np.inf)
        # Slider
        self.delta_slider.setMaximum(0)
        # Signals
        self.sp_range_1.valueChanged["double"].connect(
            self.on_delta_change_spin)
        self.delta_spin.valueChanged["double"].connect(
            self.on_delta_change_spin)
        self.delta_slider.sliderReleasedFloat["double"].connect(
            self.on_delta_change_spin)
        self.delta_slider.valueChangedFloat["double"].connect(
            self.mpl_edelta.update_delta)
        self.sp_range_2.valueChanged.connect(self.on_params_init)
        self.cb_delta_select_1.currentIndexChanged['int'].connect(
            self.on_delta_select)
        self.delta_btn_guess.clicked.connect(self.on_delta_guess)

    def mpl_curve_setup(self):
        """Setup the matplotlib interface for approach retract plotting"""
        self.mpl_curve = MPLIndentation()
        self.mpl_curve.add_toolbar(self.mplwindow)
        self.mplvl.addWidget(self.mpl_curve.canvas)
        self.mplvl.addWidget(self.mpl_curve.toolbar)
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

    def mpl_edelta_setup(self):
        """Setup the matplotlib interface for E(delta) plotting"""
        self.mpl_edelta = MPLEDelta()
        self.mpl_edelta.add_toolbar(self.edelta_mplwidget)
        self.edelta_mpllayout.addWidget(self.mpl_edelta.canvas)
        self.edelta_mpllayout.addWidget(self.mpl_edelta.toolbar)

    def mpl_qmap_setup(self):
        """Setup the matplotlib interface for 2D map plotting"""
        self.mpl_qmap = MPLQMap()
        self.mpl_qmap.add_toolbar(self.qmap_mplwidget)
        self.qmap_mpllayout.addWidget(self.mpl_qmap.canvas)
        self.qmap_mpllayout.addWidget(self.mpl_qmap.toolbar)
        # set colormaps
        cmaps = ["viridis", "plasma", "afmhot", "seismic"]
        for cm in cmaps:
            self.qmpa_cmap_cb.addItem(cm)
        self.qmpa_cmap_cb.setCurrentIndex(0)
        self.qmap_data_cb.currentIndexChanged.connect(
            self.on_qmap_data_changed)
        self.qmpa_cmap_cb.currentIndexChanged.connect(
            self.on_qmap_cmap_changed)
        self.qmap_sp_range1.valueChanged.connect(self.on_qmap_min_max_changed)
        self.qmap_sp_range2.valueChanged.connect(self.on_qmap_min_max_changed)
        self.mpl_qmap.connect_curve_selection_event(self.on_qmap_selection)

    def on_mpl_curve_update(self):
        fdist = self.current_curve
        self.mpl_curve_update(fdist)

    def on_qmap_cmap_changed(self):
        """colormap selection changed"""
        self.mpl_qmap_update()

    def on_qmap_data_changed(self):
        """data column selection changed"""
        # set previous spin control values if existent
        self.qmap_sp_range1.blockSignals(True)
        self.qmap_sp_range2.blockSignals(True)
        if hasattr(self, "_cache_qmap_spin_ctl"):
            data = self.qmap_data_cb.currentIndex()
            if data in self._cache_qmap_spin_ctl:
                vmin, vmax = self._cache_qmap_spin_ctl[data]
            else:
                vmin = vmax = 0
            self.qmap_sp_range1.setValue(vmin)
            self.qmap_sp_range2.setValue(vmax)
        self.qmap_sp_range1.blockSignals(False)
        self.qmap_sp_range2.blockSignals(False)
        self.mpl_qmap_update()

    def on_qmap_min_max_changed(self):
        """min or max spin controls changed"""
        # store spin control values for data column
        vmin = self.qmap_sp_range1.value()
        vmax = self.qmap_sp_range2.value()
        data = self.qmap_data_cb.currentIndex()
        if not hasattr(self, "_cache_qmap_spin_ctl"):
            self._cache_qmap_spin_ctl = {}
        self._cache_qmap_spin_ctl[data] = (vmin, vmax)
        self.mpl_qmap_update()

    def on_qmap_selection(self, idx):
        """Show the curve indexed in the current qmap"""
        # Get the qmap name
        cc = self.current_curve
        # idx is `enum` and curves are sorted
        curves = [ci for ci in self.data_set if ci.path == cc.path]
        fdist = curves[idx]
        idcurve = self.data_set.index(fdist)
        item = self.list_curves.topLevelItem(idcurve)
        self.list_curves.setCurrentItem(item)

    def on_delta_guess(self):
        """Guess the optimal indentation depth for the current curve"""
        fdist = self.current_curve
        value = fdist.estimate_optimal_mindelta()
        value /= units.scales["µ"]
        self.delta_spin.setValue(value)

    def on_delta_select(self, value):
        """The user selected a method for indentation depth determination

        This method is called when `cb_delta_select_1` or (indirectly)
        `cb_delta_select_2` are changed.

        At the end, `on_params_init` is called, to redo the fit. After
        fitting, the indentation depth (`sp_range_1`) will be set by
        `fit_approach_retract`, if `value==2`.

        Parameters
        ----------
        value: int
            The selected index of the dropdown widget:
            - 0: Set indentation depth globally
            - 1: Set indentation depth individually
            - 2: Guess optimal indentation depth
        """
        # These widgets are disabled when the user wants
        # PyJibe to guess the indentation depth:
        global_disable = [self.sp_range_1]
        # These widgets are enabled when the user wants to
        # select an indentation depth for each curve:
        local_enable = [self.delta_label,
                        self.delta_spin,
                        self.delta_slider,
                        self.delta_btn_guess]

        if value == 0:
            # Set indentation depth globally
            [item.setEnabled(True) for item in global_disable]
            [item.setEnabled(False) for item in local_enable]
            self.cb_range_type.setEnabled(True)
        elif value == 1:
            # Set indentation depth individually
            [item.setEnabled(True) for item in global_disable]
            [item.setEnabled(True) for item in local_enable]
            self.cb_range_type.setEnabled(False)
            self.cb_range_type.setCurrentText("absolute")
            # Set/get indentation depth individually
            fdist = self.current_curve
            if fdist in self._indentation_depth_individual:
                value = self._indentation_depth_individual[fdist]
            else:
                value = self.delta_spin.value()
            self.delta_spin.setValue(value)

        elif value == 2:
            # Guess optimal indentation depth
            [item.setEnabled(False) for item in global_disable]
            [item.setEnabled(False) for item in local_enable]
            self.cb_range_type.setEnabled(False)
            self.cb_range_type.setCurrentText("absolute")

        self.on_params_init()

    def on_delta_change_spin(self, value):
        """Indentation depth spin control value changed"""
        # Update all controls
        self.sp_range_1.blockSignals(True)
        self.delta_spin.blockSignals(True)
        self.delta_slider.blockSignals(True)

        self.delta_spin.setValue(value)
        self.delta_slider.setValue(value)
        self.sp_range_1.setValue(value)
        self.mpl_edelta.update_delta(value)
        self.on_params_init()

        self.sp_range_1.blockSignals(False)
        self.delta_spin.blockSignals(False)
        self.delta_slider.blockSignals(False)

        # Update stored indentation depth
        if self.cb_delta_select_1.currentIndex() == 1:
            # Set indentation depth individually
            fdist = self.current_curve
            self._indentation_depth_individual[fdist] = value

    def on_export_fit_results(self):
        """Saves all fit results"""
        fname, _e = QtWidgets.QFileDialog.getSaveFileName(
            self.parent_widget,
            "Save fit results",
            "fit_results_{:03d}.tsv".format(
                self._instance_counter),
            "Tab Separated Values (*.tsv)"
        )
        if fname:
            if not fname.endswith(".tsv"):
                fname += ".tsv"
            self.on_fit_all()
            exp_curv = [fdist for fdist in self.selected_curves]
            ratings = self.rate_data(exp_curv)
            export.save_tsv_approach_retract(filename=fname,
                                             fdist_list=exp_curv,
                                             ratings=ratings)

    def on_export_edelta(self):
        """Saves all edelta curves"""
        fname, _e = QtWidgets.QFileDialog.getSaveFileName(
            self.parent_widget,
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
            self.fit_apply_preprocessing(fdist)
            self.fit_approach_retract(fdist, update_ui=False)
            bar.setValue(ii+1)
            self.curve_list_update(item=ii)
        # Display map
        self.mpl_qmap_update()

    def on_rating_threshold(self):
        """(De)select curves according to threshold rating"""
        thresh = self.sp_rating_thresh.value()
        self.curve_list_update()
        for ii, ar in enumerate(self.data_set):
            rating = self.rate_data(ar)
            it = self.list_curves.topLevelItem(ii)
            if rating >= thresh:
                it.setCheckState(3, 2)
            else:
                it.setCheckState(3, 0)
        # TODO:
        # -make this more efficient. There is a lot written to disk here.
        for fdist in self.data_set:
            self.autosave(fdist)

    def on_update_weights(self, on_params_init=True):
        """Compute the weight in µm or % for user convenience

        This method updates the value of the interval range to
        suppress residuals near the contact point for the spin controls
        - `self.sp_weight_cp_um` (absolute [µm] radio button) and
        - `self.sp_weight_cp_perc` (% tip radius radio button),
        depending on which was updated by the user.

        Notes
        -----
        This method only updates the values if the model has a
        parameter "R", the radius of the indenter. In any other
        case, it will do nothing and disable the "% tip radius"
        radio button.
        """
        # First get the tip radius
        model = nmodel.get_model_by_name(self.cb_model.currentText())
        params = model.get_parameter_defaults()
        itab = self.table_parameters_initial
        for ii, key in enumerate(list(params.keys())):
            if key == "R":
                radius = float(itab.item(ii, 1).text())
                # Make sure the "% tip radius" radio button is enabled,
                # because it could have been disabled for a fit model that
                # does not contain the parameter "R".
                self.rd_weigt_perc.setEnabled(True)
                # Did the user select "% tip radius"?
                percent = self.rd_weigt_perc.isChecked()

                if percent:
                    # set um value
                    perc = self.sp_weight_cp_perc.value()
                    self.sp_weight_cp_um.blockSignals(True)
                    self.sp_weight_cp_um.setValue(radius*perc/100)
                    self.sp_weight_cp_um.blockSignals(False)
                else:
                    # set percent value
                    val = self.sp_weight_cp_um.value()
                    self.sp_weight_cp_perc.blockSignals(True)
                    self.sp_weight_cp_perc.setValue(val/radius*100)
                    self.sp_weight_cp_perc.blockSignals(False)
                break
        else:
            # The key "R" could not be found. This means we
            # have a model that does not allow to compute the
            # indentation in percentage of the tip radius
            # (e.g. conical indenter).
            # We will force the user to select the "absolute [µm]"
            # radio button and disable the "% tip radius" radio button.
            self.rd_weight_um.setChecked(True)
            self.rd_weigt_perc.setEnabled(False)

        if on_params_init:
            self.on_params_init()

    def preproc_descr_update(self, source):
        """Update the description box with the method doc string

        Writes text to `self.text_preprocessing` according to the
        method selected in `self.list_preproc_available` or
        `self.list_preproc_applied`.
        """
        if source == "available":
            thelist = self.list_preproc_available
        elif source == "applied":
            thelist = self.list_preproc_applied
        item = thelist.currentItem()
        if item is None:
            return
        method_name = item.text()
        method = getattr(npreproc.IndentationPreprocessor, method_name)
        doc = method.__doc__.replace("    ", "").strip()
        self.text_preprocessing.setPlainText(doc)

    def preproc_set_preset(self):
        """Update preselection"""
        text = self.cb_preproc_presel.currentText()
        self.list_preproc_applied.clear()
        if text == "None":
            pass
        elif text == "Recommended":
            recommended_methods = ["compute_tip_position",
                                   "correct_force_offset",
                                   "correct_tip_offset",
                                   "correct_split_approach_retract"]
            for m in recommended_methods:
                item = QtWidgets.QListWidgetItem()
                item.setText(m)
                self.list_preproc_applied.addItem(item)

    def preproc_setup(self):
        """Setup everything necessary for the preprocessing tab"""
        # Get list of preprocessing methods
        mem = inspect.getmembers(npreproc.IndentationPreprocessor)
        premem = []
        for m in mem:
            if (m[1].__doc__ is not None and
                not m[0].startswith("_") and
                    not m[0] == "apply"):
                premem.append(m[0])

        premem.sort()

        for p in premem:
            item = QtWidgets.QListWidgetItem()
            item.setText(p)
            self.list_preproc_available.addItem(item)

        self.list_preproc_available.currentItemChanged.connect(
            lambda: self.preproc_descr_update("available"))
        self.list_preproc_applied.currentItemChanged.connect(
            lambda: self.preproc_descr_update("applied"))

        # Add recommended item (see `self.preproc_set_preset`)
        self.cb_preproc_presel.addItem("Recommended")
        self.cb_preproc_presel.activated.connect(self.preproc_set_preset)
        self.cb_preproc_presel.currentIndexChanged.connect(
            self.preproc_set_preset)
        # Apply recommended defaults
        self.cb_preproc_presel.setCurrentIndex(1)

    def rate_data(self, data):
        """Apply rating to curves

        Parameters
        ----------
        data: list, afmlib.indentaion.Indentation, afmlib.AFM_DataSet
           The data to be rated
        """
        if isinstance(data, nindent.Indentation):
            data = [data]
            return_single = True
        else:
            return_single = False

        scheme_id = self.cb_rating_scheme.currentIndex()
        scheme_key = list(RATING_SCHEMES.keys())[scheme_id]
        training_set, regressor = RATING_SCHEMES[scheme_key]
        rates = []
        for fdist in data:
            rt = fdist.rate_quality(regressor=regressor,
                                    training_set=training_set)
            rates.append(rt)

        if return_single:
            return rates[0]
        else:
            return rates

    @property
    def selected_curves(self):
        """Return an IndentationGroup with all curves selected by the user"""
        curves = nanite.IndentationGroup()
        for ar in self.data_set:
            idx = self.data_set.index(ar)
            item = self.list_curves.topLevelItem(idx)
            if item.checkState(3) == 2:
                curves.append(ar)
        return curves

    def signal_slot(self, enable):
        """Enable or disable signal-slot connections"""
        cn = [
            # Signals and slots
            # Fit all button
            [self.btn_fitall.clicked, self.on_fit_all],
            # Parameter changed
            [self.cb_segment.currentTextChanged, self.on_params_init],
            [self.cb_xaxis.currentTextChanged, self.on_params_init],
            [self.cb_yaxis.currentTextChanged, self.on_params_init],
            [self.cb_model.currentTextChanged, self.on_model],
            [self.cb_range_type.currentTextChanged, self.on_params_init],
            # This does not work for checkboxes
            [self.table_parameters_initial.itemChanged, self.on_params_init],
            # Filter rating threshold
            [self.btn_rating_filter.clicked, self.on_rating_threshold],
            # Toggle weighting of contact point data
            [self.cb_weight_cp.stateChanged, self.on_params_init],
            [self.sp_weight_cp_um.valueChanged, self.on_update_weights],
            [self.sp_weight_cp_perc.valueChanged, self.on_update_weights],
            # number of samples for Edelta plot
            [self.sp_delta_num_samples.valueChanged, self.on_params_init],
            [self.sp_delta_num_samples.valueChanged, self.mpl_edelta_update],
            # rating scheme dropdown
            [self.cb_rating_scheme.currentTextChanged, self.on_params_init],
        ]

        for signal, slot in cn:
            if enable:
                signal.connect(slot)
            else:
                signal.disconnect(slot)
