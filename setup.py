#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

from setuptools import setup, find_packages


def read(fname):
    buf = open(os.path.join(os.path.dirname(__file__), fname), 'rb').read()
    return buf.decode('utf8')


setup(name='partsy',
      version='0.1.dev1',
      description='A bill-of-materials to order list part database',
      long_description=read('README.md'),
      author='Marc Brinkmann',
      author_email='git@marcbrinkmann.de',
      url='https://github.com/mbr/partsy',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      install_requires=['click', 'pyyaml', 'voluptuous'],
      entry_points={
          'console_scripts': [
              'partsy = partsy.cli:cli',
          ],
      },
      classifiers=[
          'Programming Language :: Python :: 3',
      ])
