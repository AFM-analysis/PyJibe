import os
import pkg_resources

from nanite.rate import io as nio
from PyQt5 import uic, QtWidgets


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
        self.path = path

        self.initial_stuff()
        self.setup_signals()
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

    def setup_signals(self, enable=True):
        cn = [
            # Change of index updates apc
            [self.curve_index.valueChanged, self.on_change_index],
            [self.sp_rating.valueChanged, self.on_change_values],
            [self.text_comment.textChanged, self.on_change_values],
        ]

        for signal, slot in cn:
            if enable:
                signal.connect(slot)
            else:
                signal.disconnect(slot)

    def on_change_index(self):
        index = self.curve_index.value()-1
        self.setup_signals(False)
        fdist = self.fdui.data_set[index]
        _, rating, comment = nio.hdf5_rated(self.path, fdist)
        self.sp_rating.setValue(rating)
        self.text_comment.setPlainText(comment)
        self.setup_signals(True)
        it = self.fdui.list_curves.topLevelItem(index)
        self.fdui.list_curves.setCurrentItem(it)
        self.sp_rating.selectAll()
        self.sp_rating.setFocus()

    def on_change_values(self):
        index = self.curve_index.value()-1
        fdist = self.fdui.data_set[index]
        nio.save_hdf5(h5path=self.path,
                      indent=fdist,
                      user_rate=self.sp_rating.value(),
                      user_name=self.user_name.text(),
                      user_comment=self.text_comment.toPlainText())
