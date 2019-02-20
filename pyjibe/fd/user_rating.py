import os
import pathlib
import pkg_resources

from nanite.rate import io as nio
from PyQt5 import uic, QtWidgets


# load QWidget from ui file
ui_path = pkg_resources.resource_filename("pyjibe.fd",
                                          "user_rating_design.ui")
UiUserRatingBase = uic.loadUiType(ui_path)[0]


class Rater(QtWidgets.QWidget, UiUserRatingBase):
    def __init__(self, apc, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        UiUserRatingBase.__init__(self)
        self.setupUi(self)
        self.apc = apc

        self.ratings = {}
        self.comments = {}

        self.initial_stuff()
        self.setup_signals()

    def initial_stuff(self):
        # set user name
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            if name in os.environ:
                user = os.environ[name]
                break
        else:
            user = "unknown"
        self.user_name.setText(user)
        # set correct initial index
        item = self.apc.list_curves.currentItem()
        idx = self.apc.list_curves.indexOfTopLevelItem(item)
        self.curve_index.setValue(idx+1)
        self.curve_index.setMaximum(len(self.apc.data_set))

    def setup_signals(self, enable=True):
        cn = [
            # Change of index updates apc
            [self.curve_index.valueChanged, self.on_change_index],
            [self.sp_rating.valueChanged, self.on_change_values],
            [self.text_comment.textChanged, self.on_change_values],
            [self.btn_save.clicked, self.on_save],
        ]

        for signal, slot in cn:
            if enable:
                signal.connect(slot)
            else:
                signal.disconnect(slot)

    def on_change_index(self):
        index = self.curve_index.value()-1
        self.setup_signals(False)
        if index in self.ratings:
            a = self.ratings[index]
            b = self.comments[index]
        else:
            a = -1
            b = ""
        self.sp_rating.setValue(a)
        self.text_comment.setPlainText(b)
        self.setup_signals(True)
        it = self.apc.list_curves.topLevelItem(index)
        self.apc.list_curves.setCurrentItem(it)
        self.sp_rating.selectAll()
        self.sp_rating.setFocus()

    def on_change_values(self):
        index = self.curve_index.value()-1
        self.ratings[index] = self.sp_rating.value()
        self.comments[index] = self.text_comment.toPlainText()

    def on_save(self):
        # Let user select directory
        filen = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save rating information", filter="*.h5")

        h5path = pathlib.Path(filen[0]).with_suffix(".h5")
        if h5path.exists():
            h5path.unlink()

        name = self.user_name.text()

        for ii in list(self.ratings.keys()):
            nio.save_hdf5(h5path=h5path,
                          indent=self.apc.data_set[ii],
                          user_rate=self.ratings[ii],
                          user_name=name,
                          user_comment=self.comments[ii])
