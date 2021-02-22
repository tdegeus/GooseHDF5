import h5py
import numpy as np
import warnings

from ._version import *

warnings.filterwarnings("ignore")


def abspath(path):
    r'''
Return absolute path.

:param str path: A HDF5-path.
:return: The absolute path.
    '''

    import posixpath

    return posixpath.normpath(posixpath.join('/', path))


def join(*args, root=False):
    r'''
Join path components.

:param list args: Piece of a path.
:return: The concatenated path.
    '''

    import posixpath

    lst = []

    for i, arg in enumerate(args):
        if i == 0:
            lst += [arg]
        else:
            lst += [arg.strip('/')]

    if root:
        return posixpath.join('/', *lst)

    return posixpath.join(*lst)


def getdatasets(data, root='/'):
    r'''
Iterator to transverse all datasets in HDF5 file.

:param h5py.File data: A HDF5-archive.
:param str root: Start a certain point along the path-tree.
:return: Iterator.

:example:

    .. code-block:: python

        with h5py.File('...', 'r') as data:

            # loop over all datasets
            for path in GooseHDF5.getdatasets(data):
                print(path)

            # get a set of all datasets
            paths = set(GooseHDF5.getdatasets(data))

            # get a list of all datasets
            paths = list(GooseHDF5.getdatasets(data))

    Read more in `this answer <https://stackoverflow.com/a/50720736/2646505>`_.
    '''

    # ---------------------------------------------

    def iterator(g, prefix):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path)

    # ---------------------------------------------

    if isinstance(data[root], h5py.Dataset):
        yield root

    for path in iterator(data[root], root):
        yield path


def getpaths(data, root='/', max_depth=None, fold=None):
    r'''
Iterator to transverse all datasets in HDF5 file.
One can choose to fold (not transverse deeper than):

-   Groups deeper than a certain ``max_depth``.
-   A (list of) specific group(s).

:param h5py.File data: A HDF5-archive.
:param str root: Start a certain point along the path-tree.
:param int max_depth: Set a maximum depth beyond which groups are folded.
:param list fold: Specify groups that are folded.
:return: Iterator.

:example:

    Consider this file:

    .. code-block:: bash

        /path/to/first/a
        /path/to/first/b
        /data/c
        /data/d
        /e

    Calling:

    .. code-block:: python

        with h5py.File('...', 'r') as data:

            for path in GooseHDF5.getpaths(data, max_depth=2, fold='/data'):
                print(path)

    Will print:

    .. code-block:: bash

        /path/to/...
        /data/...
        /e

    The ``...`` indicate that it concerns a folded group, not a dataset.
    Here, the first group was folded because of the maximum depth, and the second because it was
    specifically requested to be folded.
    '''

    if max_depth and fold:
        return _getpaths_fold_maxdepth(data, root, fold, max_depth)

    if max_depth:
        return _getpaths_maxdepth(data, root, max_depth)

    if fold:
        return _getpaths_fold(data, root, fold)

    return _getpaths(data, root)


def _getpaths(data, root):
    r'''
Specialization for :py:func:`getpaths`.
    '''

    # ---------------------------------------------

    def iterator(g, prefix):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path)

    # ---------------------------------------------

    if isinstance(data[root], h5py.Dataset):
        yield root

    for path in iterator(data[root], root):
        yield path


def _getpaths_maxdepth(data, root, max_depth):
    r'''
Specialization for :py:func:`getpaths` such that:

- Groups deeper than a certain maximum depth are folded.
    '''

    # ---------------------------------------------

    def iterator(g, prefix, max_depth):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif len(path.split('/')) - 1 >= max_depth:
                yield path + '/...'

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, max_depth)

    # ---------------------------------------------

    if isinstance(max_depth, str):
        max_depth = int(max_depth)

    if isinstance(data[root], h5py.Dataset):
        yield root

    for path in iterator(data[root], root, max_depth):
        yield path


def _getpaths_fold(data, root, fold):
    r'''
Specialization for :py:func:`getpaths` such that:

- Certain groups are folded.
    '''

    # ---------------------------------------------

    def iterator(g, prefix, fold):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif path in fold:
                yield path + '/...'

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, fold)

    # ---------------------------------------------

    if isinstance(fold, str):
        fold = [fold]

    if isinstance(data[root], h5py.Dataset):
        yield root

    for path in iterator(data[root], root, fold):
        yield path


