from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)

from ..head import custom_widgets


class MPLPreproc:
    def __init__(self):
        """Matplotlib plot for preprocessing data"""
        # Add matplotlib figure
        self.figure = Figure(facecolor="none", tight_layout=True,
                             frameon=True)
        self.axis = self.figure.add_subplot(111)
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

    def clear(self):
        self.axis.clear()
        self.axis.grid()
