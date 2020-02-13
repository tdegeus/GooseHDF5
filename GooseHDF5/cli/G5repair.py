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

from .. import getdatasets
from .. import copydatasets
from .. import verify
from .. import __version__
import docopt
import h5py
import os
import sys
import warnings
warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))


def main():

    args = docopt.docopt(__doc__, version=__version__)

    check_isfile(args['<source>'])

    if os.path.isfile(args['<destination>']) and not args['--force']:
        if not click.confirm('File "{0:s}" exists, continue [y/n]? '.format(args['<destination>'])):
            sys.exit(1)

    with h5py.File(args['<source>'], 'r') as source:

        paths = verify(source, getdatasets(source))

        with h5py.File(args['<destination>'], 'w') as dest:
            copydatasets(source, dest, paths)
