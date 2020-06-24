import pkg_resources

import nanite.preproc as npreproc
from PyQt5 import uic, QtWidgets


class TabPreprocess(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabPreprocess, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_preprocess.ui")
        uic.loadUi(path_ui, self)

        # Setup everything necessary for the preprocessing tab:
        # Get list of preprocessing methods
        premem = npreproc.IndentationPreprocessor.available()

        for p in premem:
            item = QtWidgets.QListWidgetItem()
            item.setText(p)
            self.list_preproc_available.addItem(item)

        self.list_preproc_available.currentItemChanged.connect(
            lambda: self.update_displayed_docstring("available"))
        self.list_preproc_applied.currentItemChanged.connect(
            lambda: self.update_displayed_docstring("applied"))

        # Add recommended item (see `self.preproc_set_preset`)
        self.cb_preproc_presel.addItem("Recommended")
        self.cb_preproc_presel.activated.connect(self.on_preset_changed)
        self.cb_preproc_presel.currentIndexChanged.connect(
            self.on_preset_changed)
        # Apply recommended defaults
        self.cb_preproc_presel.setCurrentIndex(1)

    def fit_apply_preprocessing(self, fdist):
        """Apply the preprocessing steps if required"""
        # Note: Preprocessing is cached once in `fdist`.
        # Thus calling this method a second time without any
        # change in the GUI is free.
        num = self.list_preproc_applied.count()
        preprocessing = []
        for ii in range(num):
            item = self.list_preproc_applied.item(ii)
            preprocessing.append(item.text())
        # Perform preprocessing
        fdist.apply_preprocessing(preprocessing)

    def on_preset_changed(self):
        """Update preselection"""
        text = self.cb_preproc_presel.currentText()
        self.list_preproc_applied.clear()
        if text == "None":
            pass
        elif text == "Recommended":
            recommended_methods = ["compute_tip_position",
                                   "correct_force_offset",
                                   "correct_tip_offset",
                                   "correct_split_approach_retract"]
            for m in recommended_methods:
                item = QtWidgets.QListWidgetItem()
                item.setText(m)
                self.list_preproc_applied.addItem(item)

    def update_displayed_docstring(self, source):
        """Update the description box with the method doc string

        Writes text to `self.text_preprocessing` according to the
        method selected in `self.list_preproc_available` or
        `self.list_preproc_applied`.
        """
        if source == "available":
            thelist = self.list_preproc_available
        elif source == "applied":
            thelist = self.list_preproc_applied
        item = thelist.currentItem()
        if item is None:
            return
        method_name = item.text()
        method = getattr(npreproc.IndentationPreprocessor, method_name)
        doc = method.__doc__.replace("    ", "").strip()
        self.text_preprocessing.setPlainText(doc)
