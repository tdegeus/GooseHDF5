'''G5repack
    Read and write a HDF5 file, to write it more efficiently by removing features like
    extendible datasets.

Usage:
    G5repack [options] <source>...

Arguments:
    <source>    HDF5-file.

Options:
    -c, --compress  Apply compression (using the loss-less GZip algorithm).
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

def copy_dataset(old, new, path, compress):

    data = old[path][...]

    if data.size == 1 or not compress:
        new[path] = old[path][...]
    else:
        dset = new.create_dataset(path, data.shape, compression="gzip")
        dset[:] = data

    for key in old[path].attrs:
        new[path].attrs[key] = old[path].attrs[key]

def main():

    args = docopt.docopt(__doc__, version=__version__)
    tempname = next(tempfile._get_candidate_names())

    for filename in args['<source>']:

        print(filename)

        check_isfile(filename)

        with h5py.File(filename, 'r') as source:
            with h5py.File(tempname, 'w') as tmp:
                for path in getpaths(source):
                    copy_dataset(source, tmp, path, args['--compress'])

        os.replace(tempname, filename)
