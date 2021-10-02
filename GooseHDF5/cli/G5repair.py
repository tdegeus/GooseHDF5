"""Extract readable data from a HDF5-file and copy it to a new HDF5-file.

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
"""
import argparse
import os
import sys
import warnings

import click
import h5py

from .. import copy
from .. import getdatapaths
from .. import verify
from .. import version

warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise OSError(f'"{fname}" does not exist')


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument("-f", "--force", required=False, action="store_true")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source")
        parser.add_argument("destination")
        args = parser.parse_args()

        check_isfile(args.source)

        if os.path.isfile(args.destination) and not args.force:
            if not click.confirm(f'File "{args.destination}" exists, continue [y/n]? '):
                sys.exit(1)

        with h5py.File(args.source, "r") as source:

            paths = verify(source, getdatapaths(source))

            with h5py.File(args.destination, "w") as dest:
                copy(source, dest, paths)

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
