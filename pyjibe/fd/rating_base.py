import appdirs
import collections
import pathlib
import shutil
import zipfile

import nanite.indent as nindent
import nanite.rate.rater


_cfg_dir = appdirs.user_config_dir(appname="PyJibe", appauthor="AFM-Analysis")
#: Rating configuration directory
CFG_DIR = pathlib.Path(_cfg_dir) / "rating"
#: Path to main rating configuration file
CFG_PATH = CFG_DIR / "rating_schemes.txt"


def get_rating_schemes():
    """Return an ordered dict with available rating schemes"""
    schemes = collections.OrderedDict()
    ts = get_training_set_paths()
    # We currently stick to Extra Trees
    for key in ts:
        schemes["{} + Extra Trees".format(key)] = [ts[key], "Extra Trees"]
    schemes["Disabled"] = ["none", "none"]
    return schemes


def get_training_set_paths():
    """Return ordered dict with available training set names and paths"""
    ts = collections.OrderedDict()
    # training sets from nanite
    nanite_list = nanite.rate.rater.get_available_training_sets()
    for key in nanite_list:
        ts[key] = nanite.rate.IndentationRater.get_training_set_path(key)
    # user-imported training sets
    for pp in sorted(CFG_DIR.glob("ts_*")):
        ts[pp.name[3:]] = pp
    return ts


def import_training_set(ts_zip, override=False):
    """Open a training set zip file and import it to :const:`CFG_DIR`"""
    path = pathlib.Path(ts_zip)
    if not path.suffix == ".zip":
        raise ValueError("Training set file suffix must be '.zip', "
                         "got '{}'!".format(ts_zip.suffix))
    if not path.name.startswith("ts_"):
        raise ValueError("Training set file name must begin with 'ts_', "
                         "got '{}'!".format(ts_zip.name))
    pout = CFG_DIR / path.with_suffix("").name

    if pout.exists():
        if override:
            shutil.rmtree(pout)
        else:
            raise OSError("Training set already exists: {}".format(pout))

    pout.mkdir(exist_ok=True, parents=True)

    with zipfile.ZipFile(ts_zip) as zp:
        zp.extractall(pout)

    # return index in new training set collection
    ts = get_training_set_paths()
    for idx, key in enumerate(ts.keys()):
        if ts[key] == pout:
            break
    return idx


def rate_fdist(data, scheme_id):
    """Rate one or a list of force-distance curves

    Parameters
    ----------
    data: nanite.Indentation or a list of those
    """
    if isinstance(data, nindent.Indentation):
        data = [data]
        return_single = True
    else:
        return_single = False

    schemes = get_rating_schemes()
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
