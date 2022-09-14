from __future__ import annotations

import argparse
import functools
import operator
import os
import posixpath
import re
import sys
import warnings
from functools import singledispatch
from typing import Iterator

import h5py
import numpy as np
import prettytable
from termcolor import colored

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


def abspath(path: str) -> str:
    """
    Return absolute path.

    :param str path: A HDF5-path.
    :return: The absolute path.
    """
    return posixpath.normpath(posixpath.join("/", path))


def join(*args, root: bool = False) -> str:
    """
    Join path components.

    :param list args: Piece of a path.
    :param root: Prepend the output with the root ``"/"``.
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


def getdatapaths(file, root: str = "/") -> list[str]:
    """
    Get paths to all:

    -   Datasets, and
    -   Groups that contain attributes.

    :param file: A HDF5-archive.
    :param root: Start at a certain point along the path-tree.
    :return: List of paths.
    """
    return list(getdatasets(file, root=root)) + list(getgroups(file, root=root, has_attrs=True))


def getgroups(
    file: h5py.File, root: str = "/", has_attrs: bool = False, max_depth: int = None
) -> list[str]:
    """
    Paths of all groups in a HDF5-archive.

    :param file: A HDF5-archive.
    :param root: Start at a certain point along the path-tree.
    :param has_attrs: Return only groups that have attributes.
    :param int max_depth: Set a maximum depth beyond which groups are folded.
    :return: List of paths.
    """

    keys = []
    group = file[root]
    group.visit(lambda key: keys.append(key) if isinstance(group[key], h5py.Group) else None)
    keys = [join(root, key) for key in keys]

    if has_attrs:
        keys = [key for key in keys if len(file[key].attrs) > 0]

    if max_depth is not None:
        n = len(list(filter(None, root.split("/"))))
        for i, path in enumerate(keys):
            if len(path.split("/")) - 1 > n + max_depth:
                keys[i] = posixpath.join("/", *path.split("/")[: n + max_depth + 1]) + "/..."
        keys = list(set(keys))

    return keys


def getdatasets(
    file: h5py.File, root: str = "/", max_depth: int = None, fold: str | list[str] = None
) -> Iterator:
    r"""
    Iterator to transverse all datasets in a HDF5-archive.
    One can choose to fold (not transverse deeper than):

    -   Groups deeper than a certain ``max_depth``.
    -   A (list of) specific group(s).

    :param file: A HDF5-archive.
    :param root: Start a certain point along the path-tree.
    :param max_depth: Set a maximum depth beyond which groups are folded.
    :param fold: Specify groups that are folded.
    :return: Iterator to paths.

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
                if len(list(iterator(item, path, max_depth + 1))) > 0:
                    yield path + "/..."
                else:
                    yield path

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


def _copy(source, dest, source_paths, dest_paths, expand_soft):
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

        if not expand_soft:
            link = source.get(source_path, getlink=True)
            if isinstance(link, h5py.SoftLink):
                dest[dest_path] = h5py.SoftLink(link.path)
                continue

        group = posixpath.split(dest_path)[0]
        source.copy(source_path, dest[group], posixpath.split(dest_path)[1])


