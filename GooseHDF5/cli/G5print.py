'''G5print
    Print datasets in a HDF5-file.

Usage:
    G5print [options] <source> [<dataset>...]

Arguments:
    <source>    HDF5-file.
    <dataset>   Path to the dataset.

Options:
    -r, --regex     Evaluate dataset name as a regular expression.
    -i, --info      Print information: shape, dtype.
    -a, --attrs     Print attributes.
        --no-data   Don't print data.
    -h, --help      Show help.
        --version   Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''


from .. import getpaths
from .. import __version__
import docopt
import h5py
import re
import os
import sys
import warnings
warnings.filterwarnings("ignore")


def main():

    args = docopt.docopt(__doc__, version=__version__)

    if not os.path.isfile(args['<source>']):
        print('File does not exist')
        sys.exit(1)

    with h5py.File(args['<source>'], 'r') as source:

        if len(args['<dataset>']) == 0:
            print_header = True
            datasets = list(getpaths(source))
        elif args['--regex']:
            print_header = True
            paths = getpaths(source)
            datasets = []
            for dataset in args['<dataset>']:
                datasets += [path for path in paths if re.match(dataset, path)]
        else:
            datasets = args['<dataset>']
            print_header = len(datasets) > 1

        for dataset in datasets:
            if dataset not in source:
                print('"{0:s}" not in "{1:s}"'.format(dataset, source.filename))

        for i, dataset in enumerate(datasets):

            data = source[dataset]

            if args['--info']:
                print('path = {0:s}, size = {1:s}, shape = {2:s}, dtype = {3:s}'.format(
                    dataset,
                    str(data.size),
                    str(data.shape),
                    str(data.dtype),
                ))
            elif print_header:
                print(dataset)

            if args['--attrs']:
                for key in data.attrs:
                    print(key + ' : ' + str(data.attrs[key]))

            if not args['--no-data']:
                print(data[...])

            if len(datasets) > 1 and i < len(datasets) - 1:
                print('')
