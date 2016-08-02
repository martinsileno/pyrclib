from setuptools import setup

import pyrclib

# ==============================================================================
# Installer script, run with:
# python setup.py install
# ==============================================================================

setup(name='pyrclib',
      version=pyrclib.__version__,
      description='Python IRC bot framework',
      author='Martin Sileno',
      author_email='martin@1way.it',
      license='MIT',
      url='https://github.com/martinsileno/pyrclib',
      packages=['example', 'pyrclib'],
      test_suite='pyrclib.tests',
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ])
