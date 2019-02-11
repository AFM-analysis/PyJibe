import os
import pathlib
import pkg_resources

from PyQt5 import QtWidgets, QtGui

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT


class FileDialog(QtWidgets.QFileDialog):
    def __init__(self, *args):
        """A dialog that lets the user select multiple directories"""
        QtWidgets.QFileDialog.__init__(self, *args)
        self.setOption(self.DontUseNativeDialog, True)
        self.setFileMode(self.DirectoryOnly)

        self.tree = self.findChild(QtWidgets.QTreeView)
        self.tree.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        self.list = self.findChild(QtWidgets.QListView)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.MultiSelection)

        for view in self.findChildren((QtWidgets.QListView,
                                       QtWidgets.QTreeView)):
            if isinstance(view.model(), QtWidgets.QFileSystemModel):
                view.setSelectionMode(
                    QtWidgets.QAbstractItemView.MultiSelection)

    def getDirectory(self):
        dirs = self.selectedFiles()
        if dirs:
            path = pathlib.Path(dirs[0])
            if len(dirs) > 1:
                path = path.parent
        return str(path)

    def selectedFilesRecursive(self):
        dirs = self.selectedFiles()
        files = []
        for d in dirs:
            for rt, _d, fs in os.walk(d):
                for f in fs:
                    files.append(os.path.join(rt, f))
        return files


# TODO:
# - upgrade matplotlib to something other than 1.5.1 and
#   use the capabilities of the new toolbars.

class NavigationToolbarCustom(NavigationToolbar2QT):
    """A custom toolbar that allows other icons"""

    def __init__(self, *args, **kwargs):
        super(NavigationToolbarCustom, self).__init__(*args, **kwargs)

    def _icon(self, name):
        """Override matplotlibs `_icon` function to get custom icons"""
        # PyQt5 supports large images
        name = name.replace('.png', '_large.png')
        impath = os.path.join(self.basedir, name)
        if not os.path.exists(impath):
            imdir = pkg_resources.resource_filename("pyjibe", "img")
            impath = os.path.join(imdir, name)
        pm = QtGui.QPixmap(impath)
        pm.setDevicePixelRatio(self.canvas._dpi_ratio)
        return QtGui.QIcon(pm)

    def save_data(self, *args):
        fname, _e = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save raw data", "", "Tab Separated Values (*.tsv)")
        if fname:
            if not fname.endswith(".tsv"):
                fname += ".tsv"
            self.save_data_callback(fname)

    def save_data_callback(self, filename):
        """Save the plot data to a tsv file
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
