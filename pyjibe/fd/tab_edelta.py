import pkg_resources

import numpy as np
from PyQt5 import uic, QtWidgets

from .. import units
from .mpl_edelta import MPLEDelta


class TabEdelta(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabEdelta, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_edelta.ui")
        uic.loadUi(path_ui, self)

        self.mpl_edelta_setup()

        # signals
        self.delta_spin.setValue(-np.inf)
        # Slider
        self.delta_slider.setMaximum(0)
        self.delta_spin.valueChanged["double"].connect(
            self.on_delta_change_spin)
        self.delta_slider.sliderReleasedFloat["double"].connect(
            self.on_delta_change_spin)
        self.delta_slider.valueChangedFloat["double"].connect(
            self.mpl_edelta.update_delta)
        self.delta_btn_guess.clicked.connect(self.on_delta_guess)
        self.sp_delta_num_samples.valueChanged.connect(self.mpl_edelta_update)

    @property
    def current_curve(self):
        return self.fd.current_curve

    @property
    def fd(self):
        return self.parent().parent().parent().parent()

    def mpl_edelta_setup(self):
        """Setup the matplotlib interface for E(delta) plotting"""
        self.mpl_edelta = MPLEDelta()
        self.mpl_edelta.add_toolbar(self.edelta_mplwidget)
        self.edelta_mpllayout.addWidget(self.mpl_edelta.canvas)
        self.edelta_mpllayout.addWidget(self.mpl_edelta.toolbar)

    def mpl_edelta_update(self):
        """Update the E(delta) plot"""
        if self.fd.tabs.currentWidget() == self:
            fdist = self.current_curve
            delta_opt = self.fd.tab_fit.sp_range_1.value()
            # Update slider range
            xaxis = self.fd.tab_fit.cb_xaxis.currentText()
            segment = self.fd.tab_fit.cb_segment.currentText().lower()
            segment_bool = segment == "retract"
            segid = fdist["segment"] == segment_bool
            xdata = fdist[xaxis]
            xscale = units.hrscale(xaxis)
            minx = np.min(xdata[segid])*xscale
            self.delta_slider.blockSignals(True)
            self.delta_slider.setMinimum(minx)
            self.delta_slider.setValue(delta_opt)
            self.delta_slider.blockSignals(False)
            # Update E(delta) plot
            self.fd.tab_fit.fit_approach_retract(fdist)
            self.mpl_edelta.update(fdist, delta_opt)

    def on_delta_guess(self):
        """Guess the optimal indentation depth for the current curve"""
        fdist = self.current_curve
        value = fdist.estimate_optimal_mindelta()
        value /= units.scales["µ"]
        self.delta_spin.setValue(value)

    def on_delta_change_spin(self, value):
        """Indentation depth spin control value changed"""
        # Update all controls
        self.fd.tab_fit.sp_range_1.blockSignals(True)
        self.delta_spin.blockSignals(True)
        self.delta_slider.blockSignals(True)

        self.delta_spin.setValue(value)
        self.delta_slider.setValue(value)
        self.fd.tab_fit.sp_range_1.setValue(value)
        self.mpl_edelta.update_delta(value)
        self.fd.on_params_init()

        self.fd.tab_fit.sp_range_1.blockSignals(False)
        self.delta_spin.blockSignals(False)
        self.delta_slider.blockSignals(False)
