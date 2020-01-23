import numpy as np

import pyjibe.fd.tab_info


def test_all_nan_dict():
    assert pyjibe.fd.tab_info.has_all_nans({"a": np.nan, "b": np.nan})
    assert not pyjibe.fd.tab_info.has_all_nans({"a": 1, "b": np.nan})
    assert not pyjibe.fd.tab_info.has_all_nans({"a": "1", "b": np.nan})
