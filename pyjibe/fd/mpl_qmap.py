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
        cmap = mpl.cm.get_cmap(rc["color_map"])
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
        self.qmap_data = np.nan
        self.qmap_coords = None
        self.qmap_shape = (np.nan, np.nan)
        self.dx = 1
        self.dy = 1

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
            self.select_rect.set_visible(True)
            self.select_rect.set_xy(newxy)
            self.select_rect.set_width(self.dx)
            self.select_rect.set_height(self.dy)
            self.canvas.draw()

    def update(self, qmap_data, coords_um, extent,
               cmap="viridis", vmin=None, vmax=None, label=None):
        """Update the map tab plot data

        Parameters
        ----------
        coords_um: list-like (length N) with tuple of floats
            The x- and y-coordinates [µm]
        qmap_data: list-like (length N)
            The data to be mapped.
        vmin, vmax: float
            Data range for plotting
        label: str
            QMap colorbar data label

        Notes
        -----
        If `coords` or `qmap_data` is set to none, then a message will
        be displayed in the plot stating that no map data is available.
        """
        prevmap = self.qmap_data

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

        if qmap_data is not None and not np.all(qmap_data == prevmap):
            self.colorbar.ax.set_visible(True)
            self.toolbar.setVisible(True)
            self.plot.axes.set_visible(True)
            self.no_data_text.set_visible(False)

            shape = qmap_data.shape
            self.dx = (extent[1] - extent[0])/shape[0]
            self.dy = (extent[3] - extent[2])/shape[1]
            self.plot.set_data(qmap_data)
            self.plot.set_extent(extent)

            if label is None:
                label = "Data"
            self.colorbar.set_label(label)

            # Update user-stored variable
            self.qmap_data = qmap_data
            self.qmap_coords = np.array(coords_um)

        self.canvas.draw()
