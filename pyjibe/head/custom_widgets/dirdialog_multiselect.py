import pathlib

from PyQt5 import QtCore, QtWidgets


class DirectoryDialogMultiSelect(QtWidgets.QFileDialog):
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

        # Add common directories in the sidebar
        sidebar_urls = self.sidebarUrls()
        for path in ["/Volumes", "/media", "/mnt", "/"]:
            if pathlib.Path(path).exists():
                sidebar_urls.append(QtCore.QUrl('file://' + path))
        self.setSidebarUrls(sorted(set(sidebar_urls)))

    def getDirectory(self):
        """Return a string of the root directory"""
        files = self.selectedFiles()
        if files:
            return str(pathlib.Path(files[0]).parent)
        else:
            return None
