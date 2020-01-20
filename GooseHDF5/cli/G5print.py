'''G5print
  Print datasets in a HDF5-file.

Usage:
  G5print [options] <source> <dataset>...

Arguments:
  <source>    HDF5-file.
  <dataset>   Path to the dataset.

Options:
  -r, --regex           Evaluate dataset name as a regular expression.
      --info            Print information: shape, dtype.
  -h, --help            Show help.
      --version         Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''


import warnings
warnings.filterwarnings("ignore")

import os
import re
import h5py
import docopt

from .. import __version__
from .. import getpaths


def main():

    args = docopt.docopt(__doc__, version=__version__)

    if not os.path.isfile(args['<source>']):
        print('File does not exist')
        sys.exit(1)

    with h5py.File(args['<source>'], 'r') as source:

        if args['--regex']:
            paths = getpaths(source)
            datasets = []
            for dataset in args['<dataset>']:
                datasets += [path for path in paths if re.match(dataset, path)]
        else:
            datasets = args['<dataset>']

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
            elif len(datasets) > 1:
                print(dataset)

            print(data[...])

            if len(datasets) > 1 and i < len(datasets) - 1:
                print('')

