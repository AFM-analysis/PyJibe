import pkg_resources

from nanite import preproc
from PyQt5 import uic, QtCore, QtWidgets

from .widget_preprocess_item import WidgetPreprocessItem


class TabPreprocess(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabPreprocess, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_preprocess.ui")
        uic.loadUi(path_ui, self)

        # Setup everything necessary for the preprocessing tab:
        # Get list of preprocessing methods
        premem = preproc.available()

        self._map_widgets_to_preproc_ids = {}
        for pid in premem:
            pwidget = WidgetPreprocessItem(identifier=pid, parent=self)
            self._map_widgets_to_preproc_ids[pwidget] = pid
            self.layout_preproc_area.addWidget(pwidget)
            pwidget.preproc_step_changed.connect(self.on_preproc_step_changed)
        spacer_item = QtWidgets.QSpacerItem(20, 0,
                                            QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.layout_preproc_area.addItem(spacer_item)

        # Add recommended item (see `self.preproc_set_preset`)
        self.cb_preproc_presel.addItem("Recommended")
        self.on_preset_changed()
        self.cb_preproc_presel.activated.connect(self.on_preset_changed)
        self.cb_preproc_presel.currentIndexChanged.connect(
            self.on_preset_changed)
        # Apply recommended defaults
        self.cb_preproc_presel.setCurrentIndex(1)

    @property
    def fd(self):
        return self.parent().parent().parent().parent()

    def apply_preprocessing(self, fdist=None):
        """Apply the preprocessing steps if required"""
        if fdist is None:
            if hasattr(self, "fd"):
                fdist = self.fd.current_curve
            else:
                # initialization not finished
                return
        identifiers, options = self.current_preprocessing()
        # Perform preprocessing
        preproc_visible = self.fd.stackedWidget.currentWidget() == \
            self.fd.widget_plot_preproc
        details = fdist.apply_preprocessing(identifiers,
                                            options=options,
                                            ret_details=preproc_visible)
        if preproc_visible:
            self.fd.widget_plot_preproc.update_details(details)

    @QtCore.pyqtSlot()
    def on_preproc_step_changed(self):
        self.check_selection()
        self.apply_preprocessing()

    @QtCore.pyqtSlot()
    def check_selection(self):
        """If the user selects an item, make sure requirements are checked"""
        sender = self.sender()
        state = sender.isChecked()
        if sender in self._map_widgets_to_preproc_ids:
            pid = self._map_widgets_to_preproc_ids[sender]
            if state:
                # Enable all steps that this step here requires
                req_stps = preproc.get_steps_required(pid)
                if req_stps:
                    for pwid in self._map_widgets_to_preproc_ids:
                        if (self._map_widgets_to_preproc_ids[pwid] in req_stps
                                and not pwid.isChecked()):
                            # Prevent every pwid from sending out signals!
                            # Instead call `check_selection` every time.
                            pwid.blockSignals(True)
                            pwid.setChecked(True)
                            pwid.blockSignals(False)
                            self.check_selection()
            else:
                # Disable all steps that depend on this one
                for dwid in self._map_widgets_to_preproc_ids:
                    did = self._map_widgets_to_preproc_ids[dwid]
                    req_stps = preproc.get_steps_required(did)
                    if req_stps and pid in req_stps and dwid.isChecked():
                        # Prevent every dwid from sending out signals!
                        # Instead call `check_selection` every time.
                        dwid.blockSignals(True)
                        dwid.setChecked(False)
                        dwid.blockSignals(False)
                        self.check_selection()

    def current_preprocessing(self):
        # Note: Preprocessing is cached once in `fdist`.
        # Thus calling this method a second time without any
        # change in the GUI is free.
        identifiers = []
        options = {}
        for pwidget in self._map_widgets_to_preproc_ids:
            pid = self._map_widgets_to_preproc_ids[pwidget]
            if pwidget.isChecked():
                identifiers.append(pid)
                popts = pwidget.get_options()
                if popts:
                    options[pid] = popts
        # Make sure the order is correct
        identifiers = preproc.autosort(identifiers)
        return identifiers, options

    @QtCore.pyqtSlot()
    def on_preset_changed(self):
        """Update preselection"""
        text = self.cb_preproc_presel.currentText()
        if text == "None":
            used_methods = []
            method_options = {}
        elif text == "Recommended":
            used_methods = ["compute_tip_position",
                            "correct_force_offset",
                            "correct_tip_offset",
                            "correct_split_approach_retract"]
            method_options = {
                "correct_tip_offset": [
                    {"method": "deviation_from_baseline"},
                ],
            }
        else:
            raise ValueError(f"Unknown text '{text}'!")

        for pwidget in self._map_widgets_to_preproc_ids:
            pwidget.blockSignals(True)
            pid = self._map_widgets_to_preproc_ids[pwidget]
            pwidget.setChecked(pid in used_methods)
            # Set default values
            if pid in method_options:
                for item in method_options[pid]:
                    for name in item:
                        pwidget.set_option(name=name,
                                           value=item[name])
            pwidget.blockSignals(False)
        self.apply_preprocessing()

    def set_preprocessing(self, preprocessing, options=None):
        """Set preprocessing (mostly used for testing)"""
        if options is None:
            options = {}
        for pwidget in self._map_widgets_to_preproc_ids:
            pid = self._map_widgets_to_preproc_ids[pwidget]
            pwidget.setChecked(pid in preprocessing)
            if pid in options:
                opts = options[pid]
                name = sorted(opts.keys())[0]  # not future-proof
                pwidget.set_option(name=name, value=opts[name])
