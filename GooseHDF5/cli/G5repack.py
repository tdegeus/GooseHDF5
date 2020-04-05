'''G5repack
    Read and write a HDF5 file, to write it more efficiently by removing features like
    extendible datasets.

Usage:
    G5repack [options] <source>...

Arguments:
    <source>    HDF5-file.

Options:
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

from .. import getpaths
from .. import __version__
import docopt
import h5py
import os
import tempfile
import warnings
warnings.filterwarnings("ignore")

def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))

def main():

    args = docopt.docopt(__doc__, version=__version__)
    tempname = next(tempfile._get_candidate_names())

    for filename in args['<source>']:

        print(filename)

        check_isfile(filename)

        with h5py.File(filename, 'r') as source:
            with h5py.File(tempname, 'w') as tmp:
                for path in getpaths(source):
                    tmp[path] = source[path][...]

        os.replace(tempname, filename)
