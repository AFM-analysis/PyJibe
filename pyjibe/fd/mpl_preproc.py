import collections

from cycler import cycler
import matplotlib.pylab as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
import numpy as np

from ..head import custom_widgets


class MPLPreproc:
    def __init__(self):
        """Matplotlib plot for preprocessing data"""
        # Add matplotlib figure
        self.figure = Figure(facecolor="none", tight_layout=True,
                             frameon=True)
        self.axis = self.figure.add_subplot(111)
        self.twin_axes = collections.OrderedDict()
        self.axis.set_facecolor('#FFFFFF')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.draw()

    def add_toolbar(self, widget):
        """Add toolbar to PyQT widget"""
        self.toolbar = custom_widgets.NavigationToolbarPreproc(
            self.canvas,
            widget,
            coordinates=True
        )

    def get_normed_axis(self, name):
        """Get the proper axis to plot to

        All axes share the same x-axis, but might have a different y-axis.
        We identify the differently normed axis via `name`.
        """
        if name not in self.twin_axes:
            if not self.twin_axes:
                # No twin axis has been created yet, so populate the
                # dictionary with the initial axis.
                self.twin_axes[name] = self.axis
            else:
                self.twin_axes[name] = self.axis.twinx()
        # Let all plots share the same color cycler (so we don't have
        # the same color for different lines).
        # Get the number of lines currently plotted.
        nl = self.get_num_lines()
        colors = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        new_colors = np.roll(colors, -nl).tolist()
        self.twin_axes[name].set_prop_cycle(
            cycler(color=new_colors))
        return self.twin_axes[name]

    def get_num_lines(self):
        lines = []
        for ax in self.twin_axes:
            lines2, _ = self.twin_axes[ax].get_legend_handles_labels()
            lines += lines2
        return len(lines)

    def clear(self):
        self.axis.clear()
        for ax in self.twin_axes:
            self.twin_axes[ax].clear()
        self.axis.grid()

    def legend(self):
        lines, labels = [], []
        for ax in self.twin_axes:
            lines2, labels2 = self.twin_axes[ax].get_legend_handles_labels()
            lines += lines2
            labels += labels2
        if self.twin_axes:
            axtop = list(self.twin_axes.values())[-1]
            axtop.legend(lines, labels)
