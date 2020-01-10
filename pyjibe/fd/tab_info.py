import numbers
import pkg_resources

from afmformats import meta
from nanite import model
from PyQt5 import uic, QtWidgets


class TabInfo(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        super(TabInfo, self).__init__(*args, **kwargs)
        path_ui = pkg_resources.resource_filename("pyjibe.fd",
                                                  "tab_info.ui")
        uic.loadUi(path_ui, self)

    def update_info(self, fdist):
        text = []
        keys = list(fdist.metadata.keys())

        # Dataset
        text.append("<b>Dataset</b>")
        data_keys = ["path", "enum"]
        for kk in data_keys:
            text.append(get_string_rep(kk, fdist.metadata))
        for kk in keys:
            if kk in meta.DEF_DATA and kk not in data_keys:
                text.append(get_string_rep(kk, fdist.metadata))

        # Experiment
        if set(keys) & set(meta.DEF_EXPERIMENT.keys()):
            text.append("")
            text.append("<b>Experiment:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_EXPERIMENT:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
            text += sorted(text_meta)

        # QMap
        if set(keys) & set(meta.DEF_QMAP.keys()):
            text.append("")
            text.append("<b>QMap:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_QMAP:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
            text += sorted(text_meta)

        # Analysis
        if set(keys) & set(meta.DEF_ANALYSIS.keys()):
            text.append("")
            text.append("<b>Analysis:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_ANALYSIS:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
            text += sorted(text_meta)

        # Ancillaries
        anc_dict = fdist.get_ancillary_parameters()
        if anc_dict:
            text.append("")
            text.append("<b>Ancillaries:</b>")
            text_meta = []
            md = model.models_available[fdist.fit_properties["model_key"]]
            for kk in anc_dict:
                idk = md.parameter_anc_keys.index(kk)
                text_meta.append("{}: {:.5g} {}".format(
                    md.parameter_anc_names[idk],
                    anc_dict[kk],
                    md.parameter_anc_units[idk]))
            text += sorted(text_meta)

        textstring = "<br>".join(text)

        self.info_text.setText(textstring)


def get_string_rep(key, metadata):
    """Return a nice string representation for a key in metadata"""
    value = metadata[key]
    desc, unit, validator = meta.DEF_ALL[key]

    value = validator(value)

    if unit == "m":
        unit = "µm"
        value *= 1e6

    if isinstance(value, numbers.Integral):
        pass
    elif isinstance(value, numbers.Real):
        if abs(value) > 1:
            value = "{:.2f}".format(value)
        elif abs(value) > 1e-2:
            value = "{:.5f}".format(value)
        else:
            value = "{:.3e}".format(value)

    rep = "{}: {}".format(desc, value)
    if unit:
        rep += " {}".format(unit)
    return rep
