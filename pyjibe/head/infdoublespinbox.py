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
        return convert_float_to_string(value)


class FloatValidator(QtGui.QValidator):
    def __init__(self, *args, **kwargs):
        super(FloatValidator, self).__init__(*args, **kwargs)
        self.previous = None

    def validate(self, string, position):
        previous = self.previous
        self.previous = string

        if string.count(".") > 1:
            # if user types "." and there is already a dot, let the cursor
            # move to the other side
            if not string[position-1] == ".":
                # user pressed "." another time -> don't go forward
                position -= 1
            a, b = string.split(".", 1)
            string = ".".join([a, b.replace(".", "")])

            return self.Acceptable, string, position
        elif (previous is not None and previous.count(".")
                and not string.count(".") and position == previous.index(".")):
            # make sure removing decimal point does not lead to large numbers
            # (1.003 -> 1003)
            string = string[:position]
            return self.Acceptable, string, position
        elif string == "":
            return self.Intermediate, string, position
        elif string and string[position-1] in '.e-+':
            # remove trailing numbers
            return self.Intermediate, string.rstrip("0"), position
        elif valid_float_string(string):
            return self.Acceptable, string, position
        else:
            return self.Invalid, string, position

    def fixup(self, text):
        try:
            text = convert_float_to_string(convert_string_to_float(text))
        except ValueError:
            text = ""
        return text


def valid_float_string(string):
    try:
        convert_string_to_float(string)
    except ValueError:
        valid = False
    else:
        valid = True
    return valid


def convert_float_to_string(value):
    """Convert float to a string"""
    text = f"{value:.7g}"
    if not text.count("e"):
        # We don't have the exponential notation.
        text = str(value)
    return text


def convert_string_to_float(string):
    """Convert string of float or +/- "inf" to float"""
    try:
        val = float(string)
    except ValueError:
        string = string.strip()
        if string.startswith("-"):
            asign = -1
        else:
            asign = 1
        string = string.strip("+-")
        for iid in ["i", "in", "inf"]:
            if string == iid:
                val = asign * np.inf
                break
        else:
            raise ValueError("Not a valid float!")
    return val
