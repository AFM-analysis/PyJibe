"""Widget containing force-distance plot"""
from PyQt5 import QtWidgets

from .mpl_indent import MPLIndentation


class WidgetFDist(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        """Display force-indentation graph with navigation"""
        super(WidgetFDist, self).__init__(*args, **kwargs)

        self.mplvl = QtWidgets.QVBoxLayout(self)
        # Setup the matplotlib interface for approach retract plotting
        self.mpl_curve = MPLIndentation()
        self.mpl_curve.add_toolbar(self)
        self.mplvl.addWidget(self.mpl_curve.canvas)
        self.mplvl.addWidget(self.mpl_curve.toolbar)

    @property
    def fd(self):
        return self.parent().parent()

    def mpl_curve_update(self, fdist):
        """Update the force-indentation curve"""
        autoscale_x = self.fd.cb_mpl_rescale_plot_x.checkState() == 2
        autoscale_y = self.fd.cb_mpl_rescale_plot_y.checkState() == 2
        if autoscale_x:
            rescale_x = None
        else:
            rescale_x = (self.fd.cb_mpl_rescale_plot_x_min.value(),
                         self.fd.cb_mpl_rescale_plot_x_max.value())

        if autoscale_y:
            rescale_y = None
        else:
            rescale_y = (self.fd.cb_mpl_rescale_plot_y_min.value(),
                         self.fd.cb_mpl_rescale_plot_y_max.value())

        self.mpl_curve.update(fdist,
                              rescale_x=rescale_x,
                              rescale_y=rescale_y)
