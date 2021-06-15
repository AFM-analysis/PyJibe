import collections
import pathlib
import shutil
import zipfile

import nanite.indent as nindent
import nanite.rate.rater


def get_rating_schemes(rate_ts_path):
    """Return an ordered dict with available rating schemes"""
    schemes = collections.OrderedDict()
    ts = get_training_set_paths(rate_ts_path=rate_ts_path)
    # We currently stick to Extra Trees
    for key in ts:
        schemes["{} + Extra Trees".format(key)] = [ts[key], "Extra Trees"]
    schemes["Disabled"] = ["none", "none"]
    return schemes


def get_training_set_paths(rate_ts_path):
    """Return ordered dict with available training set names and paths"""
    search_path = pathlib.Path(rate_ts_path)
    ts = collections.OrderedDict()
    # training sets from nanite
    nanite_list = nanite.rate.rater.get_available_training_sets()
    for key in nanite_list:
        ts[key] = nanite.rate.IndentationRater.get_training_set_path(key)
    # user-imported training sets
    for pp in sorted(search_path.glob("ts_*")):
        ts[pp.name[3:]] = pp
    return ts


def import_training_set(ts_zip, rate_ts_path, override=False):
    """Open a training set zip file and import it"""
    path = pathlib.Path(ts_zip)
    if not path.suffix == ".zip":
        raise ValueError("Training set file suffix must be '.zip', "
                         "got '{}'!".format(ts_zip.suffix))
    if not path.name.startswith("ts_"):
        raise ValueError("Training set file name must begin with 'ts_', "
                         "got '{}'!".format(ts_zip.name))
    pout = pathlib.Path(rate_ts_path) / path.with_suffix("").name

    if pout.exists():
        if override:
            shutil.rmtree(pout)
        else:
            raise OSError("Training set already exists: {}".format(pout))

    pout.mkdir(exist_ok=True, parents=True)

    with zipfile.ZipFile(ts_zip) as zp:
        zp.extractall(pout)

    # return index in new training set collection
    ts = get_training_set_paths(rate_ts_path=rate_ts_path)
    for idx, key in enumerate(ts.keys()):
        if ts[key] == pout:
            break
    else:
        raise ValueError(f"Something went wrong with '{ts_zip}'!")
    return idx


def rate_fdist(data, scheme_id, rate_ts_path):
    """Rate one or a list of force-distance curves

    Parameters
    ----------
    data: nanite.Indentation or a list of those
        dataset to rate
    scheme_id: int
        index of rating scheme
    rate_ts_path: str or pathlib.Path
        path to the imported training sets
    """
    if isinstance(data, nindent.Indentation):
        data = [data]
        return_single = True
    else:
        return_single = False

    schemes = get_rating_schemes(rate_ts_path)
    scheme_key = list(schemes.keys())[scheme_id]
    training_set, regressor = schemes[scheme_key]
    rates = []
    for fdist in data:
        rt = fdist.rate_quality(regressor=regressor,
                                training_set=training_set)
        rates.append(rt)

    if return_single:
        return rates[0]
    else:
        return rates
