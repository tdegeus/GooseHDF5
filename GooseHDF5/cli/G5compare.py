'''G5compare
  Compare two HDF5 files. If the function does not output anything all datasets are present in both
  files, and all the content of the datasets is equal.
  Each output line corresponds to a mismatch between the files.

Usage:
  G5compare [options] [--renamed ARG]... <source> <other>

Arguments:
  <source>    HDF5-file.
  <other>     HDF5-file.

Options:
  -t, --dtype           Verify that the type of the datasets match.
  -r, --renamed=ARG     Renamed paths, separated by a separator (see below).
  -s, --ifs=ARG         Separator used to separate renamed fields. [default: :]
  -h, --help            Show help.
      --version         Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

from .. import equal
from .. import getpaths
from .. import __version__
import docopt
import h5py
import os
import sys
import numpy as np
import warnings
warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))


def check_dataset(source, dest, source_dataset, dest_dataset, check_dtype):
    r'''
Check if the datasets (read outside) "a" and "b" are equal. If not print a message with the "path"
to the screen and return "False".
    '''

    if not equal(source, dest, source_dataset, dest_dataset):
        print(' !=  {0:s}'.format(source_dataset))
        return False

    if check_dtype:
        if source[source_dataset].dtype != dest[dest_dataset].dtype:
            print('type {0:s}'.format(source_dataset))
            return False

    return True


def _check_plain(source, other, check_dtype):
    r'''
Support function for "check_plain."
    '''

    for path in getpaths(source):
        if path not in other:
            print('-> {0:s}'.format(path))

    for path in getpaths(other):
        if path not in source:
            print('<- {0:s}'.format(path))

    for path in getpaths(source):
        if path in other:
            check_dataset(source, other, path, path, check_dtype)


def check_plain(source_name, other_name, check_dtype):
    r'''
Check all datasets (without allowing for renamed datasets).
    '''
    with h5py.File(source_name, 'r') as source:
        with h5py.File(other_name, 'r') as other:
            _check_plain(source, other, check_dtype)


def _check_renamed(source, other, renamed, check_dtype):
    r'''
Support function for "check_renamed."
    '''

    s2o = {i: i for i in list(getpaths(source))}
    o2s = {i: i for i in list(getpaths(other))}

    for s, o in renamed:
        s2o[s] = o
        o2s[o] = s

    for _, path in s2o.items():
        if path not in o2s:
            print(' ->  {0:s}'.format(path))

    for _, path in o2s.items():
        if path not in s2o:
            print(' <-  {0:s}'.format(path))

    for new_path, path in s2o.items():
        if new_path in o2s:
            check_dataset(source, other, path, new_path, check_dtype)


def check_renamed(source_name, other_name, renamed, check_dtype):
    r'''
Check all datasets while allowing for renamed datasets.
renamed = [['source_name1', 'other_name1'], ['source_name2', 'other_name2'], ...]
    '''

    with h5py.File(source_name, 'r') as source:
        with h5py.File(other_name, 'r') as other:
            _check_renamed(source, other, renamed, check_dtype)


def main():
    r'''
Main function.
    '''

    args = docopt.docopt(__doc__, version=__version__)

    check_isfile(args['<source>'])
    check_isfile(args['<other>'])

    if len(args['--renamed']) == 0:
        check_plain(args['<source>'], args['<other>'], args['--dtype'])
        sys.exit(0)

    renamed = [i.split(args['--ifs']) for i in args['--renamed']]

    check_renamed(args['<source>'], args['<other>'], renamed, args['--dtype'])
