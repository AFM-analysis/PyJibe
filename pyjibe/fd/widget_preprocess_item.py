import pkg_resources

from nanite.preproc import IndentationPreprocessor
from PyQt5 import QtCore, QtWidgets, uic


class WidgetPreprocessItem(QtWidgets.QWidget):
    #: Pass-through for stateChanged of self.CheckBox
    stateChanged = QtCore.pyqtSignal(int)

    def __init__(self, identifier, *args, **kwargs):
        """Special widget for preprocessing options"""
        super(WidgetPreprocessItem, self).__init__(*args, **kwargs)

        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "widget_preprocess_item.ui")
        uic.loadUi(path_ui, self)

        # set label text
        name = IndentationPreprocessor.get_name(identifier)
        self.label.setText(name)

        self.identifier = identifier

        # set tooltip
        meth = IndentationPreprocessor.get_func(identifier)
        self.setToolTip(meth.__doc__)

        # set options
        if meth.options is not None:
            for opt in meth.options:
                choices = opt.get("choices", [])
                choices_hr = opt.get("choices_human_readable", choices)
                for text, data in zip(choices_hr, choices):
                    self.comboBox.addItem(text, data)
        else:
            self.comboBox.hide()

        # initially set-up enabled/disabled
        self.update_enabled()

        # signal: passthrough stateChanged
        self.checkBox.stateChanged.connect(self.stateChanged)
        # signal: enable/disable widget area
        self.checkBox.stateChanged.connect(self.update_enabled)

    def get_options(self):
        """Return preprocessing options"""
        popts = {}
        if self.comboBox.isEnabled() and not self.comboBox.isHidden():
            meth = IndentationPreprocessor.get_func(self.identifier)
            if meth.options is not None:
                for opt in meth.options:
                    if "choices" in opt:
                        popts[opt["name"]] = self.comboBox.currentData()
        return popts

    def isChecked(self):
        return self.checkBox.isChecked()

    def setChecked(self, *args, **kwargs):
        self.checkBox.setChecked(*args, **kwargs)

    @QtCore.pyqtSlot()
    def update_enabled(self):
        if self.isChecked():
            self.widget.setEnabled(True)
        else:
            self.widget.setEnabled(False)
