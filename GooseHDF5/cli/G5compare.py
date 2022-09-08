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

    --shallow
        Only check for the presence of datasets and attributes. Do not check their values.

    -r, --renamed=ARG
        Renamed paths: this option takes two arguments, one for ``source`` and one for ``other``.
        It can repeated, e.g. ``G5compare a.h5 b.h5 -r /a /b  -r /c /d``

    -c, --color=STR (none, dark)
        Color theme.
        default: dark.

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
import numpy as np
from prettytable import PLAIN_COLUMNS
from prettytable import PrettyTable
from termcolor import colored

from .. import compare_rename
from .. import version

warnings.filterwarnings("ignore")


def main():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-c", "--color", type=str, default="dark")
    parser.add_argument("-t", "--dtype", required=False, action="store_true")
    parser.add_argument("--shallow", action="store_true")
    parser.add_argument("-r", "--renamed", required=False, nargs=2, action="append")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("a")
    parser.add_argument("b")
    args = parser.parse_args()

    for filepath in [args.a, args.b]:
        if not os.path.isfile(filepath):
            raise OSError(f'"{filepath}" does not exist')

    with h5py.File(args.a, "r") as a, h5py.File(args.b, "r") as b:
        comp, r_a, r_b = compare_rename(
            a, b, rename=args.renamed, matching_dtype=args.dtype, shallow=args.shallow
        )

    def print_path(path):
        if len(os.path.relpath(path).split("..")) < 3:
            return os.path.relpath(path)
        return os.path.abspath(path)

    def truncate_path(path, n):

        if len(path) <= n:
            return path

        path = os.path.abspath(path)
        path = path.split(os.sep)
        if len(path[0]) == 0:
            path[0] = os.sep
        l = np.array([len(i) for i in path])
        s = np.zeros(len(path), dtype=bool)
        s[0] = True
        s[-1] = True

        for i in range(1, len(path) - 1)[::-1]:
            s[i] = True
            if np.sum(l[s]) + np.sum(s) + 3 >= n:
                s[i] = False
                break

        if np.sum(s) != len(path):
            path = [path[0], "..."] + np.array(path)[s][1:].tolist()

        return os.path.join(*path)

    def def_row(arg):
        if arg[1] == "!=":
            return [
                colored(arg[0], "cyan", attrs=["bold"]),
                arg[1],
                colored(arg[2], "cyan", attrs=["bold"]),
            ]
        if arg[1] == "->":
            return [colored(arg[0], "red", attrs=["bold", "concealed"]), arg[1], ""]
        if arg[1] == "<-":
            return ["", arg[1], colored(arg[2], "green", attrs=["bold"])]

    out = PrettyTable()
    out.set_style(PLAIN_COLUMNS)
    out.align = "l"
    n = 0

    for key in comp:
        if key != "==":
            for item in comp[key]:
                out.add_row(def_row([item, key, item]))
                n = max(n, len(item))

    for path_a, path_b in zip(r_a["!="], r_b["!="]):
        out.add_row(def_row([path_a, "!=", path_b]))
        n = max(n, len(path_a))

    file_a = print_path(args.a)
    file_b = print_path(args.b)
    out.field_names = [truncate_path(file_a, n), "", truncate_path(file_b, n)]

    print(out.get_string())


if __name__ == "__main__":

    main()
