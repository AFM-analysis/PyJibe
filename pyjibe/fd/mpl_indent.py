from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
import numpy as np


from .. import units
from ..head import custom_widgets


class MPLIndentation(object):
    def __init__(self):
        """Matplotlib plot for force-indentation data"""
        # Add matplotlib figure
        self.figure = Figure(facecolor="none", tight_layout=True,
                             frameon=True)
        gs = gridspec.GridSpec(2, 1, height_ratios=[4, 1])

        # main axis
        self.axis_main = self.figure.add_subplot(gs[0])
        self.axis_main.grid()
        self.plots = {}
        self.axis_main.set_facecolor('#DDDDDD')
        self.plots["fit range"] = self.axis_main.axvspan(np.pi,
                                                         np.sqrt(2),
                                                         facecolor="#FFFFFF",
                                                         edgecolor="none",
                                                         label="fit range")
        self.plots["approach"] = self.axis_main.plot(range(10),
                                                     range(10),
                                                     color="#B1BDEF",
                                                     lw=2,
                                                     label="approach")[0]
        self.plots["retract"] = self.axis_main.plot(range(10),
                                                    range(10),
                                                    color="#EFB3B1",
                                                    lw=2,
                                                    label="retract")[0]
        self.plots["fit"] = self.axis_main.plot(range(10),
                                                range(10),
                                                color="blue",
                                                label="fit range")[0]

        # residuals
        self.axis_res = self.figure.add_subplot(gs[1], sharex=self.axis_main)
        self.axis_res.grid()
        self.plots["residuals"] = self.axis_res.plot(range(2),
                                                     range(2),
                                                     label="residuals")[0]

        self.canvas = FigureCanvas(self.figure)

        self.canvas.draw()

    def add_toolbar(self, widget):
        """Add toolbar to PyQT widget"""
        self.toolbar = custom_widgets.NavigationToolbarIndent(
            self.canvas,
            widget,
            coordinates=True
        )

        self.toolbar.save_data_callback = self.save_data_callback

    def save_data_callback(self, filename):
        self.fdist.export(filename)

    def update(self, fdist, rescale_x=None, rescale_y=None):
        self.fdist = fdist
        xaxis = "tip position"
        yaxis = "force"
        xscale = units.hrscale(xaxis)
        yscale = units.hrscale(yaxis)
        xunit = units.hrunit(xaxis)
        yunit = units.hrunit(yaxis)

        # approach and retract data
        for segment in ["approach", "retract"]:
            segment_bool = segment == "retract"
            self.plots[segment].set_data(
                fdist[xaxis][fdist["segment"] == segment_bool]*xscale,
                fdist[yaxis][fdist["segment"] == segment_bool]*yscale)

        self.axis_res.set_xlabel("{} [{}]".format(xaxis, xunit))
        self.axis_res.set_ylabel("residuals [{}]".format(yunit))
        self.axis_main.set_ylabel("{} [{}]".format(yaxis, yunit))

        if "fit" in fdist.data and np.sum(fdist["fit range"]):
            self.plots["residuals"].set_visible(True)
            self.plots["fit"].set_visible(True)
            self.plots["fit range"].set_visible(True)

            self.plots["fit"].set_data(fdist["tip position"]*xscale,
                                       fdist["fit"]*yscale)
            self.plots["residuals"].set_data(fdist["tip position"]*xscale,
                                             (fdist["fit residuals"])*yscale)
            # fit range
            xy = self.plots["fit range"].get_xy()
            fitrange = (fdist[xaxis]*xscale)[fdist["fit range"]]
            fitmin = np.min(fitrange)
            fitmax = np.max(fitrange)
            xy[:, 0] = fitmax
            xy[2:4, 0] = fitmin
            self.plots["fit range"].set_xy(xy)

            self.update_plot(rescale_x=rescale_x,
                             rescale_y=rescale_y)
        else:
            self.plots["residuals"].set_visible(False)
            self.plots["fit"].set_visible(False)
            self.plots["fit range"].set_visible(False)
            self.canvas.draw()

    def update_plot(self, rescale_x=None, rescale_y=None):
        """Update plot data range"""
        if rescale_x is None:
            fit_range = self.fdist["fit range"]
            xmin = np.min(self.plots["fit"].get_data()[0][fit_range])
            xmax = np.max(self.plots["fit"].get_data()[0][fit_range])
            xmargin = np.abs(xmax - xmin) * .05
            xmin -= xmargin
            xmax += xmargin
        else:
            xmin, xmax = rescale_x

        if xmin == xmax:
            xmin = xmax = np.nan

        if rescale_y is None:
            fit_range = self.fdist["fit range"]
            ymin = np.min(self.plots["fit"].get_data()[1][fit_range])
            ymax = np.max(self.plots["fit"].get_data()[1][fit_range])
            ymargin = np.abs(ymax - ymin) * .05
            ymin -= ymargin
            ymax += ymargin
        else:
            ymin, ymax = rescale_y

        if ymin == ymax:
            ymin = ymax = np.nan

        if not np.isnan(xmin + xmax):
            # x: main plot and residuals
            axes = self.axis_main, self.axis_res
            for ax in axes:
                ax.set_xlim(xmin, xmax)
        if not np.isnan(ymin + ymax):
            # y: main plot
            self.axis_main.set_ylim(ymin, ymax)
        # set residuals ylim automatically
        rmin = np.nanmin(self.plots["residuals"].get_data()[1])
        rmax = np.nanmax(self.plots["residuals"].get_data()[1])
        if not np.isnan(rmin + rmax):
            rmax = max(abs(rmin), abs(rmax))
            rmax = np.ceil(rmax*10) / 10
            rmin = -rmax
            # y: main plot
            self.axis_res.set_ylim(rmin, rmax)

        self.canvas.draw()
