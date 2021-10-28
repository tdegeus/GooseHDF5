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

from .. import compare_rename
from .. import version

warnings.filterwarnings("ignore")


def theme(theme=None):
    r"""
    Return dictionary of colors.

    .. code-block:: python

        {
            'new' : '...',
            'overwrite' : '...',
            'skip' : '...',
            'bright' : '...',
        }

    :param str theme: Select color-theme.

    :rtype: dict
    """

    if theme == "dark":
        return {
            "->": "9;31",
            "<-": "1;32",
            "!=": "1;31",
        }

    return {
        "->": "",
        "<-": "",
        "!=": "",
    }


class String:
    r"""
    Rich string.

    .. note::

        All options are attributes, that can be modified at all times.

    .. note::

        Available methods:

        *   ``A.format()`` :  Formatted string.
        *   ``str(A)`` : Unformatted string.
        *   ``A.isnumeric()`` : Return if the "data" is numeric.
        *   ``int(A)`` : Dummy integer.
        *   ``float(A)`` : Dummy float.

    :type data: str, None
    :param data: The data.

    :type width: None, int
    :param width: Print width (formatted print only).

    :type color: None, str
    :param color: Print color, e.g. "1;32" for bold green (formatted print only).

    :type align: ``'<'``, ``'>'``
    :param align: Print alignment (formatted print only).

    :type dummy: 0, int, float
    :param dummy: Dummy numerical value.

    :methods:


    """

    def __init__(self, data, width=None, align="<", color=None, dummy=0):

        self.data = data
        self.width = width
        self.color = color
        self.align = align
        self.dummy = dummy

    def format(self):
        r"""
        Return formatted string: align/width/color are applied.
        """

        if self.width and self.color:
            fmt = "\x1b[{color:s}m{{0:{align:s}{width:d}.{width:d}s}}\x1b[0m".format(
                **self.__dict__
            )
        elif self.width:
            fmt = "{{0:{align:s}{width:d}.{width:d}s}}".format(**self.__dict__)
        elif self.color:
            fmt = "\x1b[{color:s}m{{0:{align:s}s}}\x1b[0m".format(**self.__dict__)
        else:
            fmt = "{{0:{align:s}s}}".format(**self.__dict__)

        return fmt.format(str(self))

    def isnumeric(self):
        r"""
        Return if the "data" is numeric : always zero for this class.
        """
        return False

    def __str__(self):
        return str(self.data)

    def __int__(self):
        return int(self.dummy)

    def __float__(self):
        return float(self.dummy)

    def __repr__(self):
        return str(self)

    def __lt__(self, other):
        return str(self) < str(other)


def main():
    class Parser(argparse.ArgumentParser):
        def print_help(self):
            print(__doc__)

    parser = Parser()
    parser.add_argument("-c", "--color", type=str, default="dark")
    parser.add_argument("-t", "--dtype", required=False, action="store_true")
    parser.add_argument("-r", "--renamed", required=False, nargs=2, action="append")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("a")
    parser.add_argument("b")
    args = parser.parse_args()

    color = theme(args.color)

    for filepath in [args.a, args.b]:
        if not os.path.isfile(filepath):
            raise OSError(f'"{filepath}" does not exist')

    with h5py.File(args.a, "r") as a, h5py.File(args.b, "r") as b:
        comp, r_a, r_b = compare_rename(a, b, rename=args.renamed, matching_dtype=args.dtype)

    n = 0
    for key in comp:
        if key != "==":
            for item in comp[key]:
                n = max(n, len(item))

    for item in r_a["=="]:
        n = max(n, len(item))

    paths = []
    for key in comp:
        if key != "==":
            for item in comp[key]:
                paths += [(item, item, key)]

    for path_a, path_b in zip(r_a["!="], r_b["!="]):
        paths += [(path_a, path_b, "!=")]

    paths = sorted(paths, key=lambda v: v[0])

    for path_a, path_b, key in paths:
        if key == "<-":
            print(" " * n + " <- " + String(path_b, color=color["<-"]).format())
        elif key == "->":
            print(String(path_a, color=color["->"], width=n).format() + " -> ")
        else:
            print(
                String(path_a, color=color["!="], width=n).format()
                + " != "
                + String(path_b, color=color["!="], width=n).format()
            )


if __name__ == "__main__":

    main()
