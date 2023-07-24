"""Widget containing preprocessing plot"""
from nanite import preproc
from PyQt5 import QtWidgets

from .mpl_preproc import MPLPreproc


class WidgetPlotPreproc(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        """Display preprocessing graph with navigation"""
        super(WidgetPlotPreproc, self).__init__(*args, **kwargs)

        self.mplvl = QtWidgets.QVBoxLayout(self)
        # Setup the matplotlib interface for approach retract plotting
        self.mpl_curve = MPLPreproc()
        self.mpl_curve.add_toolbar(self)
        self.mplvl.addWidget(self.mpl_curve.canvas)
        self.mplvl.addWidget(self.mpl_curve.toolbar)

    @property
    def fd(self):
        return self.parent().parent().parent()

    def update_details(self, details):
        """Update UI with details"""
        self.mpl_curve.clear()
        if details is None:
            return
        self.mpl_curve.axis.set_title("Curve correction insights")
        for det in ["correct_tip_offset", "correct_force_slope"]:
            name = preproc.get_name(det)
            if det in details:
                meth = details[det]
                axis = self.mpl_curve.get_normed_axis(meth["norm"])
                for key in meth:
                    if key.startswith("plot "):
                        axis.plot(*meth[key], label=f"{key[5:]} ({name})")
        self.mpl_curve.legend()
        self.mpl_curve.canvas.draw()