def _copy_attrs(source, dest, source_paths, dest_paths, expand_soft):

    if len(source_paths) == 0:
        return 0

    _create_groups(dest, dest_paths)

    for source_path, dest_path in zip(source_paths, dest_paths):

        if not expand_soft:
            link = source.get(source_path, getlink=True)
            if isinstance(link, h5py.SoftLink):
                dest[dest_path] = h5py.SoftLink(link.path)
                continue

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
    source_root: str = None,
    recursive: bool = True,
    skip: bool = False,
    expand_soft: bool = True,
):
    """
    Copy groups/datasets from one HDF5-archive ``source`` to another HDF5-archive ``dest``.
    The datasets can be renamed by specifying a list of ``dest_datasets``
    (whose entries should correspond to the ``source_datasets``).
    In addition, a ``root`` path prefix can be specified for the destination datasets.
    Likewise, a ``source_root`` path prefix can be specified for the source datasets.

    :param source: The source HDF5-archive.
    :param dest: The destination HDF5-archive.
    :param source_datasets: List of dataset-paths in ``source``.
    :param dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    :param root: Path prefix for all ``dest_datasets``.
    :param source_root: Path prefix for all ``source_datasets``.
    :param recursive: If the source is a group, copy all objects within that group recursively.
    :param skip: Skip datasets that are not present in source.
    :param expand_soft: Copy the underlying data of a link, or copy as link with the same path.
    """

    if type(source_datasets) is str:
        source_datasets = [source_datasets]
    if type(dest_datasets) is str:
        dest_datasets = [dest_datasets]

    if len(source_datasets) == 0:
        return

    source_datasets = np.array([abspath(path) for path in source_datasets])

    if not dest_datasets:
        dest_datasets = [path for path in source_datasets]

    dest_datasets = np.array(dest_datasets)

    if skip:
        keep = [i in source for i in source_datasets]
        source_datasets = source_datasets[keep]
        dest_datasets = dest_datasets[keep]

    if root:
        dest_datasets = np.array([join(root, path, root=True) for path in dest_datasets])

    if source_root:
        source_datasets = np.array([join(source_root, path, root=True) for path in source_datasets])

    for path in source_datasets:
        if not exists(source, path):
            raise OSError(f'Dataset "{path}" does not exists in source.')

    for path in dest_datasets:
        if exists(dest, path):
            raise OSError(f'Dataset "{path}" already exists in dest.')

    isgroup = np.array([isinstance(source[path], h5py.Group) for path in source_datasets])

    if recursive:
        _copy(
            source, dest, source_datasets[isgroup], dest_datasets[isgroup], expand_soft=expand_soft
        )

    _copy(
        source,
        dest,
        source_datasets[np.logical_not(isgroup)],
        dest_datasets[np.logical_not(isgroup)],
        expand_soft=expand_soft,
    )

    if not recursive:
        _copy_attrs(
            source, dest, source_datasets[isgroup], dest_datasets[isgroup], expand_soft=expand_soft
        )


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

    warnings.warn("copydatasets() is deprecated, use copy().", category=DeprecationWarning)

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

    return np.all(np.array(list(a[...])) == np.array(list(b[...])))


def _equal(a, b, attrs, matching_dtype, shallow):

    if attrs:

        for key in a.attrs:
            if key not in b.attrs:
                return False
            if matching_dtype:
                if a.attrs[key].dtype != b.attrs[key].dtype:
                    return False
            if shallow:
                return True
            if not _equal_value(a.attrs[key], b.attrs[key]):
                return False

        for key in b.attrs:
            if key not in a.attrs:
                return False

    if isinstance(a, h5py.Group) and isinstance(b, h5py.Group):
        return True

    if not isinstance(a, h5py.Dataset) or not isinstance(b, h5py.Dataset):
        raise OSError("Not a Dataset")

    if matching_dtype:
        if a.dtype != b.dtype:
            return False

    if shallow:
        return True

    return _equal_value(a, b)


def equal(
    source: h5py.File,
    dest: h5py.File,
    source_dataset: str,
    dest_dataset: str = None,
    root: str = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
):
    r"""
    Check that a dataset is equal in both files.

    :param h5py.File source: The source HDF5-archive.
    :param h5py.File dest: The destination HDF5-archive.
    :param list source_datasets: List of dataset-paths in ``source``.
    :param list dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    :param root: Path prefix for ``dest_dataset``.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of the dataset, not its value.
    """

    if not dest_dataset:
        dest_dataset = source_dataset

    if root is not None:
        dest_dataset = join(root, dest_dataset, root=True)

    if source_dataset not in source:
        raise OSError(f'"{source_dataset:s} not in {source.filename:s}')

    if dest_dataset not in dest:
        raise OSError(f'"{dest_dataset:s} not in {dest.filename:s}')

    return _equal(source[source_dataset], dest[dest_dataset], attrs, matching_dtype, shallow)