def _getpaths_fold_maxdepth(data, root, fold, max_depth):
    r'''
Specialization for :py:func:`getpaths` such that:

- Certain groups are folded.
- Groups deeper than a certain maximum depth are folded.
    '''

    # ---------------------------------------------

    def iterator(g, prefix, fold, max_depth):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif len(path.split('/')) - 1 >= max_depth:
                yield path + '/...'

            elif path in fold:
                yield path + '/...'

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, fold, max_depth)

    # ---------------------------------------------

    if isinstance(max_depth, str):
        max_depth = int(max_depth)

    if isinstance(fold, str):
        fold = [fold]

    if isinstance(data[root], h5py.Dataset):
        yield root

    for path in iterator(data[root], root, fold, max_depth):
        yield path


def filter_datasets(data, paths):
    r'''
From a list of paths, filter those paths that do not point to datasets.

This function can, for example, be used in conjunction with :py:func:`getpaths`:

.. code-block:: python

    with h5py.File('...', 'r') as data:

        datasets = GooseHDF5.filter_datasets(data,
            GooseHDF5.getpaths(data, max_depth=2, fold='/data'))

:param h5py.File data: A HDF5-archive.
:param list paths: List of HDF5-paths.
:return: Filtered ``paths``.
    '''

    import re

    paths = list(paths)
    paths = [path for path in paths if not re.match(r'(.*)(/\.\.\.)', path)]
    paths = [path for path in paths if isinstance(data[path], h5py.Dataset)]
    return paths


def verify(data, datasets, error=False):
    r'''
Try reading each datasets.

:param h5py.File data: A HDF5-archive.
:param list datasets: List of HDF5-paths tp datasets.

:param bool error:
    -   If ``True``, the function raises an error if reading failed.
    -   If ``False``, the function just continues.

:return: List with only those datasets that can be successfully opened.
    '''

    ret = []

    for path in datasets:

        try:
            tmp = data[path][...]
        except:
            if error:
                raise IOError('Error reading "{path:s}"'.format(path=path))
            else:
                continue

        ret += [path]

    return ret


def exists(data, path):
    r'''
Check if a path exists in the HDF5-archive.

:param h5py.File data: A HDF5-archive.
:param str path: HDF5-path.
    '''

    if path in data:
        return True

    return False


def exists_any(data, paths):
    r'''
Check if any of the input paths exists in the HDF5-archive.

:param h5py.File data: A HDF5-archive.
:param list path: List of HDF5-paths.
    '''

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        if exists(data, path):
            return True

    return False


def exists_all(data, paths):
    r'''
Check if all of the input paths exists in the HDF5-archive.

:arguments:

:param h5py.File data: A HDF5-archive.
:param list path: List of HDF5-paths.
    '''

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        if not exists(data, path):
            return False

    return True


def copydatasets(source, dest, source_datasets, dest_datasets=None, root=None):
    r'''
Copy all datasets from one HDF5-archive ``source`` to another HDF5-archive ``dest``.
The datasets can be renamed by specifying a list of ``dest_datasets``
(whose entries should correspond to the ``source_datasets``).

In addition, a ``root`` (path prefix) for the destination datasets name can be specified.

:param h5py.File source: The source HDF5-archive.
:param h5py.File dest: The destination HDF5-archive.
:param list source_datatsets: List of HDF5-paths to datasets in ``source``.
:param list dest_datasets: List of HDF5-paths to datasets in ``dest``, defaults to ``source_datasets``.
:param str root: Path prefix for all ``dest_datasets``.
    '''

    import posixpath

    source_datasets = [abspath(path) for path in source_datasets]

    if not dest_datasets:
        dest_datasets = [path for path in source_datasets]

    if root:
        dest_datasets = [join(root, path, root=True) for path in dest_datasets]

    for dest_path in dest_datasets:
        if exists(dest, dest_path):
            raise IOError('Dataset "{0:s}" already exists'.format(dest_path))

    # extract groups and sort based on depth
    groups = list(set([posixpath.split(path)[0] for path in dest_datasets]))
    groups = [group for group in groups if group != '/']
    groups = sorted(groups, key=lambda group: (group.count('/'), group))

    # create groups
    for group in groups:
        if not exists(dest, group):
            dest.create_group(group)

    # copy datasets
    for source_path, dest_path in zip(source_datasets, dest_datasets):
        group = posixpath.split(dest_path)[0]
        source.copy(source_path, dest[group], posixpath.split(dest_path)[1])


