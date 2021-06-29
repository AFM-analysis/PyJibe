from afmformats.formats import formats_by_modality

from . import fd


analysis_types = {
    "fd": {
        "suffixes": [f["suffix"]
                     for f in formats_by_modality["force-distance"]],
        "gui": fd.UiForceDistance,
    }
}

known_suffixes = []
for _item in analysis_types.values():
    known_suffixes += _item["suffixes"]
