'''G5list
    List datasets (or groups of datasets) in a HDF5-file.

Usage:
    G5list [options] [--fold ARG]... <source>

Arguments:
    <source>    HDF5-file.

Options:
    -f, --fold=ARG        Fold paths.
    -d, --max-depth=ARG   Maximum depth to display.
    -r, --root=ARG        Start a certain point in the path-tree. [default: /]
    -i, --info            Print information: shape, dtype.
    -l, --long            As above but will all attributes.
    -h, --help            Show help.
        --version         Show version.

(c - MIT) T.W.J. de Geus | tom@geus.me | www.geus.me | github.com/tdegeus/GooseHDF5
'''

from .. import getpaths
from .. import __version__
import docopt
import h5py
import os
import warnings
warnings.filterwarnings("ignore")


def check_isfile(fname):
    if not os.path.isfile(fname):
        raise IOError('"{0:s}" does not exist'.format(fname))


def print_plain(source, paths):
    r'''
Print the paths to all datasets (one per line).
    '''

    for path in paths:
        print(path)


def print_info(source, paths):
    r'''
Print the paths to all datasets (one per line), including type information.
    '''

    def has_attributes(lst):
        for i in lst:
            if i != '-' and i != '0':
                return True
        return False

    out = {
        'path': [],
        'size': [],
        'shape': [],
        'dtype': [],
        'attrs': []}

    for path in paths:
        if path in source:
            data = source[path]
            out['path'] += [path]
            out['size'] += [str(data.size)]
            out['shape'] += [str(data.shape)]
            out['dtype'] += [str(data.dtype)]
            out['attrs'] += [str(len(data.attrs))]
        else:
            out['path'] += [path]
            out['size'] += ['-']
            out['shape'] += ['-']
            out['dtype'] += ['-']
            out['attrs'] += ['-']

    width = {}
    for key in out:
        width[key] = max([len(i) for i in out[key]])
        width[key] = max(width[key], len(key))

    fmt = '{0:%ds} {1:%ds} {2:%ds} {3:%ds}' % \
        (width['path'], width['size'], width['shape'], width['dtype'])

    if has_attributes(out['attrs']):
        fmt += ' {4:%ds}' % width['attrs']

    print(fmt.format('path', 'size', 'shape', 'dtype', 'attrs'))
    print(fmt.format(
            '=' * width['path'],
            '=' * width['size'],
            '=' * width['shape'],
            '=' * width['dtype'],
            '=' * width['attrs']))

    for i in range(len(out['path'])):
        print(fmt.format(
            out['path'][i],
            out['size'][i],
            out['shape'][i],
            out['dtype'][i],
            out['attrs'][i]))


def print_attribute(source, paths):

    for path in paths:
        if path in source:

            data = source[path]

            print('"{0:s}"'.format(path))
            print('size = {0:s}, shape = {1:s}, dtype = {2:s}'.format(
                str(data.size), str(data.shape), str(data.dtype)))

            for key in data.attrs:
                print(key + ':')
                print(data.attrs[key])

            print('')

def main():
    r'''
Main function.
    '''

    args = docopt.docopt(__doc__, version=__version__)

    check_isfile(args['<source>'])

    with h5py.File(args['<source>'], 'r') as source:

        paths = getpaths(
            source,
            root=args['--root'],
            max_depth=args['--max-depth'],
            fold=args['--fold'])

        if args['--info']:
            print_info(source, paths)
        elif args['--long']:
            print_attribute(source, paths)
        else:
            print_plain(source, paths)
