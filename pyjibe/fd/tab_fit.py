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

        # initial values, sources, drains for indentation depth
        self.indentation_depth_setup()

        # signals
        self.cb_segment.currentTextChanged.connect(self.on_params_init)
        self.cb_xaxis.currentTextChanged.connect(self.on_params_init)
        self.cb_yaxis.currentTextChanged.connect(self.on_params_init)
        self.cb_model.currentTextChanged.connect(self.on_model)
        self.cb_range_type.currentTextChanged.connect(self.on_params_init)
        self.table_parameters_initial.itemChanged.connect(self.on_params_init)
        self.cb_weight_cp.stateChanged.connect(self.on_params_init)
        self.sp_weight_cp_um.valueChanged.connect(self.on_update_weights)
        self.sp_weight_cp_perc.valueChanged.connect(self.on_update_weights)

    @property
    def current_curve(self):
        return self.fd.current_curve

    @property
    def fd(self):
        return self.parent().parent().parent().parent()

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
        if self.cb_delta_select.currentIndex() == 2:
            optimal_fit_edelta = True
        else:
            optimal_fit_edelta = False
        # number of samples for edelta plot
        tab_edelta = self.fd.tab_edelta
        optimal_fit_num_samples = tab_edelta.sp_delta_num_samples.value()
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
            self.fd.autosave(fdist)
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
        if self.cb_delta_select.currentIndex() == 1:
            # Set indentation depth individually
            if fdist in self._indentation_depth_individual:
                value = self._indentation_depth_individual[fdist]
                self.fd.tab_edelta.delta_spin.setValue(value)
            else:
                value = self.fd.tab_edelta.delta_spin.value()
                self._indentation_depth_individual[fdist] = value

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

    def on_model(self):
        self.fd.on_model()

    def on_params_init(self):
        self.fd.on_params_init()

    def on_delta_select(self, value):
        """The user selected a method for indentation depth determination

        This method is called when `tab_fit.cb_delta_select` or (indirectly)
        `tab_edelta.cb_delta_select` are changed.

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
        local_enable = [self.fd.tab_edelta.delta_label,
                        self.fd.tab_edelta.delta_spin,
                        self.fd.tab_edelta.delta_slider,
                        self.fd.tab_edelta.delta_btn_guess]

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
                value = self.fd.tab_edelta.delta_spin.value()
            self.fd.tab_edelta.delta_spin.setValue(value)

        elif value == 2:
            # Guess optimal indentation depth
            [item.setEnabled(False) for item in global_disable]
            [item.setEnabled(False) for item in local_enable]
            self.cb_range_type.setEnabled(False)
            self.cb_range_type.setCurrentText("absolute")

        self.on_params_init()

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
