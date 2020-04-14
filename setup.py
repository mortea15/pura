#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Morten Amundsen'
__contact__ = 'm.amundsen@sportradar.com'

from setuptools import find_packages, setup

version = '0.0.1'
long_desc = '''PURA -- Processes User Reports Automatically

PURA is a system to help with the processing of user incident reports
by assessing the reports it receives and responding to the reporter.

it uses a combination of machine learning and natural language processing for classification of emails,
runs the associated hosts against threat intel, responds to the user with a category and handles
issue creation in jira for metrics.
'''.lstrip()

classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Sportradar, NTNU',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Information Technology',
    'Intended Audience :: Science/Research',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
    'Topic :: Scientific/Engineering :: Human Machine Interfaces',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: Text Processing',
    'Topic :: Text Processing :: Filters',
    'Topic :: Text Processing :: General',
    'Topic :: Text Processing :: Linguistic'
]

requires = [
    'scikit-learn',
    'tqdm',
    'pandas',
    'numpy',
    'diffprivlib'
]

ext_deps = [
    'git+ssh://git@github.com/mortea15/emailyzer.git',
    'git+ssh://git@github.com/mortea15/juicer.git',
    'git+ssh://git@github.com/mortea15/katatasso.git'
]

setup(
    name='pura',
    version=version,
    description='An automated user incident report handler',
    long_description=long_desc,
    long_description_content_type='text/markdown',
    install_requires=requires,
    dependency_links=ext_deps,
    url='https://github.com/mortea15/pura.git',
    author=__author__,
    author_email=__contact__,
    packages=['pura', 'pura.modules', 'pura.helpers', 'pura.tests'], #find_packages(),
    classifiers=classifiers,
    zip_safe=False,
    entry_points={'console_scripts': ['pura = pura.__main__:main']}
)
