"""Widget containing preprocessing plot"""
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
        elif "correct_tip_offset" in details:
            meth = details["correct_tip_offset"]
            self.mpl_curve.clear()
            self.mpl_curve.axis.set_title(meth["method"])
            for key in meth:
                if key.startswith("plot "):
                    self.mpl_curve.axis.plot(*meth[key], label=key[5:])
            self.mpl_curve.axis.legend()
        self.mpl_curve.canvas.draw()
