"""List datasets (or groups of datasets) in a HDF5-file.

:usage:

    G5list [options] <source>

:arguments:

    <source>
        HDF5-file.

:options:

    -f, --fold=ARG
        Fold paths. Can be repeated.

    -d, --max-depth=ARG
        Maximum depth to display.

    -r, --root=ARG
        Start a certain point in the path-tree. [default: /]

    -i, --info
        Print information: shape, dtype.

    -l, --long
        As above but will all attributes.

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

from .. import getdatasets
from .. import getgroups
from .. import version

warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise OSError(f'"{fname}" does not exist')


def print_plain(source, paths):
    r"""
    Print the paths to all datasets (one per line).
    """

    for path in paths:
        print(path)


def print_info(source, paths):
    r"""
    Print the paths to all datasets (one per line), including type information.
    """

    def has_attributes(lst):
        for i in lst:
            if i != "-" and i != "0":
                return True
        return False

    out = {"path": [], "size": [], "shape": [], "dtype": [], "attrs": []}

    for path in paths:
        if path in source:
            data = source[path]
            out["path"] += [path]
            out["attrs"] += [str(len(data.attrs))]
            if isinstance(data, h5py.Dataset):
                out["size"] += [str(data.size)]
                out["shape"] += [str(data.shape)]
                out["dtype"] += [str(data.dtype)]
            else:
                out["size"] += ["-"]
                out["shape"] += ["-"]
                out["dtype"] += ["-"]
        else:
            out["path"] += [path]
            out["size"] += ["-"]
            out["shape"] += ["-"]
            out["dtype"] += ["-"]
            out["attrs"] += ["-"]

    width = {}
    for key in out:
        width[key] = max(len(i) for i in out[key])
        width[key] = max(width[key], len(key))

    fmt = "{0:%ds} {1:%ds} {2:%ds} {3:%ds}" % (
        width["path"],
        width["size"],
        width["shape"],
        width["dtype"],
    )

    if has_attributes(out["attrs"]):
        fmt += " {4:%ds}" % width["attrs"]

    print(fmt.format("path", "size", "shape", "dtype", "attrs"))
    print(
        fmt.format(
            "=" * width["path"],
            "=" * width["size"],
            "=" * width["shape"],
            "=" * width["dtype"],
            "=" * width["attrs"],
        )
    )

    for i in range(len(out["path"])):
        print(
            fmt.format(
                out["path"][i],
                out["size"][i],
                out["shape"][i],
                out["dtype"][i],
                out["attrs"][i],
            )
        )


def print_attribute(source, paths):

    for path in paths:
        if path in source:

            data = source[path]

            print(f'"{path}"')

            if isinstance(data, h5py.Dataset):
                print(
                    "- prop: size = {:s}, shape = {:s}, dtype = {:s}".format(
                        str(data.size), str(data.shape), str(data.dtype)
                    )
                )

            for key in data.attrs:
                print("- attr: " + key + " = ")
                print("        " + str(data.attrs[key]))

            print("")


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument("-f", "--fold", required=False, action="append")
        parser.add_argument("-d", "--max-depth", required=False, type=int)
        parser.add_argument("-r", "--root", required=False, default="/")
        parser.add_argument("-i", "--info", required=False, action="store_true")
        parser.add_argument("-l", "--long", required=False, action="store_true")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source")
        args = parser.parse_args()

        check_isfile(args.source)

        with h5py.File(args.source, "r") as source:

            # Print datasets

            paths = list(
                getdatasets(
                    source, root=args.root, max_depth=args.max_depth, fold=args.fold
                )
            )
            paths += list(getgroups(source, root=args.root, has_attrs=True))
            paths = sorted(paths)

            if args.info:
                print_info(source, paths)
            elif args.long:
                print_attribute(source, paths)
            else:
                print_plain(source, paths)

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
