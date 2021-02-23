'''G5print
    Print datasets in a HDF5-file.

:usage:

    G5print [options] <source> [<dataset>...]

:arguments:

    <source>
        HDF5-file.

    <dataset>
        Path to the dataset.

:options:

    -r, --regex
        Evaluate dataset name as a regular expression.

    -i, --info
        Print information: shape, dtype.

    -a, --attrs
        Print attributes.

    --no-data
        Don't print data.

    -h, --help
        Show help.

    --version
        Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''


from .. import getpaths
from .. import version
import argparse
import h5py
import re
import os
import sys
import warnings
warnings.filterwarnings("ignore")


def main():

    try:

        class Parser(argparse.ArgumentParser):
            def print_help(self):
                print(__doc__)

        parser = Parser()
        parser.add_argument('-r', '--regex', required=False, action='store_true')
        parser.add_argument('-i', '--info', required=False, action='store_true')
        parser.add_argument('-a', '--attrs', required=False, action='store_true')
        parser.add_argument(      '--no-data', required=False, action='store_true')
        parser.add_argument('-v', '--version', action='version', version=version)
        parser.add_argument('source')
        parser.add_argument('dataset', nargs='*')
        args = parser.parse_args()

        if not os.path.isfile(args.source):
            print('File does not exist')
            return 1

        with h5py.File(args.source, 'r') as source:

            if len(args.dataset) == 0:
                print_header = True
                datasets = list(getpaths(source))
            elif args.regex:
                print_header = True
                paths = getpaths(source)
                datasets = []
                for dataset in args.dataset:
                    datasets += [path for path in paths if re.match(dataset, path)]
            else:
                datasets = args.dataset
                print_header = len(datasets) > 1

            for dataset in datasets:
                if dataset not in source:
                    print('"{0:s}" not in "{1:s}"'.format(dataset, source.filename))
                    return 1

            for i, dataset in enumerate(datasets):

                data = source[dataset]

                if args.info:
                    print('path = {0:s}, size = {1:s}, shape = {2:s}, dtype = {3:s}'.format(
                        dataset,
                        str(data.size),
                        str(data.shape),
                        str(data.dtype),
                    ))
                elif print_header:
                    print(dataset)

                if args.attrs:
                    for key in data.attrs:
                        print(key + ' : ' + str(data.attrs[key]))

                if not args.no_data:
                    print(data[...])

                if len(datasets) > 1 and i < len(datasets) - 1:
                    print('')

    except Exception as e:

        print(e)
        return 1

if __name__ == '__main__':

    main()

