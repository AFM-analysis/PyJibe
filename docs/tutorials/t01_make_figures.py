"""Screenshots for quick guide import ts (not working automatically)"""
import pathlib
import shutil
import sys
import tempfile

import matplotlib.pylab as plt
import numpy as np
import pandas
import seaborn as sns
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from pyjibe.head.main import PyJibe


datapath = pathlib.Path("figshare_AFM-PAAm-gels_11637675.v3")

app = QApplication(sys.argv)
QtCore.QLocale.setDefault(QtCore.QLocale(QtCore.QLocale.C))
mw = PyJibe()


# copy files to separate folder
tempdir = pathlib.Path(tempfile.mkdtemp(prefix="pyjibe_t01_"))
dir_compl = tempdir / "compliant"
dir_compl.mkdir()
dir_stiff = tempdir / "stiff"
dir_stiff.mkdir()

for p in datapath.glob("*.jpk-force"):
    if p.name.count("Stiff"):
        shutil.copy2(p, dir_stiff)
    elif p.name.count("Compliant"):
        shutil.copy2(p, dir_compl)

# build up a session
mw.load_data(list(dir_compl.glob("*.jpk-force")))
mw.load_data(list(dir_stiff.glob("*.jpk-force")))

# main
QApplication.processEvents()
mw.grab().save("_t01_main_init.png")

warc = mw.subwindows[0].widget()
wars = mw.subwindows[1].widget()

# set parameters
for war in [warc, wars]:
    idm = war.tab_fit.cb_model.findData("sneddon_spher_approx")
    war.tab_fit.cb_model.setCurrentIndex(idm)
    war.tab_fit.sp_range_2.setValue(2)
    war.tab_fit.table_parameters_initial.item(1, 1).setText("5")
    war.tab_fit.cb_weight_cp.setCheckState(QtCore.Qt.Unchecked)
    war.btn_fitall.clicked.emit()

QApplication.processEvents()
warc.grab().save("_t01_fd_compliant.png")
wars.grab().save("_t01_fd_stiff.png")

mw.close()

data_compl = pandas.read_table(dir_compl/"pyjibe_fit_results_leaf.tsv")
data_stiff = pandas.read_table(dir_stiff/"pyjibe_fit_results_leaf.tsv")

sns.set_style("darkgrid")

plt.subplot(121, title="compliant hydrogel")
sns.boxplot("Young\'s Modulus [Pa]", data=data_compl, fliersize=0,
            color="#d6ff7d")
sns.swarmplot("Young\'s Modulus [Pa]", data=data_compl,
              size=5, color=".3", linewidth=0)

plt.subplot(122, title="stiff hydrogel")
sns.boxplot("Young\'s Modulus [Pa]", data=data_stiff, fliersize=0,
            color="#98ff80")
sns.swarmplot("Young\'s Modulus [Pa]", data=data_stiff,
              size=5, color=".3", linewidth=0)

plt.tight_layout()
plt.savefig("_t01_comparison.png", dpi=300)

print("Compliant mean +- SD: {:.5g} +- {:.5g}".format(
    np.mean(data_compl["Young\'s Modulus [Pa]"]),
    np.std(data_compl["Young\'s Modulus [Pa]"])
))

print("Stiff mean +- SD: {:.5g} +- {:.5g}".format(
    np.mean(data_stiff["Young\'s Modulus [Pa]"]),
    np.std(data_stiff["Young\'s Modulus [Pa]"])
))

shutil.rmtree(tempdir)
