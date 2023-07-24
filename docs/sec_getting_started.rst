===============
Getting started
===============

Installation
============
PyJibe can be installed via multiple channels:

1. **Windows installer:** Download the latest version for your architecture
   (e.g. ``PyJibe_X.Y.Z_win_64bit_setup.exe`` for 64bit Windows) from the
   official
   `release page <https://github.com/AFM-analysis/PyJibe/releases/latest>`__. 

2. **macOS:** Download the latest version
   (``PyJibeApp_X.Y.Z.dmg``) from the official
   `release page <https://github.com/AFM-analysis/PyJibe/releases/latest>`__. 

3. **Python 3 with pip:** PyJibe can easily be installed with
   `pip <https://pip.pypa.io/en/stable/quickstart/>`__:

   .. code:: bash

       pip install pyjibe

   To start PyJibe, simply run ``python -m pyjibe`` or just ``pyjibe``
   in a command shell. 


Update
======
If you install a newer (or older) version of PyJibe, the previously installed
version will be automatically uninstalled.

If you installed pyjibe with ``pip``, you may upgrade it with:

.. code:: bash

    pip install --upgrade pyjibe


Supported file formats
======================
PyJibe relies on the :ref:`afmformats <afmformats:index>` package.
A list of supported file formats can be found
:ref:`here <afmformats:supported_formats>`.


How to cite
===========
If you use PyJibe in a scientific publication, please cite it with:

.. pull-quote::

   Paul Müller and others (2019), PyJibe version X.X.X: Atomic force
   microscopy data analysis [Software].
   Available at https://github.com/AFM-analysis/PyJibe.

Please also consider citing Müller et al., *BMC Bioinformatics* (2019)
:cite:`Mueller19nanite` (for fitting and rating force-indentation data).
