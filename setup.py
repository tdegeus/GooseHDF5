
import re

from setuptools import setup

# --------------------------------------------------------------------------------------------------

setup(
  name              = 'GooseHDF5',
  version           = '0.0.1',
  author            = 'Tom de Geus',
  author_email      = 'tom@geus.me',
  url               = 'https://github.com/tdegeus/GooseHDF5',
  keywords          = 'HDF5, h5py',
  description       = 'Wrapper around h5py',
  long_description  = '',
  license           = 'MIT',
  packages          = ['GooseHDF5'],
  scripts           = ['bin/G5check', 'bin/G5list', 'bin/G5repair', 'bin/G5find', 'bin/G5merge', 'bin/G5select'],
  install_requires  = ['docopt>=0.6.2', 'h5py>=2.8.0'],
      options={
        'build_scripts': {
            'executable': '/usr/bin/env python3',
        },
    },
)

# --------------------------------------------------------------------------------------------------
