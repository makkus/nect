#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    'Click>=6.0',
    'stevedore>=1.18.0',
    'pyyaml'

]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='nect',
    version='0.1.0',
    description="List construction/selection/connection framework.",
    long_description=readme + '\n\n' + history,
    author="Markus Binsteiner",
    author_email='makkus@posteo.de',
    url='https://github.com/makkus/nect',
    packages=[
        'nect',
    ],
    package_dir={'nect':
                 'nect'},
    entry_points={
        'console_scripts': [
            'nect=nect.cli:main'
        ],
        'nect.nects': [
            'static-list=nect.nects.core:StaticList',
            'sort=nect.nects.core:Sort',
            'shell-pipe=nect.nects.core:ShellPipe',
            'shell=nect.nects.core:Shell',
            'dummy-list=nect.nects.core:DummyList',
            'index=nect.nects.core:PositionListFilter',
            'executables=nect.nects.apps:Executables',
            'dict=nect.nects.core:Dict'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="GNU General Public License v3",
    zip_safe=False,
    keywords='nect',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
