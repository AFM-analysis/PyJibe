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
        msum = fdist.metadata.get_summary()

        text = []

        # Dataset
        text.append("<b>Dataset</b>")
        for kk in msum["dataset"]:
            text.append(get_string_rep_meta(kk, msum["dataset"][kk]))

        # Experiment
        text.append("")
        text.append("<b>Experiment:</b>")
        texte = []
        for kk in msum["experiment"]:
            texte.append(get_string_rep_meta(kk, msum["experiment"][kk]))
        text += sorted(texte)

        # QMap
        if msum["qmap"] and not has_all_nans(msum["qmap"]):
            text.append("")
            text.append("<b>QMap:</b>")
            textq = []
            for kk in msum["qmap"]:
                textq.append(get_string_rep_meta(kk, msum["qmap"][kk]))
            text += sorted(textq)

        # Analysis
        if msum["analysis"] and not has_all_nans(msum["analysis"]):
            text.append("")
            text.append("<b>Analysis:</b>")
            texta = []
            for kk in msum["analysis"]:
                texta.append(get_string_rep_meta(kk, msum["analysis"][kk]))
            text += sorted(texta)

        # Ancillaries
        anc_dict = fdist.get_ancillary_parameters()
        if anc_dict:
            text.append("")
            text.append("<b>Ancillaries:</b>")
            text_meta = []
            model_key = fdist.fit_properties["model_key"]
            for kk in anc_dict:
                text_meta.append(
                    get_string_rep(name=model.get_parm_name(model_key, kk),
                                   value=anc_dict[kk],
                                   unit=model.get_parm_unit(model_key, kk)))
            text += sorted(text_meta)

        textstring = "<br>".join(text)

        self.info_text.setText(textstring)


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
        rep = "{}: {:.5g}{}".format(name,
                                    hrvalue,
                                    " " + scunit if scunit else "",
                                    )
    else:
        rep = "{}: {}".format(name, value)

    return rep


def has_all_nans(adict):
    """Check whether a dictionary as all-nan values"""
    for value in adict.values():
        if isinstance(value, numbers.Number):
            if not np.isnan(value):
                notallnan = True
                break
        else:
            notallnan = True
            break
    else:
        notallnan = False
    return notallnan
