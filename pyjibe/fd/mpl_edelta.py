import io

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)

import nanite.fit as nfit
import numpy as np
from PyQt5.QtWidgets import QApplication


from .. import units
from ..head import custom_widgets


class MPLEDelta(object):
    def __init__(self):
        self.figure = Figure(facecolor="none", tight_layout=False)
        # verbose text if no map data is available
        self.no_data_text = self.figure.text(.5, .5,
                                             "no E(δ) data available",
                                             horizontalalignment="center")
        self.no_data_text.set_visible(False)
        # main axis
        self.axis_main = self.figure.add_subplot(111)
        self.axis_main.grid()
        self.plot = self.axis_main.plot(range(10), range(10))[0]
        self.opt_auto = self.axis_main.axvline(5, c="r")
        self.canvas = FigureCanvas(self.figure)

        self.canvas.draw()
        se = units.hrunit("young's modulus")
        sd = units.hrunit("tip radius")
        self.axis_main.set_xlabel("indentation depth δ [{}]".format(sd))
        self.axis_main.set_ylabel("elastic modulus E [{}]".format(se))
        # adjust suplot parameters left,bottom,right,top
        self.figure.subplots_adjust(0.2, 0.15, 0.95, 0.95)

        # Update parameters
        self._update_in_progress_locks = {}
        self._update_in_progress_active = None

    def add_toolbar(self, widget):
        self.toolbar = custom_widgets.NavigationToolbarEDelta(
            self.canvas,
            widget,
            coordinates=True
        )
        self.toolbar.save_data_callback = self.save_data_callback

    def hide_plot(self, boolval):
        self.axis_main.set_visible(not boolval)
        self.no_data_text.set_visible(boolval)
        self.toolbar.setDisabled(boolval)

    def save_data_callback(self, filename):
        """Save current image as tsv"""
        with io.open(filename, "w") as fd:
            fd.write("indentation depth [m]\telastic modulus [Pa]\n")
        with io.open(filename, "ab") as fd:
            np.savetxt(fd, self.plot_data, delimiter="\t")

    def update(self, fdist, delta_opt=None):
        """Update the map tab plot data

        Parameters
        ----------
        fdist: afmlib.Indentation
            Approach-Retract data set
        delta_opt: float
            Optimal indentation depth
        """
        # TODO:
        # - use Python threading instead of this lambda method?
        self._update_in_progress_active = fdist
        if fdist in self._update_in_progress_locks:
            QApplication.instance().processEvents()
        else:
            self._update_in_progress_locks[fdist] = True
            def cbfdist(e, d): return self.update_plot(e, d, fdist=fdist)
            try:
                emod, delta = fdist.compute_emodulus_mindelta(callback=cbfdist)
            except nfit.FitDataError:
                # Could not generate E(d) plot due to weird data
                self.hide_plot(True)
                self.canvas.draw()
            else:
                self.update_plot(emod, delta, delta_opt, fdist=fdist)
            self._update_in_progress_locks.pop(fdist)

    def update_delta(self, delta):
        """Updates the vertical line for indentation depth"""
        self.opt_auto.set_data(delta, (0, 1))
        self.canvas.draw()

    def update_plot(self, emoduli, indentations,
                    delta_opt=None, fdist=None):
        """
        Parameters
        ----------
        emoduli: 1d ndarray
            emodulus values
        mindelta: 1d ndarray
            minimal indentation
        """
        self.hide_plot(False)
        if self._update_in_progress_active is fdist:
            fact_emod = units.hrscale("young's modulus")
            fact_delt = units.hrscale("tip radius")

            emoduli_p = emoduli*fact_emod
            mindeltas_p = indentations*fact_delt
            self.plot.set_data(mindeltas_p, emoduli_p)
            self.axis_main.set_xlim(mindeltas_p.min(), mindeltas_p.max())
            self.axis_main.set_ylim(emoduli_p.min(), emoduli_p.max())
            if delta_opt is not None:
                self.opt_auto.set_data(delta_opt, (0, 1))
            self.canvas.draw()

            self.plot_data = np.zeros((emoduli.size, 2), dtype=float)
            self.plot_data[:, 0] = indentations
            self.plot_data[:, 1] = emoduli

            QApplication.processEvents()
