from setuptools import setup

# ==============================================================================
# Installer script, run with:
# python setup.py install
# ==============================================================================

setup(name='pyrclib',
      version='0.2.5',
      description='Python IRC bot framework',
      author='Martin Sileno',
      author_email='martin@1way.it',
      license='MIT',
      url='https://github.com/martinsileno/pyrclib',
      packages=['example', 'pyrclib'],
      classifiers=[
          'Intended Audience :: Developers',
          'Programming Language :: Python',
          'Topic :: Software Development :: Libraries :: Python Modules',
      ])
