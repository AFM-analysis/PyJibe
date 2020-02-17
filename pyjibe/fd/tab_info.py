import numbers
import pkg_resources

from afmformats import meta
from nanite import model
import numpy as np
from PyQt5 import uic, QtWidgets

from .. import units


class TabInfo(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabInfo, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_info.ui")
        uic.loadUi(path_ui, self)

    def update_info(self, fdist):
        hr_info = {}

        # Metadata
        msum = fdist.metadata.get_summary()
        for sec in msum:
            if sec == "qmap":
                if msum["qmap"] and not has_all_nans(msum["qmap"]):
                    textq = []
                    for kk in msum["qmap"]:
                        textq.append(get_string_rep_meta(kk, msum["qmap"][kk]))
                    hr_info["QMap"] = textq
            else:
                atext = []
                for kk in msum[sec]:
                    atext.append(get_string_rep_meta(kk, msum[sec][kk]))
                hr_info[sec.capitalize()] = atext

        # Ancillaries
        anc_dict = fdist.get_ancillary_parameters()
        if anc_dict:
            text_meta = []
            model_key = fdist.fit_properties["model_key"]
            for kk in anc_dict:
                text_meta.append(
                    get_string_rep(name=model.get_parm_name(model_key, kk),
                                   value=anc_dict[kk],
                                   unit=model.get_parm_unit(model_key, kk)))
            hr_info["Ancillaries"] = text_meta

        text = []
        for sec in sorted(hr_info.keys()):
            text.append("<b>{}:</b>".format(sec))
            text += sorted(hr_info[sec])
            text.append("")

        textstring = "<br>".join(text)

        # remember the scroll position
        vval = self.info_text.verticalScrollBar().value()
        hval = self.info_text.horizontalScrollBar().value()
        self.info_text.setText(textstring)
        self.info_text.verticalScrollBar().setValue(vval)
        self.info_text.horizontalScrollBar().setValue(hval)


def get_string_rep_meta(key, value):
    """Return a nice string representation for a key in metadata"""
    name, unit, validator = meta.DEF_ALL[key]
    if isinstance(value, numbers.Number):
        if not np.isnan(value):
            value = validator(value)
    else:
        value = validator(value)
    return get_string_rep(name, value, unit)


def get_string_rep(name, value, unit):
    """Return pretty-formatted string for key, value, and unit"""

    if isinstance(value, numbers.Number):
        hrvalue, scunit = units.si2hr(name=name, value=value, si_unit=unit)

        if np.isnan(value):
            rep = "<span style='color:#757575'>{}: unknown</span>".format(name)
        else:
            rep = "{}: {:.5g}{}".format(name,
                                        hrvalue,
                                        " " + scunit if scunit else "",
                                        )
    else:
        rep = "{}: {}".format(name, value)

    return rep


def has_all_nans(adict):
    """Check whether a dictionary as all-nan values"""
    allnan = True
    for value in adict.values():
        if isinstance(value, numbers.Number):
            if not np.isnan(value):
                allnan = False
                break
        else:
            allnan = False
            break
    return allnan
