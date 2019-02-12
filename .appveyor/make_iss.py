"""Create InnoSetup .iss file from template"""
import pathlib
import platform

# get version
import pyjibe
version = pyjibe.__version__

here = pathlib.Path(__file__).parent

# read dummy
with (here / "pyjibe.iss_dummy").open('r') as dummy:
    iss = dummy.readlines()

# replace keywords
for i in range(len(iss)):
    if iss[i].strip().startswith("#define MyAppVersion"):
        iss[i] = '#define MyAppVersion "{:s}"\n'.format(version)
    if iss[i].strip().startswith("#define MyAppPlatform"):
        # sys.maxint returns the same for windows 64bit verions
        iss[i] = '#define MyAppPlatform "win_{}"\n'.format(
            platform.architecture()[0])

# write iss
with (here / "pyjibe.iss").open('w') as issfile:
    issfile.writelines(iss)

