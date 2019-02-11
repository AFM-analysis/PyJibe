import codecs
import numpy as np
import os

import nanite.model as nmodel

from .. import units


def save_tsv_approach_retract(filename, fdist_list, ratings=[]):
    """Export a list of afmlib.ApproachRetract instances"""

    columns = []

    columns.append(["Filename",
                    [os.path.basename(ar.path) for ar in fdist_list]])
    columns.append(["Position Index",
                    [ar.enum for ar in fdist_list]])
    columns.append(["X Position",
                    [np.nan]*len(fdist_list)])
    columns.append(["Y Position",
                    [np.nan]*len(fdist_list)])
    # Add fit parameters
    model_key = fdist_list[0].fit_properties["model_key"]
    model = nmodel.models_available[model_key]
    for name, key in zip(model.parameter_names, model.parameter_keys):
        values = []
        for ar in fdist_list:
            v = ar.fit_properties["params_fitted"][key].value
            values.append(units.si2hr(name, v)[0])
        hrname = units.hrscname(name)
        columns.append([hrname, values])
    # Add fit properties
    props = ["xmin", "xmax", "segment", "weight_cp", "model_key"]
    for prop in props:
        values = []
        vs = [ar.fit_properties[prop] for ar in fdist_list]
        columns.append(["fit "+prop, vs])
    if ratings:  # Add rating
        columns.append(["rating", ratings])
    save_tsv(filename, columns)


def save_tsv(filename, column_lists):
    """Export data set to a .tsv file

    Parameters
    ----------
    filename: str
        Filename to save as
    column_lists: list
        List with column headers and content to save.
        E.g.: ["Column One", [1.1, 2.2, 3.3, 4.4],
               "Column Two", [nan, 2.0, 4.0, 1.0]]
    """
    with codecs.open(filename, "w", encoding="utf-8") as fd:
        # Write header:
        header = "\t".join([d[0] for d in column_lists])
        fd.write(header+"\r\n")

        # Write data
        cols = [d[1] for d in column_lists]
        # Transpose data
        data = transpose_list(cols)
        # Save line-wise
        for d in data:
            line = "\t".join([format_content(it) for it in d])
            fd.write(line+"\r\n")


def format_content(value):
    try:
        float(value)
    except ValueError:
        return "{}".format(value)
    else:
        return "{:.6e}".format(value)


def transpose_list(m):
    height = len(m)
    width = len(m[0])
    tr = [[m[row][col] for row in range(0, height)] for col in range(0, width)]
    return tr
