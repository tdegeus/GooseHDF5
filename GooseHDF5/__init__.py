import functools
import operator
import posixpath
import warnings

import h5py
import numpy as np

from ._version import version  # noqa: F401
from ._version import version_tuple  # noqa: F401

warnings.filterwarnings("ignore")


def _dict_iterategroups(data: dict, root: str = "/"):
    """
    Get groups from a (nested) dictionary.

    :param data: A nested dictionary.
    :param root: The path the the (current) root.
    :return: iterator
    """

    for key in data.keys():

        item = data[key]
        path = join(root, key)

        if not isinstance(item, dict):
            yield path
        else:
            yield from _dict_iterategroups(item, path)


def _dict_get(data: dict, path: str):
    r"""
    Get an item from a nested dictionary.

    :param data: A nested dictionary.
    :param path: E.g.``"/path/to/data"``.
    :return: The item.
    """

    key = list(filter(None, path.split("/")))

    if len(key) > 0:
        try:
            return functools.reduce(operator.getitem, key, data)
        except KeyError:
            raise OSError(f'"{path:s}" not found')

    return data


def dump(file: h5py.File, data: dict, root: str = "/"):
    """
    Dump (nested) dictionary to file.
    """

    assert isinstance(data, dict)

    paths = list(_dict_iterategroups(data))

    for path in paths:
        file[join(root, path)] = _dict_get(data, path)


def abspath(path):
    r"""
    Return absolute path.

    :param str path: A HDF5-path.
    :return: The absolute path.
    """
    return posixpath.normpath(posixpath.join("/", path))


def join(*args, root=False):
    r"""
    Join path components.

    :param list args: Piece of a path.
    :return: The concatenated path.
    """

    lst = []

    for i, arg in enumerate(args):
        if i == 0:
            lst += [arg]
        else:
            lst += [arg.strip("/")]

    if root:
        return posixpath.join("/", *lst)

    return posixpath.join(*lst)


def getdatapaths(file, root: str = "/"):
    """
    Get paths to all datasets and groups that contain attributes.

    :param file: A HDF5-archive.
    :param root: Start a certain point along the path-tree.
    :return: ``list[str]``.
    """
    return list(getdatasets(file, root=root)) + list(
        getgroups(file, root=root, has_attrs=True)
    )


def getgroups(file: h5py.File, root: str = "/", has_attrs=False):
    """
    Iterator to transverse all groups in a HDF5-archive.

    :param file: A HDF5-archive.
    :param root: Start a certain point along the path-tree.
    :param has_attrs: Return only groups that have attributes.
    :return: ``list[str]``.
    """

    keys = []
    group = file[root]
    group.visit(
        lambda key: keys.append(key) if isinstance(group[key], h5py.Group) else None
    )
    keys = [join(root, key) for key in keys]

    if has_attrs:
        keys = [key for key in keys if len(file[key].attrs) > 0]

    return keys


def getdatasets(file, root="/", max_depth=None, fold=None):
    r"""
    Iterator to transverse all datasets in a HDF5-archive.
    One can choose to fold (not transverse deeper than):

    -   Groups deeper than a certain ``max_depth``.
    -   A (list of) specific group(s).

    :param h5py.File file: A HDF5-archive.
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

            with h5py.File("...", "r") as file:

                for path in GooseHDF5.getpaths(file, max_depth=2, fold="/data"):
                    print(path)

        Will print:

        .. code-block:: bash

            /path/to/...
            /data/...
            /e

        The ``...`` indicates that it concerns a folded group, not a dataset.
        Here, the first group was folded because of the maximum depth,
        the second because it was specifically requested to be folded.
    """

    if max_depth and fold:
        return _getpaths_fold_maxdepth(file, root, fold, max_depth)

    if max_depth:
        return _getpaths_maxdepth(file, root, max_depth)

    if fold:
        return _getpaths_fold(file, root, fold)

    return _getpaths(file, root)


