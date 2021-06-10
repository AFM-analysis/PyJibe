import pathlib
import shutil
import tempfile

data_dir = here = pathlib.Path(__file__).parent / "data"


def make_directory_with_data(num_files=1):
    tdir = pathlib.Path(tempfile.mkdtemp(prefix="pyjibe_test_"))
    files = []
    for ii in range(num_files):
        target = tdir / f"test_{ii}.jpk-force"
        shutil.copy2(data_dir / "spot3-0192.jpk-force", target)
        files.append(target)
    return files
