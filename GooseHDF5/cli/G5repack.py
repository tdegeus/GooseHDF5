"""Read and write a HDF5 file.
    This allows a compacter file by removing features like extendible datasets.

:usage:

    G5repack [options] <source>...

:arguments:

    <source>
        HDF5-file.

:options:

    -c, --compress
        Apply compression (using the loss-less GZip algorithm).

    -f, --float
        Store doubles as floats.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
"""
import argparse
import os
import tempfile
import warnings

import h5py

from .. import copy_dataset
from .. import getdatasets
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
        parser.add_argument("-c", "--compress", required=False, action="store_true")
        parser.add_argument("-f", "--float", required=False, action="store_true")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source", nargs="+")
        args = parser.parse_args()

        tempname = next(tempfile._get_candidate_names())

        for filename in args.source:

            print(filename)

            check_isfile(filename)

            with h5py.File(filename, "r") as source:
                with h5py.File(tempname, "w") as tmp:
                    copy_dataset(
                        source, tmp, getdatasets(source), args.compress, args.float
                    )

            os.replace(tempname, filename)

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
