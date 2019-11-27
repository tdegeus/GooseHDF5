#!/usr/bin/env python3
'''G5repair
  Extract readable data from a HDF5-file and copy it to a new HDF5-file.

Usage:
  G5repair [options] <source> <destination>

Arguments:
  <source>        Source HDF5-file, possibly containing corrupted data.
  <destination>   Destination HDF5-file.

Options:
  -f, --force     Force continuation, overwrite existing files.
  -h, --help      Show help.
      --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

# ==================================================================================================

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import os
import re
import h5py
import docopt
import pkg_resources

__version__ = pkg_resources.require("GooseHDF5")[0].version

from .. import *

# ==================================================================================================

def check_isfile(fname):
  r'''
Check if a file exists, quit otherwise.
  '''

  if not os.path.isfile(fname):
    raise IOError('"{0:s}" does not exist'.format(fname))

# ==================================================================================================

def main():

  # parse command-line options
  args = docopt.docopt(__doc__, version=__version__)

  # check that file exists
  check_isfile(args['<source>'])

  # check to overwrite
  if os.path.isfile(args['<destination>']) and not args['--force']:
    if not click.confirm('File "{0:s}" already exists, continue [y/n]? '.format(args['<destination>'])):
      sys.exit(1)

  # read the 'damaged' file
  with h5py.File(args['<source>'], 'r') as source:

    # get paths that can be read
    paths = verify(source, getdatasets(source))

    # copy datasets
    with h5py.File(args['<destination>'], 'w') as dest:
      copydatasets(source, dest, paths)
