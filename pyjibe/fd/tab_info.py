import numbers
import pkg_resources

from afmformats import meta
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

        text.append("<b>Dataset</b>")
        data_keys = ["path", "enum"]
        for kk in data_keys:
            text.append(get_string_rep(kk, fdist.metadata))
        for kk in keys:
            if kk in meta.DEF_DATA and kk not in data_keys:
                text.append(get_string_rep(kk, fdist.metadata))

        if set(keys) & set(meta.DEF_EXPERIMENT.keys()):
            text.append("")
            text.append("<b>Experiment:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_EXPERIMENT:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
            text += sorted(text_meta)

        if set(keys) & set(meta.DEF_QMAP.keys()):
            text.append("")
            text.append("<b>QMap:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_QMAP:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
            text += sorted(text_meta)

        if set(keys) & set(meta.DEF_ANALYSIS.keys()):
            text.append("")
            text.append("<b>Analysis:</b>")
            text_meta = []
            for kk in keys:
                if kk in meta.DEF_ANALYSIS:
                    text_meta.append(get_string_rep(kk, fdist.metadata))
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