def isnumeric(a):
    r'''
Returns ``True`` is an array contains numeric values.

:param array a: An array.
:return: bool
    '''

    import numpy as np

    if type(a) == str:
        return False

    if np.issubdtype(a.dtype, np.number):
        return True

    return False


def _equal_value(a, b):

    import numpy as np

    if type(a) == str:
        if type(b) == str:
            return a == b
        else:
            return False

    if np.issubdtype(a.dtype, np.number) and np.issubdtype(b.dtype, np.number):
        if np.allclose(a, b):
            return True
        else:
            return False

    if a.size != b.size:
        return False

    if a.size == 1:
        if a[...] == b[...]:
            return True
        else:
            return False

    return list(a) == list(b)


def _equal(a, b):

    if isinstance(a, h5py.Group) and isinstance(b, h5py.Group):
        return True

    if not isinstance(a, h5py.Dataset) or not isinstance(b, h5py.Dataset):
        raise IOError('Not a Dataset')

    for key in a.attrs:
        if key not in b.attrs:
            return False
        if not _equal_value(a.attrs[key], b.attrs[key]):
            return False

    for key in b.attrs:
        if key not in a.attrs:
            return False

    return _equal_value(a, b)


def equal(source, dest, source_dataset, dest_dataset=None):
    r'''
Check that a dataset is equal in both files.

:param h5py.File source: The source HDF5-archive.
:param h5py.File dest: The destination HDF5-archive.
:param list source_datatsets: List of HDF5-paths to datasets in ``source``.
:param list dest_datasets: List of HDF5-paths to datasets in ``dest``, defaults to ``source_datasets``.
    '''

    if not dest_dataset:
        dest_dataset = source_dataset

    if source_dataset not in source:
        raise IOError('"{0:s} not in {1:s}'.format(source_dataset, source.filename))

    if dest_dataset not in dest:
        raise IOError('"{0:s} not in {1:s}'.format(dest_dataset, dest.filename))

    return _equal(source[source_dataset], dest[dest_dataset])


def allequal(source, dest, source_datasets, dest_datasets=None):
    r'''
Check that all listed datasets are equal in both files.

:param h5py.File source: The source HDF5-archive.
:param h5py.File dest: The destination HDF5-archive.
:param list source_datatsets: List of HDF5-paths to datasets in ``source``.
:param list dest_datasets: List of HDF5-paths to datasets in ``dest``, defaults to ``source_datasets``.
    '''

    if not dest_datasets:
        dest_datasets = [path for path in source_datasets]

    for source_dataset, dest_dataset in zip(source_datasets, dest_datasets):
        if not equal(source, dest, source_dataset, dest_dataset):
            return False

    return True


def copy_dataset(source, dest, paths, compress=False, double_to_float=False):
    r'''
Copy a dataset from one file to another. This function also copies possible attributes.

:param h5py.File source: The source HDF5-archive.
:param h5py.File dest: The destination HDF5-archive.

:type paths: str, list
:param paths: (List of) HDF5-path(s) to copy.

:param bool compress: Compress the destination dataset(s).
:param bool double_to_float: Convert doubles to floats before copying.
    '''

    if type(paths) != list:
        paths = list(paths)

    for path in paths:

        data = source[path][...]

        if data.size == 1 or not compress or not isnumeric(data):
            dest[path] = source[path][...]
        else:
            dtype = source[path].dtype
            if dtype == np.float64 and double_to_float:
                dtype = np.float32
            dset = dest.create_dataset(path, data.shape, dtype=dtype, compression="gzip")
            dset[:] = data

        for key in source[path].attrs:
            dest[path].attrs[key] = source[path].attrs[key]
