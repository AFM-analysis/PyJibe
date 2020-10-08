"""Settings file management"""
import numbers
import pathlib

import appdirs

#: application name
NAME = "PyJibe"
#: application author
ORG = "AFM-Analysis"

#: default configuration parameters
DEFAULTS = {}


class SettingsFile(object):
    """Manages a settings file in the user's config dir"""

    def __init__(self, name=NAME, org=ORG, defaults=DEFAULTS, directory=None):
        """Initialize settings file (create if it does not exist)"""
        if directory is None:
            directory = appdirs.user_config_dir(appname=name, appauthor=org)
        fname = pathlib.Path(directory) / (name.replace(" ", "_") + ".cfg")
        # create file if not existent
        if not fname.exists():
            fname.parent.mkdir(exist_ok=True, parents=True)
            # Create the file
            fname.open("w").close()

        self.cfgfile = fname
        self.defaults = defaults
        self.working_directories = {}

    def _get_value(self, dtype, key):
        key = key.lower()
        cdict = self.load()
        if key in cdict:
            val = cdict[key]
        elif dtype in self.defaults and key in self.defaults[dtype]:
            val = self.defaults[dtype][key]
        else:
            raise KeyError(
                "Config key '{}' of type '{}' not set!".format(key, dtype))

        if dtype == "bool":
            if isinstance(val, bool):
                pass
            else:
                if val.lower() not in ["true", "false"]:
                    raise ValueError(
                        "Config key '{}' not boolean!".format(key))
                elif val.lower() == "true":
                    val = True
                else:
                    val = False
        elif dtype == "integer":
            if isinstance(val, numbers.Integral):
                pass
            else:
                if not val.isdigit():
                    raise ValueError(
                        "Config key '{}' is no integer!".format(key))
                val = int(val)
        elif dtype == "string_list":
            if isinstance(val, list):
                pass
            else:
                val = val.split("\t")

        return val

    def get_bool(self, key):
        """Returns boolean configuration key"""
        return self._get_value("bool", key)

    def get_int(self, key):
        """Returns integer configuration key"""
        return self._get_value("integer", key)

    def get_path(self, name=""):
        """Returns the path for label `name`"""
        wdkey = "path {}".format(name.lower())
        try:
            path = self._get_value("path", wdkey)
        except KeyError:
            path = "."
        return path

    def get_string(self, key):
        """Return string"""
        try:
            val = self._get_value("string", key)
        except KeyError:
            val = ""
        return val

    def get_string_list(self, key):
        """Returns list of strings"""
        return self._get_value("string_list", key)

    def load(self):
        """Loads the settings file returning a dictionary"""
        with self.cfgfile.open() as fop:
            fc = fop.readlines()
        cdict = {}
        for line in fc:
            line = line.strip()
            var, val = line.split("=", 1)
            cdict[var.lower().strip()] = val.strip()
        return cdict

    def save(self, cdict):
        """Save a settings dictionary into a file"""
        if not self.cfgfile:
            raise SettingsFileError("Settings path not set!")
        skeys = list(cdict.keys())
        skeys.sort()
        outlist = []
        for sk in skeys:
            outlist.append("{} = {}\n".format(sk, cdict[sk]))

        with self.cfgfile.open('w') as fop:
            fop.writelines(outlist)

    def set_bool(self, key, value):
        """Sets boolean key in the settings file"""
        cdict = self.load()
        cdict[key.lower()] = bool(value)
        self.save(cdict)

    def set_int(self, key, value):
        """Sets integer key in the settings file"""
        cdict = self.load()
        cdict[key.lower()] = int(value)
        self.save(cdict)

    def set_path(self, wd, name=""):
        """Set the path in the settings file"""
        cdict = self.load()
        wdkey = "path {}".format(name.lower())
        cdict[wdkey] = wd
        self.save(cdict)

    def set_string(self, key, value=""):
        """Set the path in the settings file"""
        if value.strip():
            cdict = self.load()
            cdict[key] = value
            self.save(cdict)

    def set_string_list(self, key, value):
        """Set a list of strings"""
        if not isinstance(value, list):
            raise ValueError("`value` must be a list!")
        for ch in ["\t", "\n"]:
            if "".join(value).count(ch):
                raise ValueError("List items must not contain {}!".format(ch))
        cdict = self.load()
        cdict[key.lower()] = "\t".join(value)
        self.save(cdict)


class SettingsFileCache(SettingsFile):
    """A SettingsFile-based data cache"""

    def __init__(self, name):
        directory = appdirs.user_cache_dir()
        super(SettingsFileCache, self).__init__(name=name,
                                                defaults={},
                                                directory=directory)


class SettingsFileError(BaseException):
    pass
