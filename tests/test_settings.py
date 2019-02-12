import pathlib

from pyjibe import settings


def test_cfg_basic():
    cfg = settings.SettingsFile()
    wd = pathlib.Path(".").resolve()
    cfg.set_path(str(wd.parent), "Peter")

    assert wd.parent == pathlib.Path(cfg.get_path("Peter")).resolve()


if __name__ == "__main__":
    # Run all tests
    loc = locals()
    for key in list(loc.keys()):
        if key.startswith("test_") and hasattr(loc[key], "__call__"):
            loc[key]()