def allequal(
    source: h5py.File,
    dest: h5py.File,
    source_datasets: list[str],
    dest_datasets: list[str] = None,
    root: str = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
):
    r"""
    Check that all listed datasets are equal in both files.

    :param h5py.File source: The source HDF5-archive.
    :param h5py.File dest: The destination HDF5-archive.
    :param list source_datasets: List of dataset-paths in ``source``.
    :param list dest_datasets: List of dataset-paths in ``dest``, defaults to ``source_datasets``.
    :param root: Path prefix for all ``dest_datasets``.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of the dataset, not its value.
    """

    if not dest_datasets:
        dest_datasets = [path for path in source_datasets]

    for source_dataset, dest_dataset in zip(source_datasets, dest_datasets):
        if not equal(
            source,
            dest,
            source_dataset,
            dest_dataset,
            root=root,
            attrs=attrs,
            matching_dtype=matching_dtype,
            shallow=shallow,
        ):
            return False

    return True


def _compare_paths(
    a: h5py.File, b: h5py.File, paths_a: list[str], paths_b: list[str], attrs: bool
) -> type[list[str], list[str]]:
    """
    Default paths for :py:func:`compare`.
    """

    if paths_b is None and paths_a is not None:
        paths_b = paths_a

    if paths_a is None:
        if attrs:
            paths_a = getdatapaths(a)
        else:
            paths_a = list(getdatasets(a))

    if paths_b is None:
        if attrs:
            paths_b = getdatapaths(b)
        else:
            paths_b = list(getdatasets(b))

    return paths_a, paths_b


@singledispatch
def compare(
    a: str | h5py.File,
    b: str | h5py.File,
    paths_a: list[str] = None,
    paths_b: list[str] = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
) -> dict[list]:
    """
    Compare two files.
    Return dictionary with differences::

        {
            "->" : ["/path/in/b/but/not/in/a", ...],
            "<-" : ["/path/in/a/but/not/in/b", ...],
            "!=" : ["/path/in/both/but/different/data", ...],
            "==" : ["/data/matching", ...]
        }

    :param a: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param b: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param paths_a: Paths from ``a`` to consider. Default: read from :py:func:`getdatapaths`.
    :param paths_b: Paths from ``b`` to consider. Default: read from :py:func:`getdatapaths`.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of datasets, not their values, size, or attributes.
    :return: Dictionary with difference.
    """
    raise NotImplementedError("Overload not found.")


@compare.register(h5py.File)
def _(
    a: h5py.File,
    b: h5py.File,
    paths_a: list[str] = None,
    paths_b: list[str] = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
) -> dict[list]:

    ret = {"<-": [], "->": [], "!=": [], "==": []}
    paths_a, paths_b = _compare_paths(a, b, paths_a, paths_b, attrs)

    not_in_b = [str(i) for i in np.setdiff1d(paths_a, paths_b)]
    not_in_a = [str(i) for i in np.setdiff1d(paths_b, paths_a)]
    inboth = [str(i) for i in np.intersect1d(paths_a, paths_b)]

    for path in not_in_a:
        ret["<-"].append(path)

    for path in not_in_b:
        ret["->"].append(path)

    for path in inboth:
        if not equal(a, b, path, attrs=attrs, matching_dtype=matching_dtype, shallow=shallow):
            ret["!="].append(path)
        else:
            ret["=="].append(path)

    return ret


@compare.register(str)
def _(
    a: str,
    b: str,
    paths_a: list[str] = None,
    paths_b: list[str] = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
) -> dict[list]:

    with h5py.File(a, "r") as a_file, h5py.File(b, "r") as b_file:
        return compare(a_file, b_file, paths_a, paths_a, attrs, matching_dtype, shallow)