def getpaths(data, root="/", max_depth=None, fold=None):
    r"""
    Iterator to transverse all datasets in HDF5-archive.
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
    """

    warnings.warn(
        "getpaths() is deprecated, use getdatasets().", warnings.DeprecationWarning
    )
    return getdatasets(data, root, max_depth, fold)


def _getpaths(file, root):
    r"""
    Specialization for :py:func:`getpaths`.
    """

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

    if isinstance(file[root], h5py.Dataset):
        yield root

    yield from iterator(file[root], root)


def _getpaths_maxdepth(file, root, max_depth):
    r"""
    Specialization for :py:func:`getpaths` such that:

    - Groups deeper than a certain maximum depth are folded.
    """

    # ---------------------------------------------

    def iterator(g, prefix, max_depth):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif len(path.split("/")) - 1 >= max_depth:
                yield path + "/..."

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, max_depth)

    # ---------------------------------------------

    if isinstance(max_depth, str):
        max_depth = int(max_depth)

    if isinstance(file[root], h5py.Dataset):
        yield root

    yield from iterator(file[root], root, max_depth)


def _getpaths_fold(file, root, fold):
    r"""
    Specialization for :py:func:`getpaths` such that:

    - Certain groups are folded.
    """

    # ---------------------------------------------

    def iterator(g, prefix, fold):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif path in fold:
                yield path + "/..."

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, fold)

    # ---------------------------------------------

    if isinstance(fold, str):
        fold = [fold]

    if isinstance(file[root], h5py.Dataset):
        yield root

    yield from iterator(file[root], root, fold)


def _getpaths_fold_maxdepth(file, root, fold, max_depth):
    r"""
    Specialization for :py:func:`getpaths` such that:

    - Certain groups are folded.
    - Groups deeper than a certain maximum depth are folded.
    """

    # ---------------------------------------------

    def iterator(g, prefix, fold, max_depth):

        for key in g.keys():

            item = g[key]
            path = join(prefix, key)

            if isinstance(item, h5py.Dataset):
                yield path

            elif len(path.split("/")) - 1 >= max_depth:
                yield path + "/..."

            elif path in fold:
                yield path + "/..."

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, fold, max_depth)

    # ---------------------------------------------

    if isinstance(max_depth, str):
        max_depth = int(max_depth)

    if isinstance(fold, str):
        fold = [fold]

    if isinstance(file[root], h5py.Dataset):
        yield root

    yield from iterator(file[root], root, fold, max_depth)


def filter_datasets(file, paths):
    r"""
    From a list of paths, filter those paths that do not point to datasets.

    :param h5py.File file: A HDF5-archive.
    :param list paths: List of HDF5-paths.
    :return: Filtered ``paths``.
    """

    import re

    paths = list(paths)
    paths = [path for path in paths if not re.match(r"(.*)(/\.\.\.)", path)]
    paths = [path for path in paths if isinstance(file[path], h5py.Dataset)]
    return paths


def verify(file, datasets, error=False):
    r"""
    Try reading each datasets.

    :param h5py.File file: A HDF5-archive.
    :param list datasets: List of HDF5-paths tp datasets.

    :param bool error:
        -   If ``True``, the function raises an error if reading failed.
        -   If ``False``, the function just continues.

    :return: List with only those datasets that can be successfully opened.
    """

    ret = []

    for path in datasets:

        try:
            file[path][...]
        except:  # noqa: E722
            if error:
                raise OSError(f'Error reading "{path:s}"')
            else:
                continue

        ret += [path]

    return ret


def exists(file, path):
    r"""
    Check if a path exists in the HDF5-archive.

    :param h5py.File file: A HDF5-archive.
    :param str path: HDF5-path.
    """

    if path in file:
        return True

    return False


