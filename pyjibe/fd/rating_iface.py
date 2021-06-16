import os
import pathlib
import pkg_resources

from nanite.rate import io as nio
from PyQt5 import uic, QtCore, QtWidgets


# load QWidget from ui file
ui_path = pkg_resources.resource_filename("pyjibe.fd",
                                          "rating_iface.ui")
UiUserRatingBase = uic.loadUiType(ui_path)[0]


class Rater(QtWidgets.QWidget, UiUserRatingBase):
    def __init__(self, fdui, path):
        QtWidgets.QWidget.__init__(self, None)
        UiUserRatingBase.__init__(self)
        self.setupUi(self)
        self.fdui = fdui
        path = pathlib.Path(path)
        if not path.suffix == ".h5":
            path = path.with_name(path.name + ".h5")
        self.path = path

        self.initial_stuff()

        # signals
        self.curve_index.valueChanged.connect(self.on_change_index)
        self.sp_rating.valueChanged.connect(self.on_change_values)
        self.text_comment.textChanged.connect(self.on_change_values)

        self.on_change_index()  # load first dataset if applicable

    def initial_stuff(self):
        # set container path
        self.container_path.setText(str(self.path))
        # set user name
        for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
            if name in os.environ:
                user = os.environ[name]
                break
        else:
            user = "unknown"
        self.user_name.setText(user)
        # set correct initial index
        item = self.fdui.list_curves.currentItem()
        idx = self.fdui.list_curves.indexOfTopLevelItem(item)
        self.curve_index.setValue(idx+1)
        self.curve_index.setMaximum(len(self.fdui.data_set))

    @QtCore.pyqtSlot()
    def on_change_index(self):
        self.curve_index.blockSignals(True)
        self.sp_rating.blockSignals(True)
        self.text_comment.blockSignals(True)

        index = self.curve_index.value()-1
        fdist = self.fdui.data_set[index]
        _, rating, comment = nio.hdf5_rated(self.path, fdist)
        self.sp_rating.setValue(rating)
        self.text_comment.setPlainText(comment)
        it = self.fdui.list_curves.topLevelItem(index)
        self.fdui.list_curves.setCurrentItem(it)
        self.sp_rating.selectAll()
        self.sp_rating.setFocus()

        self.curve_index.blockSignals(False)
        self.sp_rating.blockSignals(False)
        self.text_comment.blockSignals(False)

    @QtCore.pyqtSlot()
    def on_change_values(self):
        index = self.curve_index.value()-1
        fdist = self.fdui.data_set[index]
        nio.save_hdf5(h5path=self.path,
                      indent=fdist,
                      user_rate=self.sp_rating.value(),
                      user_name=self.user_name.text(),
                      user_comment=self.text_comment.toPlainText())
