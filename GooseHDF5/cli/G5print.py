"""Print datasets in a HDF5-file.

:usage:

    G5print [options] <source> [<dataset>...]

:arguments:

    <source>
        HDF5-file.

    <dataset>
        Path to the dataset.

:options:

    -f, --fold=ARG
        Fold paths. Can be repeated.

    -d, --max-depth=ARG
        Maximum depth to display.

    -r, --root=ARG
        Start a certain point in the path-tree. [default: /]

    --regex
        Evaluate dataset name as a regular expression.

    -i, --info
        Print information: shape, dtype.

    -a, --attrs
        Print attributes.

    --no-data
        Don't print data.

    --full
        Print full array.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
"""
import argparse
import os
import re
import sys
import warnings

import h5py
import numpy as np

from .. import getdatasets
from .. import getgroups
from .. import version

warnings.filterwarnings("ignore")


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument("-f", "--fold", required=False, action="append")
        parser.add_argument("-d", "--max-depth", required=False, type=int)
        parser.add_argument("-r", "--root", required=False, default="/")
        parser.add_argument("--regex", required=False, action="store_true")
        parser.add_argument("-i", "--info", required=False, action="store_true")
        parser.add_argument("-a", "--attrs", required=False, action="store_true")
        parser.add_argument("--full", required=False, action="store_true")
        parser.add_argument("--no-data", required=False, action="store_true")
        parser.add_argument("-v", "--version", action="version", version=version)
        parser.add_argument("source")
        parser.add_argument("dataset", nargs="*")
        args = parser.parse_args()

        if not os.path.isfile(args.source):
            print("File does not exist")
            return 1

        if args.full:
            np.set_printoptions(threshold=sys.maxsize)

        with h5py.File(args.source, "r") as source:

            if len(args.dataset) == 0:
                print_header = True
                datasets = list(
                    getdatasets(
                        source, root=args.root, max_depth=args.max_depth, fold=args.fold
                    )
                )
                datasets += list(getgroups(source, has_attrs=True))
                datasets = sorted(datasets)
            elif args.regex:
                print_header = True
                paths = list(
                    getdatasets(
                        source, root=args.root, max_depth=args.max_depth, fold=args.fold
                    )
                )
                paths += list(getgroups(source, has_attrs=True))
                datasets = []
                for dataset in args.dataset:
                    datasets += [path for path in paths if re.match(dataset, path)]
                datasets = sorted(datasets)
            else:
                datasets = args.dataset
                print_header = len(datasets) > 1

            for dataset in datasets:
                if dataset not in source:
                    print(f'"{dataset}" not in "{source.filename}"')
                    return 1

            for i, dataset in enumerate(datasets):

                data = source[dataset]

                if args.info:
                    if isinstance(data, h5py.Dataset):
                        print(
                            "path = {:s}, size = {:s}, shape = {:s}, dtype = {:s}".format(
                                dataset,
                                str(data.size),
                                str(data.shape),
                                str(data.dtype),
                            )
                        )
                    else:
                        print(f"path = {dataset}")
                elif print_header:
                    print(dataset)

                for key in data.attrs:
                    print(key + " : " + str(data.attrs[key]))

                if isinstance(data, h5py.Dataset):
                    if not args.no_data:
                        print(data[...])

                if len(datasets) > 1 and i < len(datasets) - 1:
                    print("")

    except Exception as e:

        print(e)
        return 1


if __name__ == "__main__":

    main()