def compare_rename(
    a: h5py.File,
    b: h5py.File,
    rename: list[str] = None,
    paths_a: list[str] = None,
    paths_b: list[str] = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
    regex: bool = False,
) -> dict[list]:
    """
    Compare two files.
    Return three dictionaries with differences::

        # plain comparison between a and b

        {
            "->" : ["/path/in/b/but/not/in/a", ...],
            "<-" : ["/path/in/a/but/not/in/b", ...],
            "!=" : ["/path/in/both/but/different/data", ...],
            "==" : ["/data/matching", ...]
        }

        # comparison of renamed paths: list of paths in a

        {
            "!=" : ["/path/in/a/with/rename/path/not_equal", ...],
            "==" : ["/path/in/a/with/rename/path/matching", ...]
        }

        # comparison of renamed paths: list of paths in b

        {
            "!=" : ["/path/in/b/with/rename/path/not_equal", ...],
            "==" : ["/path/in/b/with/rename/path/matching", ...]
        }

    :param a: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param b: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param rename: List with with renamed pairs: ``[["/a/0", "/b/1"], ...]``.
    :param paths_a: Paths from ``a`` to consider. Default: read from :py:func:`getdatapaths`.
    :param paths_b: Paths from ``b`` to consider. Default: read from :py:func:`getdatapaths`.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of datasets, not their values, size, or attributes.
    :param regex: Use regular expressions to match ``rename``.
    :return: Dictionary with difference.
    """

    opts = dict(attrs=attrs, matching_dtype=matching_dtype, shallow=shallow)

    if rename is None:
        empty = {"!=": [], "==": []}
        return compare(a, b, paths_a, paths_b, **opts), empty, empty

    paths_a, paths_b = _compare_paths(a, b, paths_a, paths_b, attrs)

    rename_a = []
    rename_b = []

    if not regex:
        for path_a, path_b in rename:
            if path_a not in paths_a or path_b not in paths_b:
                raise OSError("Renamed paths must be present")
            rename_a.append(path_a)
            rename_b.append(path_b)
    else:
        for pattern_a, pattern_b in rename:
            for path_a in paths_a:
                if re.match(rf"({pattern_a})(.*)", path_a):
                    path_b = re.sub(rf"({pattern_a})(.*)", rf"{pattern_b}\2", path_a)
                    if path_b not in paths_b:
                        continue
                    rename_a.append(path_a)
                    rename_b.append(path_b)

    keep_a = ~np.in1d(paths_a, rename_a)
    keep_b = ~np.in1d(paths_b, rename_b)

    paths_a = np.array(paths_a)[keep_a]
    paths_b = np.array(paths_b)[keep_b]

    ret = compare(a, b, paths_a, paths_b, **opts)
    ret_a = {"!=": [], "==": []}
    ret_b = {"!=": [], "==": []}

    for path_a, path_b in zip(rename_a, rename_b):
        if not equal(a, b, path_a, path_b, **opts):
            ret_a["!="].append(path_a)
            ret_b["!="].append(path_b)
        else:
            ret_a["=="].append(path_a)
            ret_b["=="].append(path_b)

    return ret, ret_a, ret_b


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
            dset = dest.create_dataset(path, data.shape, dtype=dtype, compression="gzip")
            dset[:] = data

        for key in source[path].attrs:
            dest[path].attrs[key] = source[path].attrs[key]


def _linktype2str(source: h5py.File | h5py.Group, path: str) -> str:

    dset = source.get(path, getlink=True)

    if isinstance(dset, h5py.SoftLink):
        return "soft"

    if isinstance(dset, h5py.HardLink):
        return "hard"

    if isinstance(dset, h5py.ExternalLink):
        return "external"

    return "??"


def print_plain(source, paths: list[str], show_links: bool = False):
    r"""
    Print the paths to all datasets (one per line).
    :param paths: List of paths.
    :param show_links: Show the path the link points to.
    """

    if show_links:
        for path in paths:
            if isinstance(source.get(path, getlink=True), h5py.SoftLink):
                print(path + " -> " + source.get(path, getlink=True).path)
            else:
                print(path)
        return

    for path in paths:
        print(path)


def info_table(source, paths: list[str], link_type: bool = False) -> prettytable.PrettyTable:
    r"""
    Get a table with basic information per path:

    - path
    - size
    - shape
    - dtype
    - attrs: Number of attributes
    - link: Link type

    :param paths: List of paths.
    :param link_type: Include the link-type in the output.
    """

    def has_attributes(lst):
        for i in lst:
            if i != "-" and i != "0":
                return True
        return False

    header = ["path", "size", "shape", "dtype", "attrs"]
    out = {key: [] for key in header}

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

    if link_type:
        header.append("link")
        out["link"] = [_linktype2str(source, path) for path in paths]

    table = prettytable.PrettyTable()
    for key in header:
        table.add_column(column=out[key], fieldname=key, align="l")

    return table


def print_attribute(source, paths: list[str]):
    r"""
    Print paths to dataset and to all underlying attributes.
    :param paths: List of paths.
    """

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


