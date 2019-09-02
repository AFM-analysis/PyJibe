import pkg_resources

import nanite
from PyQt5 import uic, QtWidgets

from .mpl_qmap import MPLQMap


class TabQMap(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabQMap, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_qmap.ui")
        uic.loadUi(path_ui, self)

        # Setup the matplotlib interface for 2D map plotting
        self.mpl_qmap = MPLQMap()
        self.mpl_qmap.add_toolbar(self.qmap_mplwidget)
        self.qmap_mpllayout.addWidget(self.mpl_qmap.canvas)
        self.qmap_mpllayout.addWidget(self.mpl_qmap.toolbar)
        # set colormaps
        cmaps = ["viridis", "plasma", "afmhot", "seismic"]
        for cm in cmaps:
            self.qmpa_cmap_cb.addItem(cm)
        self.qmpa_cmap_cb.setCurrentIndex(0)
        self.qmap_data_cb.currentIndexChanged.connect(
            self.on_qmap_data_changed)
        self.qmpa_cmap_cb.currentIndexChanged.connect(
            self.on_qmap_cmap_changed)
        self.qmap_sp_range1.valueChanged.connect(self.on_qmap_min_max_changed)
        self.qmap_sp_range2.valueChanged.connect(self.on_qmap_min_max_changed)
        self.mpl_qmap.connect_curve_selection_event(self.on_qmap_selection)

    def on_qmap_cmap_changed(self):
        """colormap selection changed"""
        self.update_qmap()

    def on_qmap_data_changed(self):
        """data column selection changed"""
        # set previous spin control values if existent
        self.qmap_sp_range1.blockSignals(True)
        self.qmap_sp_range2.blockSignals(True)
        if hasattr(self, "_cache_qmap_spin_ctl"):
            data = self.qmap_data_cb.currentIndex()
            if data in self._cache_qmap_spin_ctl:
                vmin, vmax = self._cache_qmap_spin_ctl[data]
            else:
                vmin = vmax = 0
            self.qmap_sp_range1.setValue(vmin)
            self.qmap_sp_range2.setValue(vmax)
        self.qmap_sp_range1.blockSignals(False)
        self.qmap_sp_range2.blockSignals(False)
        self.update_qmap()

    def on_qmap_min_max_changed(self):
        """min or max spin controls changed"""
        # store spin control values for data column
        vmin = self.qmap_sp_range1.value()
        vmax = self.qmap_sp_range2.value()
        data = self.qmap_data_cb.currentIndex()
        if not hasattr(self, "_cache_qmap_spin_ctl"):
            self._cache_qmap_spin_ctl = {}
        self._cache_qmap_spin_ctl[data] = (vmin, vmax)
        self.update_qmap()

    def on_qmap_selection(self, idx):
        """Show the curve indexed in the current qmap"""
        # Perform operations on ForceDistance
        fd = self.parent().parent().parent().parent()
        # Get the qmap name
        cc = fd.current_curve
        # idx is `enum` and curves are sorted
        curves = [ci for ci in fd.data_set if ci.path == cc.path]
        fdist = curves[idx]
        idcurve = fd.data_set.index(fdist)
        item = fd.list_curves.topLevelItem(idcurve)
        fd.list_curves.setCurrentItem(item)

    def update_qmap(self, fdist_map, index):
        # Build list of possible selections
        selist = nanite.qmap.available_features

        # Get plotting parameter and check if it makes sense
        feature = self.qmap_data_cb.currentText()
        if not feature or feature not in selist:
            # Use a default plotting map
            feature = "data min height"

        # Make sure that we have a valid property to plot
        assert feature in selist

        # Update dropdown menu with possible selections
        # disable signals while updating the combobox
        self.qmap_data_cb.blockSignals(True)
        # remove all items
        for _i in range(self.qmap_data_cb.count()):
            self.qmap_data_cb.removeItem(0)
        # add new items
        for item in selist:
            self.qmap_data_cb.addItem(item)
        self.qmap_data_cb.setCurrentIndex(selist.index(feature))
        self.qmap_data_cb.blockSignals(False)

        if len(fdist_map) > 1:
            # Get map data
            qmap = nanite.QMap(fdist_map)
            # update plot
            self.mpl_qmap.update(qmap=qmap,
                                 feature=feature,
                                 cmap=self.qmpa_cmap_cb.currentText(),
                                 vmin=self.qmap_sp_range1.value(),
                                 vmax=self.qmap_sp_range2.value())
            self.mpl_qmap.set_selection_by_index(index)
        else:
            self.mpl_qmap.reset()
