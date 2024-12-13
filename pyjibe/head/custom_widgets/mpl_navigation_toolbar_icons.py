import os
import importlib.resources

from PyQt6 import QtCore, QtGui, QtWidgets

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
from matplotlib import cbook

# TODO:
# - use the capabilities of the new toolbars?


class NavigationToolbarCustom(NavigationToolbar2QT):
    """A custom toolbar that allows other icons"""

    def __init__(self, *args, **kwargs):
        super(NavigationToolbarCustom, self).__init__(*args, **kwargs)

    def _icon(self, name, color=None):
        """Override matplotlibs `_icon` function to get custom icons"""
        name = name.replace('.png', '_large.png')
        impath = cbook._get_data_path('images', name)
        pm = None  # Initialize pm to None
        if os.path.exists(impath):
            pm = QtGui.QPixmap(str(impath))
        else:
            ref = importlib.resources.files("pyjibe.img") / name
            with importlib.resources.as_file(ref) as ref_path:
                pm = QtGui.QPixmap(str(ref_path))
        if pm is None or pm.isNull():
            raise ValueError(f"Could not find image '{name}'")
        pm.setDevicePixelRatio(self.devicePixelRatioF() or 1)
        if self.palette().color(self.backgroundRole()).value() < 128:
            icon_color = self.palette().color(self.foregroundRole())
            mask = pm.createMaskFromColor(QtGui.QColor('black'),
                                          QtCore.Qt.MaskMode.MaskOutColor)
            pm.fill(icon_color)
            pm.setMask(mask)
        return QtGui.QIcon(pm)

    def save_data(self, *args):
        fname, _e = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save raw data", "", "Tab Separated Values (*.tab)")
        if fname:
            if not fname.endswith(".tab"):
                fname += ".tab"
            self.save_data_callback(fname)

    def save_data_callback(self, filename):
        """Save the plot data to a tab file
        """
        raise ValueError("This Method must be overridden!")


class NavigationToolbarIndent(NavigationToolbarCustom):
    def __init__(self, *args, **kwargs):
        self.toolitems = (
            ('Home', 'Reset plot', 'home', 'home'),
            ('Pan', 'Pan tool', 'move', 'pan'),
            ('Zoom', 'Zoom tool', 'zoom_to_rect', 'zoom'),
            ('Save', 'Save approach-retract curve image',
             'saveimg', 'save_figure'),
            ('Save', 'Save approach-retract curve data',
             'savedat', 'save_data'),
        )
        super(NavigationToolbarIndent, self).__init__(*args, **kwargs)


class NavigationToolbarEDelta(NavigationToolbarCustom):
    def __init__(self, *args, **kwargs):
        self.toolitems = (
            ('Home', 'Reset plot', 'home', 'home'),
            ('Pan', 'Pan tool', 'move', 'pan'),
            ('Zoom', 'Zoom tool', 'zoom_to_rect', 'zoom'),
            ('Save', 'Save E(δ) curve image', 'saveimg', 'save_figure'),
            ('Save', 'Save E(δ) data', 'savedat', 'save_data'),
        )
        super(NavigationToolbarEDelta, self).__init__(*args, **kwargs)


class NavigationToolbarPreproc(NavigationToolbarCustom):
    def __init__(self, *args, **kwargs):
        self.toolitems = (
            ('Home', 'Reset plot', 'home', 'home'),
            ('Pan', 'Pan tool', 'move', 'pan'),
            ('Zoom', 'Zoom tool', 'zoom_to_rect', 'zoom'),
        )
        super(NavigationToolbarPreproc, self).__init__(*args, **kwargs)


class NavigationToolbarQMap(NavigationToolbarCustom):
    def __init__(self, *args, **kwargs):
        self.toolitems = (
            ('Home', 'Reset plot', 'home', 'home'),
            ('Pan', 'Pan tool', 'move', 'pan'),
            ('Zoom', 'Zoom tool', 'zoom_to_rect', 'zoom'),
            ('Save', 'Save quantitative map image', 'saveimg', 'save_figure'),
            ('Save', 'Save quantitative map data', 'savedat', 'save_data'),
        )
        super(NavigationToolbarQMap, self).__init__(*args, **kwargs)
