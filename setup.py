from os.path import dirname, realpath, exists
from setuptools import setup, find_packages
import sys


author = u"Paul Müller"
authors = [author]
description = 'Graphical user interface for Bio-AFM analysis'
name = 'pyjibe'
year = "2019"

sys.path.insert(0, realpath(dirname(__file__))+"/"+name)
from _version import version

setup(
    name=name,
    author=author,
    author_email='dev@craban.de',
    url='https://github.com/AFM-analysis/PyJibe',
    version=version,
    packages=find_packages(),
    package_dir={name: name},
    include_package_data=True,
    license="GPL v3",
    description=description,
    long_description=open('README.rst').read() if exists('README.rst') else '',
    install_requires=["appdirs",
                      "nanite>=1.1.0",
                      "matplotlib",
                      "pyqt5"],
    python_requires='>=3.6, <4',
    entry_points={"gui_scripts" : ['pyjibe = pyjibe.__main__:main']},
    keywords=["atomic force microscopy", "biomechanics"],
    setup_requires=['pytest-runner'],
    tests_require=["pytest", "pytest-qt"],
    classifiers= [
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering :: Visualization',
        'Intended Audience :: Science/Research'
                 ],
    platforms=['ALL'],
    )
