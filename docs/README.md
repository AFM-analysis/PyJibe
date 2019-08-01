PyJibe documentation
====================
Building the documentation of PyJibe requires Python 3.
To install the requirements for building the documentation, run

    pip install -r requirements.txt

To compile the documentation, run

    sphinx-build . _build

Notes
=====
To view the sphinx inventory of PyJibe, run

   python -m sphinx.ext.intersphinx 'http://pyjibe.readthedocs.io/en/latest/objects.inv'
