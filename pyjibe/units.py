"""Helper methods for handling units in PyJibe"""


def si2hr(name, value, si_unit=None):
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
        scaleunit = scalename + unit
    elif si_unit in default_scales:
        scalename = default_scales[si_unit]
        scale = scales[scalename]
        hr_value = value/scale
        scaleunit = scalename + si_unit
    elif si_unit is not None:
        hr_value = value
        scaleunit = si_unit
    else:
        hr_value = value
        scaleunit = ""
    return hr_value, scaleunit


def hrscale(name, si_unit=None):
    """Returns the multiplier for unit scale conversion, e.g. 1e6 for µm"""
    name = name.lower()
    if name in human_units:
        scalename, _unit = human_units[name]
        scale = 1/scales[scalename]
    elif si_unit in default_scales:
        scalename = default_scales[si_unit]
        scale = 1/scales[scalename]
    else:
        scale = 1
    return scale


def hrunit(name, si_unit=None):
    """Returns the unit name for scale conversion, e.g. µm"""
    name = name.lower()
    if name in human_units:
        scalename, unit = human_units[name]
        scaleunit = scalename + unit
        if si_unit is not None and si_unit != unit:
            raise ValueError(
                "Bad `si_unit` '{}' given for '{}', expected '{}'! ".format(
                    si_unit, name, unit))
    elif si_unit in default_scales:
        scaleunit = default_scales[si_unit] + si_unit
    elif si_unit is not None:
        scaleunit = si_unit
    else:
        scaleunit = ""
    return scaleunit


def hrscname(name, si_unit=None):
    """Returns the name with human readable units, e.g. Force [nN]"""
    unit = hrunit(name, si_unit=si_unit)
    if unit == "":
        hrscname = name
    else:
        hrscname = "{} [{}]".format(name, unit)
    return hrscname


# TODO:
# - make the scales user-editable
default_scales = {"deg": "",
                  "m": "µ",
                  "m/s": "µ",
                  "m/V": "n",
                  "N": "n",
                  "Pa": "",
                  "Pa·s": "",
                  }

human_units = {}
human_units["young's modulus"] = [default_scales["Pa"], "Pa"]
human_units["tip radius"] = ["µ", "m"]
human_units["contact point"] = ["n", "m"]
human_units["force"] = [default_scales["N"], "N"]
human_units["force baseline"] = ["p", "N"]
human_units["tip position"] = [default_scales["m"], "m"]

scales = {}
scales["k"] = 1e3
scales[""] = 1
scales["m"] = 1e-3
scales["µ"] = 1e-6
scales["n"] = 1e-9
scales["p"] = 1e-12
