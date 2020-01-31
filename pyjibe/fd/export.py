from collections import OrderedDict
import codecs
import numbers

import numpy as np

from afmformats import meta
import nanite.model as nmodel

from .. import units

#: Valid export choices in `save_tsv_metadata_results`
EXPORT_CHOICES = list(meta.META_FIELDS.keys()) + [
    "params_ancillary",
    "params_fitted",
    "params_initial",
    "rating"]


def save_tsv_metadata_results(filename, fdist_list, which=EXPORT_CHOICES):
    """Export metadata and fitting parameters

    Parameters
    ----------
    filename: str
        Path to store data to
    fdist_list: list-like
        List of :class:`nanite.Indentation` instances
    which: list of str
        Valid for choices to export (see :data:`EXPORT_CHOICES`)
    """
    if np.sum([k not in EXPORT_CHOICES for k in which]):
        raise ValueError("Found invalid export choices.")

    columns = OrderedDict()
    # Metadata
    for ii, fdist in enumerate(fdist_list):
        meta = fdist.metadata.get_summary()
        for topic in meta:
            if topic in which:
                for kk in meta[topic]:
                    label, hrvalue = get_unitname_value_meta(
                        key=kk, value=meta[topic][kk])
                    if label not in columns:
                        columns[label] = [np.nan] * len(fdist_list)
                    columns[label][ii] = hrvalue

        # Parameters
        if "model_key" in fdist.fit_properties:
            model_key = fdist.fit_properties["model_key"]

            # Ancillary
            if "params_ancillary" in which:
                anc_dict = fdist.get_ancillary_parameters()
                for kk in anc_dict:
                    label, hrvalue = get_unitname_value(
                        name=nmodel.get_parm_name(model_key, kk),
                        value=anc_dict[kk],
                        unit=nmodel.get_parm_unit(model_key, kk))
                    if label not in columns:
                        columns[label] = [np.nan] * len(fdist_list)
                    columns[label][ii] = hrvalue

            # Initial
            if "params_initial" in which:
                if "params_initial" in fdist.fit_properties:
                    fp = fdist.fit_properties["params_initial"]
                    for ki in fp:
                        if not fp[ki].vary:
                            label, hrvalue = get_unitname_value(
                                name=nmodel.get_parm_name(model_key, ki),
                                value=fp[ki].value,
                                unit=nmodel.get_parm_unit(model_key, ki))
                            if label not in columns:
                                columns[label] = [np.nan] * len(fdist_list)
                            columns[label][ii] = hrvalue

            # Fitted
            if "params_fitted" in which:
                if "params_fitted" in fdist.fit_properties:
                    fp = fdist.fit_properties["params_fitted"]
                    for ki in fp:
                        if fp[ki].vary:
                            label, hrvalue = get_unitname_value(
                                name=nmodel.get_parm_name(model_key, ki),
                                value=fp[ki].value,
                                unit=nmodel.get_parm_unit(model_key, ki))
                            if label not in columns:
                                columns[label] = [np.nan] * len(fdist_list)
                            columns[label][ii] = hrvalue

                    # Additional fit parameters
                    props = {"xmin": ("Fit interval minimum", "m"),
                             "xmax": ("Fit interval maximum", "m"),
                             "segment": ("Fit segment", ""),
                             "weight_cp": ("Fit weight contact point", "m"),
                             "model_key": ("Fit model", ""),
                             }
                    for prop in props:
                        label, hrvalue = get_unitname_value(
                            name=props[prop][0],
                            value=fdist.fit_properties[prop],
                            unit=props[prop][1])
                        if label not in columns:
                            columns[label] = [np.nan] * len(fdist_list)
                        columns[label][ii] = hrvalue

            if "rating" in which:
                rdict = fdist.get_rating_parameters()
                for label in ["Regressor", "Training set", "Rating"]:
                    if label not in columns:
                        columns[label] = [np.nan] * len(fdist_list)
                    columns[label][ii] = rdict[label]

    save_tsv(filename, columns)


def save_tsv(filename, column_dict):
    """Export data set to a .tsv file

    Parameters
    ----------
    filename: str
        Filename to save as
    column_dict: dict of lists
        List with column headers and content to save.
        E.g.: {"Column One": [1.1, 2.2, 3.3, 4.4],
               "Column Two": [nan, 2.0, 4.0, 1.0],
               }
    """
    with codecs.open(filename, "wb") as fd:
        fd.write(codecs.BOM_UTF8)
    with codecs.open(filename, "a", encoding="utf-8") as fd:
        # Write header:
        header = "\t".join([d for d in list(column_dict.keys())])
        fd.write(header+"\r\n")

        # Write data
        cols = list(column_dict.values())
        # Transpose data
        data = transpose_list(cols)
        # Save line-wise
        for d in data:
            line = "\t".join([format_content(it) for it in d])
            fd.write(line+"\r\n")


def format_content(value):
    if isinstance(value, numbers.Number):
        return "{:.5g}".format(value)
    else:
        return "{}".format(value)


def get_unitname_value_meta(key, value):
    """Return header / value pair for tsv export of Indentation metadata"""
    name, unit, validator = meta.DEF_ALL[key]
    if isinstance(value, numbers.Number):
        if not np.isnan(value):
            value = validator(value)
    else:
        value = validator(value)
    return get_unitname_value(name, value, unit)


def get_unitname_value(name, value, unit):
    """Return header / value pair for tsv export"""
    if isinstance(value, numbers.Number):
        hrvalue, scunit = units.si2hr(name=name, value=value, si_unit=unit)
        strunit = " [{}]".format(scunit) if scunit else ""
        header = name + strunit
    else:
        hrvalue = value
        header = name
    return header, hrvalue


def transpose_list(m):
    height = len(m)
    width = len(m[0])
    tr = [[m[row][col] for row in range(0, height)] for col in range(0, width)]
    return tr
