import numpy as np

from PyQt5 import QtWidgets, QtCore


class InfDoubleSlider(QtWidgets.QSlider):
    valueChangedFloat = QtCore.pyqtSignal("double")
    sliderReleasedFloat = QtCore.pyqtSignal("double")

    def __init__(self, *args, **kwargs):
        super(InfDoubleSlider, self).__init__(*args, **kwargs)
        self._max_int = 100000

        super(InfDoubleSlider, self).setMinimum(0)
        super(InfDoubleSlider, self).setMaximum(self._max_int)

        self._min_value = -10
        self._max_value = 10

        self.valueChanged.connect(self.on_value_changed)
        self.sliderReleased.connect(self.on_slider_released)

    @property
    def _value_range(self):
        return self._max_value - self._min_value

    def value(self):
        pos = super(InfDoubleSlider, self).value()
        if pos == 0:
            value = -np.inf
        elif pos == self._max_int:
            value = np.inf
        else:
            # remove 2 because of inf borders
            value = (pos-1) / (self._max_int) * \
                self._value_range + self._min_value
        return value

    def on_slider_released(self):
        """Emits a double signal when `valueChanged["int"]` is emitted"""
        self.sliderReleasedFloat["double"].emit(self.value())

    def on_value_changed(self):
        """Emits a double signal when `valueChanged["int"]` is emitted"""
        self.valueChangedFloat["double"].emit(self.value())

    def setValue(self, value):
        if value == -np.inf:
            pos = 0
        elif value == np.inf:
            pos = self._max_int
        else:
            pos = int((value - self._min_value) /
                      self._value_range * (self._max_int))

        if pos < 0:
            pos = 0
        if pos > self._max_int:
            pos = self._max_int
        super(InfDoubleSlider, self).setValue(pos)

    def setMinimum(self, value):
        if value > self._max_value:
            raise ValueError("Minimum limit cannot be higher than maximum")
        orig_value = self.value()
        self._min_value = value
        self.setValue(orig_value)

    def setMaximum(self, value):
        if value < self._min_value:
            raise ValueError("Minimum limit cannot be higher than maximum")
        orig_value = self.value()
        self._max_value = value
        self.setValue(orig_value)

    def minimum(self):
        return self._min_value

    def maximum(self):
        return self._max_value
