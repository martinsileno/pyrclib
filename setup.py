from distutils.core import setup

#===============================================================================
# Installer script, run with:
# python setup.py install
#===============================================================================

setup(name='pyrclib',
      version='0.2.0b3',
      description='Python IRC bot framework',
      author='Marco Mugnai',
      author_email='martin@1way.it',
      license='MIT',
      url='http://trac.1way.it/',
      packages=['pyrclib'],
      classifiers=[
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Topic :: Communications :: IRC',
            'Topic :: Software Development :: Libraries :: Python Modules'
            ]
     )