def _G5print_parser():
    """
    Return parser for :py:func:`G5print`.
    """

    desc = "Print (one, several, or all) datasets in a HDF5-file."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--full", action="store_true", help="Print full array")
    parser.add_argument("--no-data", action="store_true", help="Don't print data")
    parser.add_argument("--regex", action="store_true", help="Evaluate dataset name as a regex")
    parser.add_argument("-a", "--attrs", action="store_true", help="Print attributes")
    parser.add_argument("-d", "--max-depth", type=int, help="Maximum depth to display")
    parser.add_argument("-f", "--fold", action="append", help="Fold paths")
    parser.add_argument("-i", "--info", action="store_true", help="Print information: shape, dtype")
    parser.add_argument("-r", "--root", default="/", help="Start somewhere in the path-tree")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("source", help="File path")
    parser.add_argument("dataset", nargs="*", help="Path to datasets to print (default: all)")
    return parser


def G5print(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _G5print_parser()
    args = parser.parse_args(args)

    if not os.path.isfile(args.source):
        print("File does not exist")
        return 1

    if args.full:
        np.set_printoptions(threshold=sys.maxsize)

    with h5py.File(args.source, "r") as source:

        if len(args.dataset) == 0:
            print_header = True
            datasets = list(
                getdatasets(source, root=args.root, max_depth=args.max_depth, fold=args.fold)
            )
            datasets += list(getgroups(source, root=args.root, has_attrs=True))
            datasets = sorted(datasets)
        elif args.regex:
            print_header = True
            paths = list(
                getdatasets(source, root=args.root, max_depth=args.max_depth, fold=args.fold)
            )
            paths += list(getgroups(source, root=args.root, has_attrs=True))
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


def _G5list_parser():
    """
    Return parser for :py:func:`G5list`.
    """

    desc = """List datasets (or groups of datasets) in a HDF5-file.
    Note that if you have a really big file the ``--layer`` option can be much faster than
    searching the entire file.
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--min-attrs", type=int, help="Filter based on min. number of attributes")
    parser.add_argument("--link-type", action="store_true", help="Print the link-type")
    parser.add_argument("-D", "--datasets", action="store_true", help="Print only datasets")
    parser.add_argument("-d", "--max-depth", type=int, help="Maximum depth to display")
    parser.add_argument("-f", "--fold", action="append", help="Fold paths")
    parser.add_argument("-i", "--info", action="store_true", help="Print info: shape, dtype")
    parser.add_argument("-L", "--layer", type=str, help="Print paths at a specific layer")
    parser.add_argument("-l", "--long", action="store_true", help="--info but with attributes")
    parser.add_argument("-r", "--root", default="/", help="Start somewhere in the path-tree")
    parser.add_argument("--links", action="store_true", help="Show destination of soft links")
    parser.add_argument("-s", "--sort", type=str, default="path", help="Sort by some column")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("source")
    return parser


def G5list(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _G5list_parser()
    args = parser.parse_args(args)

    if not os.path.isfile(args.source):
        raise OSError(f'"{args.source}" does not exist')

    with h5py.File(args.source, "r") as source:

        if args.layer is not None:
            paths = sorted(join(args.layer, i, root=True) for i in source[args.layer])
        else:
            paths = list(
                getdatasets(source, root=args.root, max_depth=args.max_depth, fold=args.fold)
            )
            if not args.datasets:
                paths += getgroups(source, root=args.root, has_attrs=True, max_depth=args.max_depth)
            paths = sorted(list(set(paths)))

        if args.min_attrs is not None:
            rm = []
            for path in paths:
                if path in source:
                    source[path]
                    if len(source[path].attrs) < args.min_attrs:
                        rm.append(path)
            for path in rm:
                paths.remove(path)

        if args.info:
            table = info_table(source, paths, link_type=args.link_type)
            table.set_style(prettytable.SINGLE_BORDER)
            print(table.get_string(sortby=args.sort))
        elif args.long:
            print_attribute(source, paths)
        else:
            print_plain(source, paths, show_links=args.links)


def _G5compare_parser():
    """
    Return parser for :py:func:`G5compare`.
    """

    desc = """Compare two HDF5 files.
    If the function does not output anything all datasets are present in both files,
    and all the content of the datasets is equal.
    Each output line corresponds to a mismatch between the files.

    Deal with renamed paths::

        G5compare a.h5 b.h5 -r "/a" "/b"  -r "/c" "/d"
    """
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument(
        "-t", "--dtype", action="store_true", help="Verify that the type of the datasets match."
    )
    parser.add_argument(
        "--shallow",
        action="store_true",
        help="Only check for the presence of datasets and attributes. Do not check their values.",
    )
    parser.add_argument("-r", "--renamed", nargs=2, action="append", help="Renamed paths.")
    parser.add_argument("-c", "--colors", default="dark", help="Color theme: dark/light/none")
    parser.add_argument("--table", default="SINGLE_BORDER", help="Table theme")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("a", help="Path to HDF5-file.")
    parser.add_argument("b", help="Path to HDF5-file.")
    return parser


def _truncate_print_path(path: str, n: int) -> str:
    """
    Truncate a file path, such that the printed length is smaller than ``n``.
    For example::

        "/path/to/long/foo/bar" -> "/path/.../bar"

    :param path: Path to truncate.
    :param n: Maximum length of the path.
    :return: Truncated path.
    """

    if len(path) <= n:
        return path

    path = os.path.abspath(path).split(os.sep)
    if len(path[0]) == 0:
        path[0] = os.sep

    length = np.array([len(i) for i in path])
    incl = np.zeros(len(path), dtype=bool)
    incl[0] = True
    incl[-1] = True

    # try including from the back
    for i in range(1, len(path) - 1)[::-1]:
        incl[i] = True
        if np.sum(length[incl]) + np.sum(incl) + 3 > n:
            incl[i] = False
            break

    # try including from the front
    for i in range(1, len(path) - 1):
        incl[i] = True
        if np.sum(length[incl]) + np.sum(incl) + 3 > n:
            incl[i] = False
            break

    if np.sum(incl) != len(path):
        i = np.argmin(incl)
        j = i + np.argmax(incl[i:])
        path = path[:i] + ["..."] + path[j:]

    return os.path.join(*path)


def G5compare(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _G5compare_parser()
    args = parser.parse_args(args)

    for filepath in [args.a, args.b]:
        if not os.path.isfile(filepath):
            raise OSError(f'"{filepath}" does not exist')

    with h5py.File(args.a, "r") as a, h5py.File(args.b, "r") as b:
        comp, r_a, r_b = compare_rename(
            a, b, rename=args.renamed, matching_dtype=args.dtype, shallow=args.shallow, regex=True
        )

    def print_path(path):
        if len(os.path.relpath(path).split("..")) < 3:
            return os.path.relpath(path)
        return os.path.abspath(path)

    def def_row(arg, colors):

        if colors == "none":
            if arg[1] == "!=":
                return arg
            if arg[1] == "->":
                return [arg[0], arg[1], ""]
            if arg[1] == "<":
                return ["", arg[1], arg[2]]

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

    out = prettytable.PrettyTable()
    if args.table == "PLAIN_COLUMNS":
        out.set_style(prettytable.PLAIN_COLUMNS)
    elif args.table == "SINGLE_BORDER":
        out.set_style(prettytable.SINGLE_BORDER)
    out.align = "l"

    for key in comp:
        if key != "==":
            for item in comp[key]:
                out.add_row(def_row([item, key, item], args.colors))

    for path_a, path_b in zip(r_a["!="], r_b["!="]):
        out.add_row(def_row([path_a, "!=", path_b], args.colors))

    file_a = print_path(args.a)
    file_b = print_path(args.b)
    n = max(len(row[0]) for row in out.rows)
    out.field_names = [_truncate_print_path(file_a, n), "", _truncate_print_path(file_b, n)]

    print(out.get_string())


def _G5print_catch():
    try:
        G5print(sys.argv[1:])
    except Exception as e:
        print(e)
        return 1


def _G5list_catch():
    try:
        G5list(sys.argv[1:])
    except Exception as e:
        print(e)
        return 1


def _G5compare_catch():
    try:
        G5compare(sys.argv[1:])
    except Exception as e:
        print(e)
        return 1