def exists_any(file, paths):
    r"""
    Check if any of the input paths exists in the HDF5-archive.

    :param h5py.File file: A HDF5-archive.
    :param list path: List of HDF5-paths.
    """

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        if exists(file, path):
            return True

    return False


def exists_all(file, paths):
    r"""
    Check if all of the input paths exists in the HDF5-archive.

    :arguments:

    :param h5py.File file: A HDF5-archive.
    :param list path: List of HDF5-paths.
    """

    if isinstance(paths, str):
        paths = [paths]

    for path in paths:
        if not exists(file, path):
            return False

    return True


def _create_groups(file, paths):
    """
    Create all groups higher than ``paths``.
    For ``path = ["/a/b/c"]`` this function will create groups ``["/a", "/a/b"]``.
    """

    groups = [posixpath.split(path)[0] for path in paths]
    groups = [group for group in groups if group != "/"]
    groups = sorted(groups, key=lambda group: (group.count("/"), group))

    for group in groups:
        if not exists(file, group):
            file.create_group(group)


def _copy(source, dest, source_paths, dest_paths):
    """
    Copy paths recursively.
    """

    if len(source_paths) == 0:
        return 0

    _create_groups(dest, dest_paths)

    for source_path, dest_path in zip(source_paths, dest_paths):
        # skip paths that were already recursively copied
        # (main function checks existence before, so this can be the only reason)
        if dest_path in dest:
            continue
        group = posixpath.split(dest_path)[0]
        source.copy(source_path, dest[group], posixpath.split(dest_path)[1])


def _copy_attrs(source, dest, source_paths, dest_paths):

    if len(source_paths) == 0:
        return 0

    _create_groups(dest, dest_paths)

    for source_path, dest_path in zip(source_paths, dest_paths):

        source_group = source[source_path]

        if dest_path not in dest:
            dest_group = dest.create_group(dest_path)
        else:
            dest_group = dest[dest_path]

        for key in source_group.attrs:
            dest_group.attrs[key] = source_group.attrs[key]


def copy(
    source: h5py.File,
    dest: h5py.File,
    source_datasets: list[str],
    dest_datasets: list[str] = None,
    root: str = None,
    recursive=True,
):
    """
    Copy groups/datasets from one HDF5-archive ``source`` to another HDF5-archive ``dest``.
    The datasets can be renamed by specifying a list of ``dest_datasets``
    (whose entries should correspond to the ``source_datasets``).
    In addition, a ``root`` (path prefix) for the destination datasets name can be specified.

    :param source: The source HDF5-archive.
    :param dest: The destination HDF5-archive.
    :param source_datasets: List of dataset-paths in ``source``.
    :param dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    :param root: Path prefix for all ``dest_datasets``.
    :param recursive: If the source is a group, copy all objects within that group recursively.
    """

    source_datasets = np.array([abspath(path) for path in source_datasets])

    if not dest_datasets:
        dest_datasets = np.array([path for path in source_datasets])

    if root:
        dest_datasets = np.array(
            [join(root, path, root=True) for path in dest_datasets]
        )

    for path in dest_datasets:
        if exists(dest, path):
            raise OSError(f'Dataset "{path}" already exists')

    isgroup = np.array(
        [isinstance(source[path], h5py.Group) for path in source_datasets]
    )

    if recursive:
        _copy(source, dest, source_datasets[isgroup], dest_datasets[isgroup])

    _copy(
        source,
        dest,
        source_datasets[np.logical_not(isgroup)],
        dest_datasets[np.logical_not(isgroup)],
    )

    if not recursive:
        _copy_attrs(source, dest, source_datasets[isgroup], dest_datasets[isgroup])


