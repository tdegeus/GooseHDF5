"""Compare two HDF5 files.
    If the function does not output anything all datasets are present in both files,
    and all the content of the datasets is equal.
    Each output line corresponds to a mismatch between the files.

:usage:

    G5compare [options] <source> <other>

:arguments:

    <source>
        HDF5-file.

    <other>
        HDF5-file.

:options:

    -t, --dtype
        Verify that the type of the datasets match.

    -r, --renamed=ARG
        Renamed paths: this option takes two arguments, one for ``source`` and one for ``other``.
        It can repeated, e.g. ``G5compare a.h5 b.h5 -r /a /b  -r /c /d``

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

from .. import equal
from .. import getdatapaths
from .. import version

warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise OSError(f'"{fname}" does not exist')


def check_dataset(source, dest, source_dataset, dest_dataset, check_dtype):
    r"""
    Check if the datasets (read outside) "a" and "b" are equal.
    If not print a message with the "path" to the screen and return "False".
    """

    if not equal(source, dest, source_dataset, dest_dataset):
        print(f" !=  {source_dataset}")
        return False

    if check_dtype:
        if source[source_dataset].dtype != dest[dest_dataset].dtype:
            print(f"type {source_dataset}")
            return False

    return True


def _check_plain(source, other, check_dtype):
    r"""
    Support function for "check_plain."
    """

    for path in getdatapaths(source):
        if path not in other:
            print(f"-> {path}")

    for path in getdatapaths(other):
        if path not in source:
            print(f"<- {path}")

    for path in getdatapaths(source):
        if path in other:
            check_dataset(source, other, path, path, check_dtype)


def check_plain(source_name, other_name, check_dtype):
    r"""
    Check all datasets (without allowing for renamed datasets).
    """
    with h5py.File(source_name, "r") as source:
        with h5py.File(other_name, "r") as other:
            _check_plain(source, other, check_dtype)


def _check_renamed(source, other, renamed, check_dtype):
    r"""
    Support function for "check_renamed."
    """

    s2o = {i: i for i in list(getdatapaths(source))}
    o2s = {i: i for i in list(getdatapaths(other))}

    for s, o in renamed:
        s2o[s] = o
        o2s[o] = s

    for _, path in s2o.items():
        if path not in o2s:
            print(f" ->  {path}")

    for _, path in o2s.items():
        if path not in s2o:
            print(f" <-  {path}")

    for new_path, path in s2o.items():
        if new_path in o2s:
            check_dataset(source, other, path, new_path, check_dtype)


def check_renamed(source_name, other_name, renamed, check_dtype):
    r"""
    Check all datasets while allowing for renamed datasets.
    renamed = [['source_name1', 'other_name1'], ['source_name2', 'other_name2'], ...]
    """

    with h5py.File(source_name, "r") as source:
        with h5py.File(other_name, "r") as other:
            _check_renamed(source, other, renamed, check_dtype)


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument("-t", "--dtype", required=False, action="store_true")
        parser.add_argument("-r", "--renamed", required=False, nargs=2, action="append")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source")
        parser.add_argument("other")
        args = parser.parse_args()

        check_isfile(args.source)
        check_isfile(args.other)

        if not args.renamed:
            check_plain(args.source, args.other, args.dtype)
            return 0

        check_renamed(args.source, args.other, args.renamed, args.dtype)

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
