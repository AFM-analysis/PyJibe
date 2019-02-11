"""Helper methods for handling units in PyJibe"""


def si2hr(name, value):
    """Convert an SI unit to a human readable unit

    Parameters
    ----------
    name: str
        The parameter name string, see `human_units`.
    value: float or array
        The value of the parameters that will be converted
        to a human readable scale.

    Returns
    -------
    hr_value: float
        The human readable value.
    scaleunit: str
        The unit including the scale, e.g. "µm".
    """
    name = name.lower()
    if name in human_units:
        scalename, unit = human_units[name]
        scale = scales[scalename]
        hr_value = value/scale
        scaleunit = scalename+unit
    else:
        hr_value = value
        scaleunit = ""
    return hr_value, scaleunit


def hrscale(name):
    """Returns the multiplier for unit scale conversion, e.g. 1e6 for µm"""
    name = name.lower()
    if name in human_units:
        scalename, _unit = human_units[name]
        scale = 1/scales[scalename]
    else:
        scale = 1
    return scale


def hrunit(name):
    """Returns the unit name for scale conversion, e.g. µm"""
    name = name.lower()
    if name in human_units:
        scalename, unit = human_units[name]
        scaleunit = scalename+unit
    else:
        scaleunit = ""
    return scaleunit


def hrscname(name):
    """Returns the name with human readable units, e.g. Force [nN]"""
    unit = hrunit(name)
    if unit == "":
        hrscname = name
    else:
        hrscname = "{} [{}]".format(name, unit)
    return hrscname


# TODO:
# - make the scales user-editable
human_units = {}
human_units["young's modulus"] = ["", "Pa"]
human_units["tip radius"] = ["µ", "m"]
human_units["contact point"] = ["n", "m"]
human_units["force"] = ["n", "N"]
human_units["force baseline"] = ["p", "N"]
human_units["tip position"] = ["µ", "m"]
human_units["half cone angle"] = ["", "deg"]


scales = {}
scales["k"] = 1e3
scales[""] = 1
scales["m"] = 1e-3
scales["µ"] = 1e-6
scales["n"] = 1e-9
scales["p"] = 1e-12
