#!/usr/bin/env python3
'''G5compare
  Compare two HDF5 files. If the function does not output anything all datasets are present in both
  files, and all the content of the datasets is equals

Usage:
  G5compare [options] [--renamed ARG]... <source> <other>

Arguments:
  <source>    HDF5-file.
  <other>     HDF5-file.

Options:
  -r, --renamed=ARG     Renamed paths, separated by a separator (see below).
  -s, --ifs=ARG         Separator used to separate renamed fields. [default: :]
  -h, --help            Show help.
      --version         Show version.

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

def not_equal(path):
  r'''
Support function for "check_dataset".
  '''

  print('!= {0:s}'.format(path))
  return False

# ==================================================================================================

def check_dataset(path, a, b):
  r'''
Check if the datasets (read outside) "a" and "b" are equal. If not print a message with the "path"
to the screen and return "False".
  '''

  if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number):
    if np.allclose(a, b):
      return True
    else:
      return not_equal(path)

  if a.size != b.size:
    return not_equal(path)

  if a.size == 1:
    if a[...] == b[...]:
      return True
    else:
      return not_equal(path)

  if list(a) == list(b):
    return True
  else:
    return not_equal(path)

  return True

# ==================================================================================================

def check_plain(source_name, other_name):
  r'''
Check all datasets (without allowing for renamed datasets).
  '''

  with h5py.File(source_name, 'r') as source:

    with h5py.File(other_name, 'r') as other:

      # check missing dataset
      for path in getpaths(source):
        if path not in other:
          print('-> {0:s}'.format(path))

      # check missing dataset
      for path in getpaths(other):
        if path not in source:
          print('<- {0:s}'.format(path))

      # check values
      for path in getpaths(source):
        if path in other:
          check_dataset(path, source[path][...], other[path][...])

# ==================================================================================================

def check_renamed(source, other, renamed):
  r'''
Check all datasets while allowing for renamed datasets.

renamed = [['source_name1', 'other_name1'], ['source_name2', 'other_name2'], ...]
  '''

  with h5py.File(source, 'r') as source:

    with h5py.File(other, 'r') as other:

      # get list of all datasets
      s2o = {i:i for i in list(getpaths(source))}
      o2s = {i:i for i in list(getpaths(other))}

      # rename
      for s, o in renamed:
        s2o[s] = o
        o2s[o] = s

      # check missing dataset
      for _, path in s2o.items():
        if path not in o2s:
          print('-> {0:s}'.format(path))

      # check missing dataset
      for _, path in o2s.items():
        if path not in s2o:
          print('<- {0:s}'.format(path))

      # check values
      for path in s2o:
        if s2o[path] in o2s:
          check_dataset(path, source[path][...], other[s2o[path]][...])

# ==================================================================================================

def main():

  # parse command-line options
  args = docopt.docopt(__doc__, version=__version__)

  # check that file exists
  check_isfile(args['<source>'])
  check_isfile(args['<other>'])

  # check without accounting for renamed field
  if len(args['--renamed']) == 0:
    check_plain(args['<source>'], args['<other>'])
    sys.exit(0)

  # unpack renaming
  renamed = [i.split(args['--ifs']) for i in args['--renamed']]

  # check with accounting for renamed field
  check_renamed(args['<source>'], args['<other>'], renamed)
