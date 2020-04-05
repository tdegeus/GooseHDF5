
from setuptools import setup
from setuptools import find_packages

import re

filepath = 'GooseHDF5/__init__.py'
__version__ = re.findall(r'__version__ = \'(.*)\'', open(filepath).read())[0]

setup(
    name='GooseHDF5',
    version=__version__,
    license='MIT',
    author='Tom de Geus',
    author_email='tom@geus.me',
    description='Wrapper around h5py',
    long_description='Wrapper around h5py',
    keywords='HDF5, h5py',
    url='https://github.com/tdegeus/GooseHDF5',
    packages=find_packages(),
    install_requires=['docopt>=0.6.2', 'h5py>=2.8.0'],
    entry_points={
        'console_scripts': [
            'G5check = GooseHDF5.cli.G5check:main',
            'G5compare = GooseHDF5.cli.G5compare:main',
            'G5list = GooseHDF5.cli.G5list:main',
            'G5print = GooseHDF5.cli.G5print:main',
            'G5repack = GooseHDF5.cli.G5repack:main',
            'G5repair = GooseHDF5.cli.G5repair:main']})
