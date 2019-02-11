from . import fd


analysis_types = {"fd":
                  {"file extensions": [".jpk", ".jpk-force"],
                   "gui": fd.UiForceDistance,
                   }}

file_extensions = []
for _item in analysis_types.values():
    file_extensions += _item["file extensions"]
