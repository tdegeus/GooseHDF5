#!/usr/bin/env python3
'''G5list
  List datasets (or groups of datasets) in a HDF5-file.

Usage:
  G5list [options] [--fold ARG]... <source>

Arguments:
  <source>    HDF5-file.

Options:
  -f, --fold=ARG        Fold paths.
  -d, --max-depth=ARG   Maximum depth to display.
  -r, --root=ARG        Start a certain point in the path-tree. [default: /]
      --info            Print information: shape, dtype.
  -h, --help            Show help.
      --version         Show version.

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

def print_plain(source, paths):
  r'''
Print the paths to all datasets (one per line)
  '''

  for path in paths:
    print(path)

# ==================================================================================================

def print_info(source, paths):
  r'''
Print the paths to all datasets (one per line), including type information.
  '''

  out = {
    'path'  : [],
    'size'  : [],
    'shape' : [],
    'dtype' : [],
  }

  for path in paths:
    if path in source:
      data = source[path]
      out['path' ] += [path]
      out['size' ] += [str(data.size)]
      out['shape'] += [str(data.shape)]
      out['dtype'] += [str(data.dtype)]
    else:
      out['path' ] += [path]
      out['size' ] += ['-']
      out['shape'] += ['-']
      out['dtype'] += ['-']

  width = {}
  for key in out:
    width[key] = max([len(i) for i in out[key]])
    width[key] = max(width[key], len(key))

  fmt = '{0:%ds} {1:%ds} {2:%ds} {3:%ds}' % (width['path'], width['size'], width['shape'], width['dtype'])

  print(fmt.format('path', 'size', 'shape', 'dtype'))
  print(fmt.format('='*width['path'], '='*width['size'], '='*width['shape'], '='*width['dtype']))

  for i in range(len(out['path'])):
    print(fmt.format(out['path'][i], out['size'][i], out['shape'][i], out['dtype'][i]))

# ==================================================================================================

def main():

  # parse command-line options
  args = docopt.docopt(__doc__, version=__version__)

  # check that file exists
  check_isfile(args['<source>'])

  # open file and read
  with h5py.File(args['<source>'], 'r') as source:

    # get iterator to data-sets
    paths = getpaths(source,
      root      = args['--root'],
      max_depth = args['--max-depth'],
      fold      = args['--fold'])

    # print
    if args['--info']:
      print_info(source, paths)
    else:
      print_plain(source, paths)
