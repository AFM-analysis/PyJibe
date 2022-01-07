import pkg_resources

import nanite.model as nmodel
import numpy as np
from PyQt5 import uic, QtCore, QtWidgets

from .. import units


class TabFit(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabFit, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_fit.ui")
        uic.loadUi(path_ui, self)

        # Setup the fitting tab
        id_para = 0
        # Model selection
        models_av = list(nmodel.models_available.keys())
        # Exact spherical model is only available in developer mode
        self.settings = QtCore.QSettings()
        self.settings.setIniCodec("utf-8")
        dev_mode = bool(int(
            self.settings.value("advanced/developer mode", "0")))
        exp_mode = bool(int(
            self.settings.value("advanced/expert mode", "0")))
        if not dev_mode:
            models_av.remove("sneddon_spher")
        if not (dev_mode or exp_mode):
            self.widget_method.hide()
        models_av.sort(key=lambda x: nmodel.models_available[x].model_name)
        for ii, key in enumerate(models_av):
            model = nmodel.models_available[key]
            self.cb_model.addItem(model.model_name, key)
            if key == "hertz_para":
                id_para = ii
        # Setz Hertz Parabolic as default
        self.cb_model.setCurrentIndex(id_para)
        # Axis selection
        self.cb_xaxis.addItem("tip position")
        self.cb_yaxis.addItem("force")

        # initial values, sources, drains for indentation depth
        self.indentation_depth_setup()

        # hide option to set right part of fitting range individually
        # (will be displayed when indentation depth is set individually,
        # i.e. `self.cb_delta_select.currentIndex == 1`)
        self.cb_right_individ.setVisible(False)

        # Show axes selection only in developer mode
        for wid in [self.label_axes, self.widget_axes]:
            wid.setVisible(dev_mode)

        # signals
        self.cb_segment.currentIndexChanged.connect(self.on_params_init)
        self.cb_xaxis.currentIndexChanged.connect(self.on_params_init)
        self.cb_yaxis.currentIndexChanged.connect(self.on_params_init)
        self.cb_model.currentIndexChanged.connect(self.on_model)
        self.cb_range_type.currentTextChanged.connect(self.on_params_init)
        self.table_parameters_anc.itemChanged.connect(self.on_params_anc)
        self.table_parameters_initial.itemChanged.connect(self.on_params_init)
        self.cb_weight_cp.stateChanged.connect(self.on_params_init)
        self.sp_weight_cp_um.valueChanged.connect(self.on_update_weights)
        self.sp_weight_cp_perc.valueChanged.connect(self.on_update_weights)
        self.toolButton_method_apply.clicked.connect(self.on_params_init)
        self.sp_gcfk.valueChanged.connect(self.on_params_init)

    @property
    def current_curve(self):
        return self.fd.current_curve

    @property
    def fd(self):
        return self.parent().parent().parent().parent()

    @property
    def fit_model(self):
        return nmodel.models_available[self.cb_model.currentData()]

    def anc_update_parameters(self, fdist):
        model_key = self.fit_model.model_key
        # Apply the current set of parameters
        # (some ancillary parameters depend on the correct initial parameters)
        fdist.fit_properties["params_initial"] = self.fit_parameters()
        # ancillaries
        anc = fdist.get_ancillary_parameters(model_key=model_key)
        anc_used = [ak for ak in anc if ak in self.fit_model.parameter_keys]
        if anc_used:
            self.widget_anc.setVisible(True)
            itab = self.table_parameters_initial
            atab = self.table_parameters_anc
            atab.blockSignals(True)
            rows_changed = self.assert_parameter_table_rows(atab,
                                                            len(anc_used),
                                                            cb_first=True,
                                                            read_only=True)
            row = 0
            for ak in self.fit_model.parameter_anc_keys:
                if ak not in anc_used:
                    continue
                # Get the human-readable name of the parameter
                hrname = self.fit_model.get_parm_name(ak)
                # Determine unit scale, e.g. 1e6 [sic] for µm
                si_unit = self.fit_model.get_parm_unit(ak)
                # Determine unit scale, e.g. 1e6 [sic] for µm
                scale = units.hrscale(hrname, si_unit=si_unit)
                label = units.hrscname(hrname, si_unit=si_unit)
                value_text = "{:.5g}".format(anc[ak] * scale)
                atab.verticalHeaderItem(row).setText(label)
                if rows_changed:
                    atab.item(row, 0).setCheckState(QtCore.Qt.Checked)
                atab.item(row, 1).setText(value_text)
                # updates initial parameters if "use" is checked
                if atab.item(row, 0).checkState() == QtCore.Qt.Checked:
                    # update initial parameters
                    for rr in range(itab.rowCount()):
                        if itab.verticalHeaderItem(rr).text() == label:
                            if value_text != "nan":
                                itab.item(rr, 1).setText(value_text)
                row += 1
            atab.blockSignals(False)
        else:
            self.widget_anc.setVisible(False)

    def assert_parameter_table_rows(self, table, rows, cb_first=False,
                                    read_only=False):
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

        Returns
        -------
        rows_changed: bool
            Whether the number of rows changed
        """
        rows_changed = (table.rowCount() - rows) != 0
        table.setRowCount(rows)
        cols = table.columnCount()
        for rr in range(rows):
            hitem = QtWidgets.QTableWidgetItem()
            table.setVerticalHeaderItem(rr, hitem)
            for cc in range(cols):
                if table.item(rr, cc) is None:
                    item = QtWidgets.QTableWidgetItem()
                    table.setItem(rr, cc, item)
                else:
                    item = table.item(rr, cc)
                if cc == 0 and cb_first:
                    item.setFlags(QtCore.Qt.ItemIsUserCheckable
                                  | QtCore.Qt.ItemIsEnabled
                                  | QtCore.Qt.ItemIsEditable)
                elif read_only:
                    item.setFlags(QtCore.Qt.ItemIsEnabled)
                else:
                    item.setFlags(QtCore.Qt.ItemIsEnabled
                                  | QtCore.Qt.ItemIsEditable)

        return rows_changed

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
        dev_mode = bool(int(
            self.settings.value("advanced/developer mode", "0")))
        exp_mode = bool(int(
            self.settings.value("advanced/expert mode", "0")))
        # segment
        segment = self.cb_segment.currentText().lower()
        # x axis
        x_axis = self.cb_xaxis.currentText()
        # y axis
        y_axis = self.cb_yaxis.currentText()
        # Get model key from dropdown list
        model_key = self.fit_model.model_key
        # Geometric factor
        gcf_k = self.sp_gcfk.value()
        # Determine range type
        if self.cb_range_type.currentText() == "absolute":
            range_type = "absolute"
        else:
            range_type = "relative cp"
        # Determine range
        range_x = [self.sp_range_1.value() * units.scales["µ"],
                   self.sp_range_2.value() * units.scales["µ"]]
        # Remember range if applicable
        if self.cb_delta_select.currentIndex() == 1:
            self._indentation_depth_individual[fdist] = (
                self.sp_range_1.value(), self.sp_range_2.value())
        # Determine if we want to weight the contact point
        self.on_update_weights(on_params_init=False)
        if self.cb_weight_cp.checkState() == 2:
            weight_cp = self.sp_weight_cp_um.value() * units.scales["µ"]
        else:
            weight_cp = False
        # Determine if we want to autodetect the optimal indentation depth
        if self.cb_delta_select.currentIndex() == 2:
            optimal_fit_edelta = True
        else:
            optimal_fit_edelta = False
        # number of samples for edelta plot
        tab_edelta = self.fd.tab_edelta
        optimal_fit_num_samples = tab_edelta.sp_delta_num_samples.value()
        # fit parameters
        params = self.fit_parameters()
        # fit method (if in developer mode)
        kwargs = {}
        if dev_mode or exp_mode:
            # We are in developer or expert mode.
            # Populate the user-defined keyword arguments. Note that
            # these are not passed as "options", but directly to the
            # minimizer method.
            # See https://github.com/lmfit/lmfit-py/discussions/766
            method_kws = {}
            for item in self.lineEdit_method.text().strip().split():
                key, val = item.split("=", 1)
                method_kws[key] = float(val)
            kwargs = {
                "method": self.comboBox_method.currentText(),
                "method_kws": method_kws,
            }
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
                        gcf_k=gcf_k,
                        **kwargs
                        )
        ftab = self.table_parameters_fitted
        success = fdist.fit_properties.get("success", False)
        if success:
            # Perform automatic saving of results
            self.fd.autosave(fdist)
            # Display automatically detected optimal indentation depth
            if optimal_fit_edelta:
                # Set guessed indentation depth in GUI
                val = fdist.fit_properties["optimal_fit_delta"]
                self.sp_range_1.setValue(val / units.scales["µ"])

        if update_ui:
            # Display fit results in `self.table_parameters_fitted`
            if success:
                # use fit parameters only
                showpar = fdist.fit_properties["params_fitted"]
            else:
                # use initial parameters
                showpar = fdist.fit_properties["params_initial"]
            # Display all varied parameters and expression parameters
            # (expression parameters are discouraged, but supported).
            dispars = [p for p in showpar.values() if p.vary or p.expr]
            # Show hidden parameters only in dev mode
            if not dev_mode:
                dispars = [p for p in dispars if not p.name.startswith("_")]
            self.assert_parameter_table_rows(ftab, len(dispars),
                                             read_only=True)
            for ii, p in enumerate(dispars):
                # Get the human-readable name of the parameter
                hrname = self.fit_model.get_parm_name(p.name)
                # SI unit
                si_unit = self.fit_model.get_parm_unit(p.name)
                # Determine unit scale, e.g. 1e6 [sic] for µm
                scale = units.hrscale(hrname, si_unit=si_unit)
                label = units.hrscname(hrname, si_unit=si_unit)
                ftab.verticalHeaderItem(ii).setText(label)
                if success:
                    ftab.item(ii, 0).setText("{:.5g}".format(p.value * scale))
                else:
                    ftab.item(ii, 0).setText("nan")

    def fit_parameters(self):
        """Return initial fit parameters currently set in the GUI

        The parameter data is read out from
        `self.table_parameters_initial`. If the model that was
        previously set does not match the current model, only the
        parameters with the same name (existing in both models) are
        updated.
        """
        # Get model key from dropdown list
        model_key = self.fit_model.model_key
        # Get parameters from `self.table_parameters_initial`
        model = nmodel.models_available[model_key]
        params = model.get_parameter_defaults()
        itab = self.table_parameters_initial
        if itab.verticalHeaderItem(0):
            # Only update if there is already something set
            for ii, key in enumerate(list(params.keys())):
                p = params[key]
                if p.expr:
                    # Parameter has an expression, no update necessary
                    continue
                # Determine the scale for which we need to revert
                # the multiplications.
                # performed in `fit_update_parameters`.
                hrname = model.parameter_names[ii]
                si_unit = model.parameter_units[ii]
                scale = units.hrscale(hrname, si_unit=si_unit)
                label = units.hrscname(hrname, si_unit=si_unit)
                for rr in range(itab.rowCount()):
                    # search for a row matching the parameter `p`
                    if itab.verticalHeaderItem(rr).text() == label:
                        # update parameter `p`
                        state = itab.item(rr, 0).checkState()
                        if state == QtCore.Qt.Unchecked:
                            p.vary = True
                        else:
                            p.vary = False
                        p.set(float(itab.item(rr, 1).text()) / scale)
                        p.min = float(itab.item(rr, 2).text()) / scale
                        p.max = float(itab.item(rr, 3).text()) / scale
                        break
        return params

    def fit_update_parameters(self, fdist):
        """Update the ancillary and initial parameters in the UI"""
        dev_mode = bool(int(
            self.settings.value("advanced/developer mode", "0")))
        model_key = self.fit_model.model_key

        # set the model
        # - resets params_initial if model changed
        # - important for computing ancillary parameters
        fdist.fit_properties["model_key"] = model_key
        if fdist.fit_properties.get("params_initial", False):
            # (cannot coerce this into one line, because "params_initial"
            # can be None.)
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

        params.update_constraints()  # in case we have expressions
        par_names = list(params.keys())
        # Remove hidden parameters from the list. These are parameters that
        # are important for the fit, but that users are not supposed to modify.
        # Do not remove hidden parameters if in dev mode.
        if not dev_mode:
            par_names = [p for p in par_names if not p.startswith("_")]
        self.assert_parameter_table_rows(itab, len(par_names), cb_first=True)
        for ii, key in enumerate(par_names):
            p = params[key]
            # Get the human readable name of the parameter
            hrname = self.fit_model.get_parm_name(key)
            # SI unit
            si_unit = self.fit_model.get_parm_unit(key)
            # Determine unit scale, e.g. 1e6 [sic] for µm
            scale = units.hrscale(hrname, si_unit=si_unit)
            label = units.hrscname(hrname, si_unit=si_unit)
            itab.verticalHeaderItem(ii).setText(label)
            if p.vary:
                state = QtCore.Qt.Unchecked
            else:
                state = QtCore.Qt.Checked
            itab.item(ii, 0).setCheckState(state)
            itab.item(ii, 1).setText("{:.5g}".format(p.value * scale))
            itab.item(ii, 2).setText(str(p.min * scale))
            itab.item(ii, 3).setText(str(p.max * scale))
            # grey out/disable expression parameters
            if p.expr:
                for jj in range(4):
                    item = itab.item(ii, jj)
                    if jj == 0:  # check box
                        item.setCheckState(QtCore.Qt.Unchecked)
                    item.setFlags(QtCore.Qt.NoItemFlags)

        itab.blockSignals(False)

        # indentation depth
        if self.cb_delta_select.currentIndex() == 1:
            # Set indentation depth individually
            if fdist in self._indentation_depth_individual:
                left, right = self._indentation_depth_individual[fdist]
                self.fd.tab_edelta.delta_spin.setValue(left)
                if self.cb_right_individ.isChecked() and right is not None:
                    self.sp_range_2.setValue(right)

        # ancillaries
        self.anc_update_parameters(fdist)

    def indentation_depth_setup(self):
        """Initiate ranges (spin/slider) that allow inf values"""
        # Initialize individual indentation depth dictionary
        self._indentation_depth_individual = {}
        # Left
        self.sp_range_1.setValue(-np.inf)
        # Right
        self.sp_range_2.setValue(np.inf)
        # Signals
        self.cb_delta_select.currentIndexChanged['int'].connect(
            self.on_delta_select)

    @QtCore.pyqtSlot()
    def on_model(self):
        self.fd.on_model()

    @QtCore.pyqtSlot()
    def on_params_anc(self):
        self.fd.on_params_init()

    @QtCore.pyqtSlot()
    def on_params_init(self):
        self.fd.on_params_init()

    @QtCore.pyqtSlot(int)
    def on_delta_select(self, index):
        """The user selected a method for indentation depth determination

        This method is called when `tab_fit.cb_delta_select` or (indirectly)
        `tab_edelta.cb_delta_select` are changed.

        At the end, `on_params_init` is called, to redo the fit. After
        fitting, the indentation depth (`sp_range_1`) will be set by
        `fit_approach_retract`, if `value==2`.

        Parameters
        ----------
        index: int
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
        local_enable = [self.fd.tab_edelta.delta_label,
                        self.fd.tab_edelta.delta_spin,
                        self.fd.tab_edelta.delta_slider,
                        self.fd.tab_edelta.delta_btn_guess]

        if index == 0:
            # Set indentation depth globally
            [item.setEnabled(True) for item in global_disable]
            [item.setEnabled(False) for item in local_enable]
            self.cb_range_type.setEnabled(True)
        elif index == 1:
            # Set indentation depth individually
            [item.setEnabled(True) for item in global_disable]
            [item.setEnabled(True) for item in local_enable]
            self.cb_range_type.setEnabled(False)
            self.cb_range_type.setCurrentText("absolute")
            # Set/get indentation depth individually
            fdist = self.current_curve
            if fdist in self._indentation_depth_individual:
                left = self._indentation_depth_individual[fdist][0]
            else:
                left = self.fd.tab_edelta.delta_spin.value()
            self.fd.tab_edelta.delta_spin.setValue(left)
        elif index == 2:
            # Guess optimal indentation depth
            [item.setEnabled(False) for item in global_disable]
            [item.setEnabled(False) for item in local_enable]
            self.cb_range_type.setEnabled(False)
            self.cb_range_type.setCurrentText("absolute")
        else:
            raise ValueError("Invalid index '{}'!".format(index))

        # enable checkbox for right range
        if index == 1:
            self.cb_right_individ.setVisible(True)
        else:
            self.cb_right_individ.setVisible(False)
            self.cb_right_individ.setChecked(False)
        self.on_params_init()

    @QtCore.pyqtSlot()
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
        params = self.fit_parameters()
        if "R" in params:
            radius = params["R"].value * units.hrscale("tip radius")
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
                self.sp_weight_cp_um.setValue(radius * perc / 100)
                self.sp_weight_cp_um.blockSignals(False)
            else:
                # set percent value
                val = self.sp_weight_cp_um.value()
                self.sp_weight_cp_perc.blockSignals(True)
                self.sp_weight_cp_perc.setValue(val / radius * 100)
                self.sp_weight_cp_perc.blockSignals(False)
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
