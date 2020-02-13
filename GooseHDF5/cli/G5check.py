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

from .. import verify
from .. import getdatasets
from .. import __version__
import docopt
import h5py
import os
import warnings
warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))


def read(filename, check):
    r'''
Read (and check) all datasets.
    '''

    with h5py.File(filename, 'r') as source:

        paths = getdatasets(source)

        if check:
            verify(source, paths, error=True)


def main():
    r'''
Main function.
    '''

    args = docopt.docopt(__doc__, version=__version__)

    check_isfile(args['<source>'])

    read(args['<source>'], not args['--basic'])

    try:
        read(args['<source>'], not args['--basic'])
    except:
        print(args['<source>'])
