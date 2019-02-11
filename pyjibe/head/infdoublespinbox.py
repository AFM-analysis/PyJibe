import numpy as np

from PyQt5 import QtWidgets, QtGui


class InfDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super(InfDoubleSpinBox, self).__init__(*args, **kwargs)
        self.setMinimum(-np.inf)
        self.setMaximum(np.inf)
        self.validator = FloatValidator()
        self.setDecimals(1000)
        self.setSingleStep(0.1)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return convert_string_to_float(text)

    def textFromValue(self, value):
        return str(value)


class FloatValidator(QtGui.QValidator):
    def validate(self, string, position):
        if valid_float_string(string):
            return self.Acceptable, string, position
        if string == "" or string[position-1] in 'e.-+':
            return self.Intermediate, string, position
        return self.Invalid, string, position

    def fixup(self, text):
        try:
            val = convert_string_to_float(text)
        except ValueError:
            val = ""
        return str(val)


def valid_float_string(string):
    try:
        convert_string_to_float(string)
    except ValueError:
        valid = False
    else:
        valid = True
    return valid


def convert_string_to_float(string):
    try:
        val = float(string)
    except ValueError:
        string = string.strip()
        if string[0] == "-":
            asign = -1
        else:
            asign = 1
        string = string.strip("+-")
        for iid in ["i", "in", "inf"]:
            if string == iid:
                val = asign*np.inf
                break
        else:
            raise ValueError("Not a valid float!")
    return val
