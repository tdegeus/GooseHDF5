'''G5repair
    Extract readable data from a HDF5-file and copy it to a new HDF5-file.

:usage:

    G5repair [options] <source> <destination>

:arguments:

    <source>
        Source HDF5-file, possibly containing corrupted data.

    <destination>
        Destination HDF5-file.

:options:

    -f, --force
        Force continuation, overwrite existing files.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

from .. import getdatasets
from .. import copydatasets
from .. import verify
from .. import version
import argparse
import h5py
import os
import sys
import warnings
warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-f', '--force', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('source')
        parser.add_argument('destination')
        args = parser.parse_args()

        check_isfile(args.source)

        if os.path.isfile(args.destination) and not args.force:
            if not click.confirm('File "{0:s}" exists, continue [y/n]? '.format(args.destination)):
                sys.exit(1)

        with h5py.File(args.source, 'r') as source:

            paths = verify(source, getdatasets(source))

            with h5py.File(args.destination, 'w') as dest:
                copydatasets(source, dest, paths)

    except Exception as e:

        print(e)
        return 1


if __name__ == '__main__':

    main()