def copydatasets(
    source: h5py.File,
    dest: h5py.File,
    source_datasets: list[str],
    dest_datasets: list[str] = None,
    root: str = None,
):
    """
    Copy datasets from one HDF5-archive ``source`` to another HDF5-archive ``dest``.
    The datasets can be renamed by specifying a list of ``dest_datasets``
    (whose entries should correspond to the ``source_datasets``).
    If the source is a Group object,
    by default all objects within that group will be copied recursively.

    In addition, a ``root`` (path prefix) for the destination datasets name can be specified.

    :param source: The source HDF5-archive.
    :param dest: The destination HDF5-archive.
    :param source_datasets: List of dataset-paths in ``source``.
    :param dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    :param root: Path prefix for all ``dest_datasets``.
    """

    warnings.warn(
        "copydatasets() is deprecated, use copy().", warnings.DeprecationWarning
    )

    return copy(source, dest, source_datasets, dest_datasets, root)


def isnumeric(a):
    """
    Returns ``True`` is an array contains numeric values.

    :param array a: An array.
    :return: bool
    """

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

    if a.size != b.size:
        return False

    if np.issubdtype(a.dtype, np.floating):
        if not np.issubdtype(b.dtype, np.floating):
            return False
        if np.allclose(a, b):
            return True
        return False

    if np.issubdtype(a.dtype, np.integer):
        if not np.issubdtype(b.dtype, np.integer):
            return False
        if np.all(np.equal(a, b)):
            return True
        return False

    if a.dtype == np.bool_:
        if b.dtype != np.bool_:
            return False
        if np.all(np.equal(a, b)):
            return True
        return False

    if a.size == 1:
        if a[...] == b[...]:
            return True
        else:
            return False

    return list(a[...]) == list(b[...])


def _equal(a, b):

    for key in a.attrs:
        if key not in b.attrs:
            return False
        if not _equal_value(a.attrs[key], b.attrs[key]):
            return False

    for key in b.attrs:
        if key not in a.attrs:
            return False

    if isinstance(a, h5py.Group) and isinstance(b, h5py.Group):
        return True

    if not isinstance(a, h5py.Dataset) or not isinstance(b, h5py.Dataset):
        raise OSError("Not a Dataset")

    return _equal_value(a, b)


def equal(source, dest, source_dataset, dest_dataset=None):
    r"""
    Check that a dataset is equal in both files.

    :param h5py.File source: The source HDF5-archive.
    :param h5py.File dest: The destination HDF5-archive.
    :param list source_datasets: List of dataset-paths in ``source``.
    :param list dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    """

    if not dest_dataset:
        dest_dataset = source_dataset

    if source_dataset not in source:
        raise OSError(f'"{source_dataset:s} not in {source.filename:s}')

    if dest_dataset not in dest:
        raise OSError(f'"{dest_dataset:s} not in {dest.filename:s}')

    return _equal(source[source_dataset], dest[dest_dataset])


def allequal(source, dest, source_datasets, dest_datasets=None):
    r"""
    Check that all listed datasets are equal in both files.

    :param h5py.File source: The source HDF5-archive.
    :param h5py.File dest: The destination HDF5-archive.
    :param list source_datasets: List of dataset-paths in ``source``.
    :param list dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    """

    if not dest_datasets:
        dest_datasets = [path for path in source_datasets]

    for source_dataset, dest_dataset in zip(source_datasets, dest_datasets):
        if not equal(source, dest, source_dataset, dest_dataset):
            return False

    return True


def copy_dataset(source, dest, paths, compress=False, double_to_float=False):
    r"""
    Copy a dataset from one file to another. This function also copies possible attributes.

    :param h5py.File source: The source HDF5-archive.
    :param h5py.File dest: The destination HDF5-archive.

    :type paths: str, list
    :param paths: (List of) HDF5-path(s) to copy.

    :param bool compress: Compress the destination dataset(s).
    :param bool double_to_float: Convert doubles to floats before copying.
    """

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
            dset = dest.create_dataset(
                path, data.shape, dtype=dtype, compression="gzip"
            )
            dset[:] = data

        for key in source[path].attrs:
            dest[path].attrs[key] = source[path].attrs[key]
