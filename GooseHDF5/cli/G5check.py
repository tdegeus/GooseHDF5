"""Try reading datasets.
    In case of reading failure the path is printed (otherwise nothing is printed).

:usage:

    G5check [options] <source>

:arguments:

    <source>
        HDF5-file.

:options:

    -b, --basic
        Only try getting a list of datasets, skip trying to read them.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
"""
import argparse
import os
import warnings

import h5py

from .. import getdatapaths
from .. import verify
from .. import version

warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise OSError(f'"{fname}" does not exist')


def read(filename, check):

    with h5py.File(filename, "r") as source:
        paths = getdatapaths(source)
        if check:
            verify(source, paths, error=True)


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument("-b", "--basic", required=False, action="store_true")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source")
        args = parser.parse_args()

        check_isfile(args.source)
        read(args.source, not args.basic)

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
