#!/usr/bin/env python3
'''G5check
  Try reading datasets. In case of reading failure the path is printed (otherwise nothing is
  printed).

Usage:
  G5check <source> [options]

Arguments:
  <source>        HDF5-file.

Options:
  -b, --basic     Only try getting a list of datasets, skip trying to read them.
  -h, --help      Show help.
      --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

# ==================================================================================================

# temporary fix: suppress warning from h5py
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import sys
import os
import re
import h5py
import docopt

from .. import *

# ==================================================================================================

def check_isfile(fname):
  r'''
Check if a file exists, quit otherwise.
  '''

  if not os.path.isfile(fname):
    raise IOError('"{0:s}" does not exist'.format(fname))

# ==================================================================================================

def read(filename, check):
  r'''
Read (and check) all datasets
  '''

  with h5py.File(filename, 'r') as source:

    paths = getdatasets(source)

    if check:
      verify(source, paths, error=True)

# ==================================================================================================

def main():

  # parse command-line options
  args = docopt.docopt(__doc__,version='0.0.2')

  # check that file exists
  check_isfile(args['<source>'])

  read(args['<source>'], not args['--basic'])

  # read datasets
  try:
    read(args['<source>'], not args['--basic'])
  except:
    print(args['<source>'])
