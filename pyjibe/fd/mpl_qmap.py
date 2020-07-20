import copy
import io

import matplotlib as mpl
from matplotlib import pyplot
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvasQTAgg as FigureCanvas)
import matplotlib.patches as mpatches
from mpl_toolkits.axes_grid1 import make_axes_locatable
import numpy as np


from ..head import custom_widgets


rc = {"color_invalid": "k",
      "color_map": "viridis",
      "color_map_over": "w",
      "color_map_under": "w",
      }


class MPLQMap(object):
    def __init__(self):
        """Matplotlib plot for 2D quantitative map data"""
        # Do not use tight_layout (adjust subplot parameters instead)
        self.figure = Figure(facecolor="none", tight_layout=False)
        # verbose text if no map data is available
        self.no_data_text = self.figure.text(.5, .5,
                                             "no map data available",
                                             horizontalalignment="center")
        self.no_data_text.set_visible(False)
        # main axis
        self.axis_main = self.figure.add_subplot(111)
        cmap = copy.copy(mpl.cm.get_cmap(rc["color_map"]))
        cmap.set_over(rc["color_map_over"], 1)
        cmap.set_under(rc["color_map_under"], 1)
        self.plot = self.axis_main.imshow(np.zeros((10, 10)),
                                          interpolation="none",
                                          origin='lower',
                                          cmap=cmap)
        self.canvas = FigureCanvas(self.figure)

        self.axis_main.set_xlabel("position x [µm]")
        self.axis_main.set_ylabel("position y [µm]")
        self.axis_main.set_facecolor(rc["color_invalid"])

        # selection rectangle
        self.select_rect = mpatches.Rectangle(
            (0.1, 0.1), 200, 200, ec="red", fc="none",
            transform=self.axis_main.transData)
        self.axis_main.add_patch(self.select_rect)

        # color bar
        divider = make_axes_locatable(self.axis_main)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        acbar = pyplot.colorbar(self.plot, cax=cax, label="Data")
        acbar.ax.yaxis.set_ticks_position("right")
        acbar.ax.yaxis.set_label_position("right")
        self.colorbar = acbar

        self.lines = []

        # mouse click event
        self.click_callback = None
        self.canvas.mpl_connect('button_press_event', self.on_click)

        # adjust suplot parameters left,bottom,right,top
        self.figure.subplots_adjust(0.2, 0.2, 0.8, 0.95)
        self.canvas.draw()

    def add_toolbar(self, widget):
        """Add mpl toolbar"""
        self.toolbar = custom_widgets.NavigationToolbarQMap(
            self.canvas,
            widget,
            coordinates=True
        )
        self.toolbar.save_data_callback = self.save_data_callback
        self.reset()

    def connect_curve_selection_event(self, callback):
        """Connect mouse click event with callback

        The callback method should accept an index as argument that
        enumerates `self.data_coords`.
        """
        self.click_callback = callback

    def on_click(self, event):
        if (self.click_callback is not None and
            self.qmap_coords is not None and
                event.inaxes is self.axis_main):
            idx = self.set_selection_by_coord(x=event.xdata, y=event.ydata)
            self.click_callback(idx)
        else:
            self.select_rect.set_visible(False)
            self.canvas.draw()

    def reset(self):
        self.colorbar.ax.set_visible(False)
        self.toolbar.setVisible(False)
        self.plot.axes.set_visible(False)
        self.no_data_text.set_visible(True)
        self.qmap = None
        self.qmap_coords = None
        self.qmap_data = None
        self.qmap_shape = (np.nan, np.nan)
        self.dx = 1
        self.dy = 1
        self.reset_lines()

    def reset_lines(self):
        for _ in range(len(self.lines)):
            self.lines.pop(0).remove()

    def save_data_callback(self, filename):
        """Save current image as tsv"""
        with io.open(filename, "wb") as fd:
            np.savetxt(fd, self.qmap_data, delimiter="\t")

    def set_selection_by_coord(self, x, y):
        """Set the position of the red selection frame with coordinates

        Parameters
        ----------
        x,y: float
            The coordinates of the selection. These values do not
            have to be exact.

        Returns
        -------
        index: int
            Index in self.qmap_coords corresponding to the
            selection.

        Notes
        -----
        If the index matches the currently displayed index, then
        the visibility of the selection rectangle patch is toggled.

        See Also
        --------
        set_selection_by_index: Use index instead of coords
        """
        if self.qmap_coords is not None:
            cx = self.qmap_coords[:, 0]
            cy = self.qmap_coords[:, 1]
            index = np.argmin((cx-x)**2 + (cy-y)**2)
            self.set_selection_by_index(index=index)
            return index
        else:
            return None

    def set_selection_by_index(self, index):
        """Set the position of the red selection frame with index

        Parameters
        ----------
        index: int
            Index in self.qmap_coords corresponding to the
            selection.

        Notes
        -----
        If the index matches the currently displayed index, then
        the visibility of the selection rectangle patch is toggled.

        See Also
        --------
        set_selection_by_coord: Use coordinates instead of index
        """
        if self.qmap_coords is not None:
            cx = self.qmap_coords[:, 0]
            cy = self.qmap_coords[:, 1]
            newxy = (cx[index]-self.dx/2, cy[index]-self.dy/2)
            self.select_rect.set_xy(newxy)
            self.show_selection(True)

    def show_selection(self, b):
        self.select_rect.set_visible(b)
        if b:
            self.select_rect.set_width(self.dx)
            self.select_rect.set_height(self.dy)
        self.canvas.draw()

    def update(self, qmap, feature, cmap="viridis", vmin=None, vmax=None):
        """Update the map tab plot data

        Parameters
        ----------
        qmap: nanite.QMap
            Qmap data
        vmin, vmax: float
            Data range for plotting
        label: str
            QMap colorbar data label

        Notes
        -----
        If `coords` or `qmap_data` is set to none, then a message will
        be displayed in the plot stating that no map data is available.
        """
        prev_data = self.qmap_data

        qmap_data = qmap.get_qmap(feature=feature, qmap_only=True)
        qmap_coords = qmap.get_coords(which="um")
        qmap_coords_px = qmap.get_coords(which="px")
        shape = qmap_data.shape
        extent = qmap.extent
        dx = (extent[1] - extent[0])/shape[0]
        dy = (extent[3] - extent[2])/shape[1]

        # TODO:
        # - only update the plot if vmin/vmax or qmap_data as changed

        if vmin == vmax:
            vmin = vmax = None

        if vmin is None:
            vmin = np.nanmin(qmap_data)
        if vmax is None:
            vmax = np.nanmax(qmap_data)
        self.plot.set_clim(vmin=vmin, vmax=vmax)

        self.plot.set_cmap(cmap)

        # explicitly set x/y limits
        self.axis_main.set_xlim(extent[0], extent[1])
        self.axis_main.set_ylim(extent[2], extent[3])

        if (prev_data is None
                or not np.allclose(qmap_data, prev_data, equal_nan=True)):
            # visibility of plot elements
            self.colorbar.ax.set_visible(True)
            self.toolbar.setVisible(True)
            self.plot.axes.set_visible(True)
            self.no_data_text.set_visible(False)

            # set plot data
            self.plot.set_data(qmap_data)
            self.plot.set_extent(extent)
            self.colorbar.set_label(feature)

            # set invalid elements
            self.reset_lines()
            xm, ym = np.meshgrid(range(shape[0]),
                                 range(shape[1]))

            for xi, yi in zip(xm.flat, ym.flat):
                if np.isnan(qmap_data[yi, xi]):
                    xv = extent[0] + (xi+.5) * dx
                    yv = extent[2] + (yi+.5) * dy
                    for p in qmap_coords_px:
                        if np.allclose([xi, yi], p):
                            # data available, but not computed
                            color = "#14571A"  # green
                            break
                    else:
                        # curve not available
                        color = "#571714"  # red
                    self.lines.append(
                        self.axis_main.plot([xv-dx*.4, xv+dx*.4],
                                            [yv-dy*.4, yv+dy*.4],
                                            color=color,
                                            lw=1)[0]
                    )

            # common variables
            self.dx = dx
            self.dy = dy
            self.qmap = qmap
            self.qmap_coords = qmap_coords
            self.qmap_data = qmap_data

        self.canvas.draw()
