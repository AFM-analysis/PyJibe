import os.path as os_path
import pkg_resources
import traceback

import nanite
from PyQt5 import uic, QtCore, QtWidgets
from PyQt5.QtCore import QStandardPaths

from ..extensions import ExtensionManager, SUPPORTED_FORMATS


class ExtensionErrorWrapper:
    def __init__(self, ehash):
        self.ehash = ehash

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, trc):
        if exc_type is not None:
            QtWidgets.QMessageBox.warning(
                None,
                f"Loading extension {self.ehash} failed!",
                f"It was not possible to load the extension {self.ehash}! "
                + "You might have to install additional software:\n\n"
                + traceback.format_exc(),
                )
            return True  # do not raise the exception


class Preferences(QtWidgets.QDialog):
    """Implements the plotting pipeline using pyqtgraph"""
    instances = {}
    feature_changed = QtCore.pyqtSignal()

    def __init__(self, parent, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, parent=parent, *args, **kwargs)
        path_ui = pkg_resources.resource_filename(
            "pyjibe.head", "preferences.ui")
        uic.loadUi(path_ui, self)
        self.settings = QtCore.QSettings()
        self.parent = parent

        #: configuration keys, corresponding widgets, and defaults
        self.config_pairs = [
            ["advanced/developer mode", self.advanced_developer_mode, 0],
            ["advanced/expert mode", self.advanced_expert_mode, 0],
            ["check for updates", self.general_check_for_updates, 1],
        ]

        # extensions
        store_path = os_path.join(
            QStandardPaths.writableLocation(
                QStandardPaths.AppDataLocation), "extensions")
        self.extensions = ExtensionManager(store_path)

        self.reload()

        # signals
        self.btn_apply = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Apply)
        self.btn_apply.clicked.connect(self.on_settings_apply)
        self.btn_cancel = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Cancel)
        self.btn_ok = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.btn_ok.clicked.connect(self.on_settings_apply)
        self.btn_restore = self.buttonBox.button(
            QtWidgets.QDialogButtonBox.RestoreDefaults)
        self.btn_restore.clicked.connect(self.on_settings_restore)
        # extension buttons
        self.checkBox_ext_enabled.clicked.connect(self.on_ext_enabled)
        self.pushButton_ext_load.clicked.connect(self.on_ext_load)
        self.pushButton_ext_remove.clicked.connect(self.on_ext_remove)
        self.listWidget_ext.currentRowChanged.connect(self.on_ext_selected)
        self.listWidget_ext.itemChanged.connect(self.on_ext_modified)
        # tab changed
        self.tabWidget.currentChanged.connect(self.on_tab_changed)

    def reload(self):
        """Read configuration or set default parameters"""
        for key, widget, default in self.config_pairs:
            value = self.settings.value(key, default)
            if isinstance(widget, QtWidgets.QCheckBox):
                widget.setChecked(bool(int(value)))
            elif isinstance(widget, QtWidgets.QLineEdit):
                widget.setText(value)
            elif widget is self.dcor_servers:
                self.dcor_servers.clear()
                self.dcor_servers.addItems(value)
                self.dcor_servers.setCurrentIndex(0)
            else:
                raise NotImplementedError("No rule for '{}'".format(key))

        # peculiarities of developer mode
        devmode = bool(int(self.settings.value("advanced/developer mode", 0)))
        if devmode:
            nanite.read.DEFAULT_MODALITY = None
        else:
            nanite.read.DEFAULT_MODALITY = "force-distance"

        self.reload_ext()

    def reload_ext(self):
        """Reload the list of extensions"""
        # extensions
        row = self.listWidget_ext.currentRow()
        self.listWidget_ext.blockSignals(True)
        self.listWidget_ext.clear()
        have_extensions = bool(self.extensions)
        self.widget_ext_controls.setVisible(have_extensions)
        if have_extensions:
            for ii, ext in enumerate(self.extensions):
                lwitem = QtWidgets.QListWidgetItem(ext.title,
                                                   self.listWidget_ext)
                lwitem.setFlags(QtCore.Qt.ItemIsEditable
                                | QtCore.Qt.ItemIsSelectable
                                | QtCore.Qt.ItemIsEnabled
                                | QtCore.Qt.ItemIsUserCheckable)
                lwitem.setCheckState(2 if ext.enabled else 0)
                lwitem.setData(100, ext.hash)
            self.listWidget_ext.setCurrentRow(0)
            if row + 1 > self.listWidget_ext.count() or row < 0:
                row = 0
            self.listWidget_ext.setCurrentRow(row)
        self.listWidget_ext.blockSignals(False)
        self.on_ext_selected()

    @QtCore.pyqtSlot(bool)
    def on_ext_enabled(self, enabled):
        """Enable or disable an extension (signal from checkbox widget)"""
        item = self.listWidget_ext.currentItem()
        ehash = item.data(100)
        with ExtensionErrorWrapper(ehash):
            self.extensions.extension_set_enabled(ehash, enabled)
        self.reload_ext()
        self.feature_changed.emit()

    @QtCore.pyqtSlot()
    def on_ext_load(self):
        """Load an extension from the file system"""
        format_string = " ".join(f"*{su}" for su in SUPPORTED_FORMATS)
        paths, _ = QtWidgets.QFileDialog.getOpenFileNames(
            parent=self,
            caption="Select an extension file",
            directory=self.settings.value("paths/extension", ""),
            filter=f"Supported extension files ({format_string})")
        if paths:
            for pp in paths:
                with ExtensionErrorWrapper(pp):
                    self.extensions.import_extension_from_path(pp)
            self.reload_ext()
            self.feature_changed.emit()

    @QtCore.pyqtSlot()
    def on_ext_remove(self):
        """Remove an extension"""
        ehash = self.listWidget_ext.currentItem().data(100)
        self.extensions.extension_remove(ehash)
        self.reload_ext()
        self.feature_changed.emit()

    @QtCore.pyqtSlot(QtWidgets.QListWidgetItem)
    def on_ext_modified(self, item):
        """Enable or disable an extension (signal from listWidget)"""
        ehash = item.data(100)
        enabled = bool(item.checkState())
        with ExtensionErrorWrapper(ehash):
            self.extensions.extension_set_enabled(ehash, enabled)
        self.listWidget_ext.setCurrentItem(item)
        self.reload_ext()
        self.feature_changed.emit()

    @QtCore.pyqtSlot()
    def on_ext_selected(self):
        """Display details for an extension (signal from listWidget)"""
        item = self.listWidget_ext.currentItem()
        if item is not None:
            ehash = item.data(100)
            ext = self.extensions[ehash]
            self.checkBox_ext_enabled.blockSignals(True)
            self.checkBox_ext_enabled.setChecked(ext.enabled)
            self.checkBox_ext_enabled.blockSignals(False)
            with ExtensionErrorWrapper(ehash):
                if ext.enabled:  # only load the extension if enabled
                    ext.load()
            self.label_ext_name.setText(ext.title)
            item.setText(ext.title)
            self.label_ext_description.setText(ext.description)

    @QtCore.pyqtSlot()
    def on_settings_apply(self):
        """Save current changes made in UI to settings and reload UI"""
        for key, widget, default in self.config_pairs:
            if isinstance(widget, QtWidgets.QCheckBox):
                value = int(widget.isChecked())
                if key == "advanced/developer mode":
                    devmode = int(self.settings.value(
                        "advanced/developer mode", 0))
                    if devmode != value:
                        msg = QtWidgets.QMessageBox()
                        msg.setIcon(QtWidgets.QMessageBox.Information)
                        msg.setText("Please restart PyJibe for the changes "
                                    + "to take effect.")
                        msg.setWindowTitle("Restart PyJibe")
                        msg.exec_()
            elif isinstance(widget, QtWidgets.QLineEdit):
                value = widget.text().strip()
            elif widget is self.dcor_servers:
                curtext = self.dcor_servers.currentText()
                items = self.settings.value(key, default)
                if curtext in items:
                    items.remove(curtext)
                items.insert(0, curtext)
                value = items
            else:
                raise NotImplementedError("No rule for '{}'".format(key))
            self.settings.setValue(key, value)

        # reload UI to give visual feedback
        self.reload()

    @QtCore.pyqtSlot()
    def on_settings_restore(self):
        self.settings.clear()
        self.reload()

    @QtCore.pyqtSlot()
    def on_tab_changed(self):
        if self.tabWidget.currentWidget() is self.tab_extensions:
            # Managing extensions has nothing to do with other settings.
            enabled = False
        else:
            enabled = True

        self.btn_apply.setEnabled(enabled)
        self.btn_cancel.setEnabled(enabled)
        self.btn_restore.setEnabled(enabled)
