from __future__ import annotations

import argparse
import filecmp
import functools
import operator
import os
import posixpath
import re
import sys
import uuid
import warnings
from difflib import SequenceMatcher
from typing import Iterator

import h5py
import numpy as np
import prettytable
import yaml
from numpy.typing import ArrayLike
from termcolor import colored

from ._version import version  # noqa: F401
from ._version import version_tuple  # noqa: F401

warnings.filterwarnings("ignore")


class ExtendableSlice:
    """
    Write slices of an extendable dataset to HDF5 file.

    For example::

        n = 100
        shape = [10, 10]
        dataset = np.random.random([n] + shape)

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", shape, np.float64) as dset:
                for i in range(n):
                    dset.append(dataset[i, ...])  # one can also use ``dset += dataset[i, ...]``

    :param file: Opened HDF5 file (in write mode).
    :param name: Path to the dataset.
    :param shape:
        Shape of the slice (only new dataset).
        The shape of the dataset is ``[0] + shape`` (``0`` is the extendable dimension).
    :param dtype: Data-type to use (only new dataset).
    :param maxshape:
        Maximum shape of all dimensions >= 1 (only new dataset).
        Default: same as ``shape``.
        The maxshape of the dataset is ``[None] + maxshape`` (``None`` is the extendable dimension).
    :param attrs: A dictionary with attributes.
    :param kwargs: Additional options for ``h5py.File.create_dataset`` (e.g. ``chunks``).
    """

    def __init__(
        self,
        file: h5py.File,
        name: str,
        shape: tuple[int, ...] = None,
        dtype=None,
        maxshape: tuple[int, ...] = None,
        attrs: dict = None,
        **kwargs,
    ):
        if maxshape is None:
            maxshape = shape

        if name in file:
            self.dset = file[name]
            self.shape = list(self.dset.shape[1:])
            if shape is not None:
                assert list(shape) == self.shape, "shape mismatch"
            if maxshape is not None:
                assert list(self.dset.maxshape) == [None] + list(maxshape), "maxshape mismatch"
            else:
                assert self.dset.maxshape[0] is None, "maxshape mismatch"
        else:
            assert dtype is not None, "dtype must be specified for new datasets"
            assert shape is not None, "shape must be specified for new datasets"
            self.shape = list(shape)
            self.dset = file.create_dataset(
                name=name,
                shape=[0] + self.shape,
                maxshape=[None] + list(maxshape),
                dtype=dtype,
                **kwargs,
            )

        if attrs is not None:
            for attr in attrs:
                self.dset.attrs[attr] = attrs[attr]

        self.dset.parent.file.flush()

    def append(self, data: ArrayLike):
        """
        Add new slice to the dataset.

        :param data: The "slice" to append.
        """
        return self.setitem(self.dset.shape[0], data)

    def __add__(self, data: ArrayLike):
        return self.append(data)

    def setitem(self, index, data: ArrayLike):
        """
        Overwrite a slice of the dataset.

        .. note::

            This immediately writes to the dataset and flushes the file.

        :param index: The index of the slice.
        :param data: The "slice" to append.
        """
        if np.isscalar(index):
            idx = index
        else:
            idx = index[0]

        if idx < 0:
            self.dset[index] = data
            self.dset.parent.file.flush()
            return self

        if idx >= self.dset.shape[0]:
            self.dset.resize([idx + 1] + self.shape)

        self.dset[index] = data
        self.dset.parent.file.flush()
        return self

    def __setitem__(self, index, data: ArrayLike):
        return self.setitem(index, data)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class ExtendableList:
    """
    Write extendable list to HDF5 file.

    For example::

        data = np.random.random([100])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", np.float64) as dset:
                for d in data:
                    dset.append(d)

    :param file: Opened HDF5 file (in write mode).
    :param name: Path to the dataset.
    :param dtype: Data-type to use (only new dataset).
    :param buffer: Buffer size: flush file after this many entries.
    :param attrs: A dictionary with attributes.
    :param kwargs: Additional options for ``h5py.File.create_dataset`` (e.g. ``chunks``).
    """

    def __init__(
        self,
        file: h5py.File,
        name: str,
        dtype=None,
        buffer: int = None,
        attrs: dict = None,
        **kwargs,
    ):
        self.buffer = buffer
        if self.buffer is not None:
            self.data = np.empty(buffer, dtype=dtype)
        self.i = 0

        if name in file:
            self.dset = file[name]
        else:
            assert dtype is not None, "dtype must be specified for new datasets"
            self.dset = file.create_dataset(
                name=name,
                shape=(0,),
                maxshape=(None,),
                dtype=dtype,
                **kwargs,
            )

        if attrs is not None:
            for attr in attrs:
                self.dset.attrs[attr] = attrs[attr]

        self.dset.parent.file.flush()

    def _flush_full_buffer(self):
        """
        Flush the buffer if the buffer is full.
        """
        if self.i == self.buffer:
            return self.flush()
        return self

    def flush(self):
        """
        Flush the buffer.
        """
        if self.i > 0:
            self.dset.resize((self.dset.size + self.i,))
            self.dset[-self.i :] = self.data[: self.i]
            self.i = 0
            self.dset.parent.file.flush()
        return self

    def append(self, data: int | float | ArrayLike):
        """
        Add new entry or slice to the dataset.

        .. note::

            If a list or array is appended the data is directly written to the dataset.
            The file and buffer are flushed immediately.

            In other cases, the data is first written to a buffer.
            The data is only written to the dataset when the buffer is full.
            At that point, the file is flushed.

        :param data: The data to append.
        """
        if isinstance(data, list) or isinstance(data, np.ndarray):
            self.flush()
            n = len(data)
            self.dset.resize((self.dset.size + n,))
            self.dset[-n:] = data
            self.dset.parent.file.flush()
            return self

        if self.buffer is None:
            return self.setitem(self.dset.size, data)

        self.data[self.i] = data
        self.i += 1
        return self._flush_full_buffer()

    def __add__(self, data: ArrayLike):
        return self.append(data)

    def setitem(self, index, data: ArrayLike):
        """
        Overwrite and item or a slice of the dataset.

        .. note::

            This immediately writes to the dataset and flushes the file.

        :param index: The index of the item of the slice.
        :param data: A value or a "slice" of data.
        """
        self.flush()

        if isinstance(index, slice):
            size = None
            start = index.start
            stop = index.stop
            step = index.step
            if step is None:
                step = 1

            if start is None and stop is None:
                size = data.size * step
            else:
                if stop is None:
                    stop = start + data.size * step
                if start is None:
                    start = stop - data.size * step
                if start > 0 and stop > 0:
                    size = stop

            if size is not None:
                assert self.dset.size <= size, "cannot shrink dataset"
                if self.dset.size < size:
                    self.dset.resize((size,))
            self.dset[index] = data
            self.dset.parent.file.flush()
            return self

        if index is Ellipsis:
            assert self.dset.size <= data.size, "cannot shrink dataset"
            if self.dset.size < data.size:
                self.dset.resize((data.size,))
            self.dset[index] = data
            self.dset.parent.file.flush()
            return self

        assert np.isscalar(index), "index must be scalar or slice"
        if index >= self.dset.size:
            self.dset.resize((index + 1,))
        self.dset[index] = data
        self.dset.parent.file.flush()
        return self

    def __setitem__(self, index, data: ArrayLike):
        return self.setitem(index, data)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.flush()


def create_extendible(
    file: h5py.File, name: str, dtype, attrs: dict = {}, **kwargs
) -> h5py.Dataset:
    """
    Create extendible dataset.

    :param file: Opened HDF5 file.
    :param name: Path to the dataset.
    :param dtype: Data-type to use.
    :param attrs: An optional dictionary with attributes.
    :param kwargs:
        Additional options for ``h5py.File.create_dataset``.
        If not specified, ``shape = [0] * ndim`` and ``maxshape = [None] * ndim``.
        If you you specify ``shape`` or ``maxdim``, ``ndim`` can be omitted.
    """

    if name in file:
        return file[name]

    if "ndim" in kwargs:
        ndim = kwargs.pop("ndim")
    else:
        ndim = len(kwargs["shape"]) if "shape" in kwargs else len(kwargs["maxshape"])

    shape = kwargs.pop("shape", tuple(0 for i in range(ndim)))
    maxshape = kwargs.pop("maxshape", tuple(None for i in range(ndim)))
    dset = file.create_dataset(name=name, shape=shape, maxshape=maxshape, dtype=dtype, **kwargs)

    for attr in attrs:
        dset.attrs[attr] = attrs[attr]

    return dset


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


def getdatapaths(
    file: h5py.File,
    root: str = "/",
    max_depth: int = None,
    fold: str | list[str] = None,
    fold_symbol: str = "/...",
) -> list[str]:
    """
    Get paths to all dataset and groups that contain attributes.

    .. warning::

        :py:func:`getgroups` visits all groups in the file,
        regardless if they are folded (by ``fold`` or ``max_depth``).
        Depending on the file, this can be quite costly.
        If runtime is an issue consider searching for datasets only using :py:func:`getdatasets`
        if your use-case allows it.

    :param file: A HDF5-archive.
    :param root: Start a certain point along the path-tree.
    :param max_depth: Set a maximum depth beyond which groups are folded.
    :param fold: Specify groups that are folded.
    :param fold_symbol: Use symbol to indicate that a group is folded.
    :return: List of paths (always absolute, so includes the ``root`` if used).
    """
    kwargs = dict(root=root, max_depth=max_depth, fold=fold, fold_symbol=fold_symbol)
    ret = list(getdatasets(file, **kwargs)) + list(getgroups(file, has_attrs=True, **kwargs))
    return list(set(ret))


def getgroups(
    file: h5py.File,
    root: str = "/",
    has_attrs: bool = False,
    max_depth: int = None,
    fold: str | list[str] = None,
    fold_symbol: str = "/...",
) -> list[str]:
    """
    Paths of all groups in a HDF5-archive.

    .. warning::

        The function visits all groups in the file,
        regardless if they are folded (by ``fold`` or ``max_depth``).
        Depending on the file, this can be quite costly.

    :param file: A HDF5-archive.
    :param root: Start at a certain point along the path-tree.
    :param has_attrs: Return only groups that have attributes.
    :param int max_depth: Set a maximum depth beyond which groups are folded.
    :param fold: Specify groups that are folded.
    :param fold_symbol: Use symbol to indicate that a group is folded.
    :return: List of paths (always absolute, so includes the ``root`` if used).
    """

    root = abspath(root)

    if fold:
        if type(fold) is str:
            fold = [abspath(fold)]
        else:
            fold = [abspath(f) for f in fold]
        fold = [f if f.startswith(root) else join(root, f) for f in fold]

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
                keys[i] = posixpath.join("/", *path.split("/")[: n + max_depth + 1]) + fold_symbol
        keys = list(set(keys))

    if fold is not None:
        if type(fold) is str:
            fold = [fold]
        for i, path in enumerate(keys):
            for f in fold:
                if path.startswith(f):
                    keys[i] = f + fold_symbol
        keys = list(set(keys))

    return keys


def getdatasets(
    file: h5py.File,
    root: str = "/",
    max_depth: int = None,
    fold: str | list[str] = None,
    fold_symbol: str = "/...",
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
    :param fold_symbol: Use symbol to indicate that a group is folded.
    :return: Iterator to paths (always absolute, so includes the ``root`` if used).

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

    root = abspath(root)

    if fold:
        if type(fold) is str:
            fold = [abspath(fold)]
        else:
            fold = [abspath(f) for f in fold]
        fold = [f if f.startswith(root) else join(root, f) for f in fold]

    if max_depth and fold:
        return _getpaths_fold_maxdepth(file, root, fold, max_depth, fold_symbol)

    if max_depth:
        return _getpaths_maxdepth(file, root, max_depth, fold_symbol)

    if fold:
        return _getpaths_fold(file, root, fold, fold_symbol)

    return _getpaths(file, root)


def _getpaths(file, root):
    """
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


def _getpaths_maxdepth(file, root, max_depth, fold_symbol):
    """
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
                    yield path + fold_symbol
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


def _getpaths_fold(file, root, fold, fold_symbol):
    """
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
                yield path + fold_symbol

            elif isinstance(item, h5py.Group):
                yield from iterator(item, path, fold)

    # ---------------------------------------------

    if isinstance(fold, str):
        fold = [fold]

    if isinstance(file[root], h5py.Dataset):
        yield root

    yield from iterator(file[root], root, fold)


def _getpaths_fold_maxdepth(file, root, fold, max_depth, fold_symbol):
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
                yield path + fold_symbol

            elif path in fold:
                yield path + fold_symbol

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


def copy(
    source: h5py.File,
    dest: h5py.File,
    source_paths: list[str],
    dest_paths: list[str] = None,
    root: str = None,
    source_root: str = None,
    skip: bool = False,
    preserve_soft: bool = False,
    shallow: bool = False,
    expand_soft: bool = False,
    expand_external: bool = False,
    expand_refs: bool = False,
    without_attrs: bool = False,
):
    """
    Copy groups/datasets from one HDF5-archive ``source`` to another HDF5-archive ``dest``.
    The datasets can be renamed by specifying a list of ``dest_paths``
    (whose entries should correspond to the ``source_paths``).
    In addition, a ``root`` path prefix can be specified for the destination datasets.
    Likewise, a ``source_root`` path prefix can be specified for the source datasets.

    For the options ``shallow``, ``expand_soft``, ``expand_external``, ``expand_refs``,
    ``without_attrs`` see:
    `h5py.Group.copy <https://docs.h5py.org/en/stable/high/group.html#h5py.Group.copy>`_.

    :param source: The source HDF5-archive.
    :param dest: The destination HDF5-archive.
    :param source_paths: List of dataset-paths in ``source``.
    :param dest_paths: List of dataset-paths in ``dest``, defaults to ``source_paths``.
    :param root: Path prefix for all ``dest_paths``.
    :param source_root: Path prefix for all ``source_paths``.
    :param skip: Skip datasets that are not present in source.
    :param preserve_soft: Preserve soft links.
    :param shallow: Only copy immediate members of a group.
    :param expand_soft: Expand soft links into new objects.
    :param expand_external: Expand external links into new objects.
    :param expand_refs: Copy objects which are pointed to by references.
    :param without_attrs: Copy object(s) without copying HDF5 attributes.
    """

    if len(source_paths) == 0:
        return

    if type(source_paths) is str:
        source_paths = [source_paths]
    if type(dest_paths) is str:
        dest_paths = [dest_paths]

    source_paths = np.array([abspath(path) for path in source_paths])

    if not dest_paths:
        dest_paths = source_paths.copy()
    else:
        dest_paths = np.array([abspath(path) for path in dest_paths])

    if skip:
        keep = [i in source for i in source_paths]
        source_paths = source_paths[keep]
        dest_paths = dest_paths[keep]

    if root:
        root = abspath(root)
        dest_paths = np.array([join(root, path) for path in dest_paths])

    if source_root:
        source_root = abspath(source_root)
        source_paths = np.array([join(source_root, path) for path in source_paths])

    for path in source_paths:
        if path not in source:
            raise OSError(f'Dataset "{path}" does not exists in source.')

    for path in dest_paths:
        if path in dest:
            raise OSError(f'Dataset "{path}" already exists in dest.')

    if len(source_paths) == 0:
        return 0

    _create_groups(dest, dest_paths)
    isgroup = np.array([isinstance(source[path], h5py.Group) for path in source_paths])
    keep = np.ones(len(source_paths), dtype=bool)
    if shallow:
        keep[isgroup] = False

    for source_path, dest_path in zip(source_paths[keep], dest_paths[keep]):
        if dest_path in dest:
            continue
        if preserve_soft:
            link = source.get(source_path, getlink=True)
            if isinstance(link, h5py.SoftLink):
                dest[dest_path] = h5py.SoftLink(link.path)
                continue
        group = posixpath.split(dest_path)[0]
        source.copy(
            source=source_path,
            dest=dest[group],
            name=posixpath.split(dest_path)[1],
            shallow=shallow,
            expand_soft=expand_soft,
            expand_external=expand_external,
            expand_refs=expand_refs,
            without_attrs=without_attrs,
        )

    for source_path, dest_path in zip(source_paths[isgroup], dest_paths[isgroup]):
        if dest_path not in dest:
            dest_group = dest.create_group(dest_path)
        else:
            dest_group = dest[dest_path]
        source_group = source[source_path]
        for key in source_group.attrs:
            dest_group.attrs[key] = source_group.attrs[key]


def isnumeric(a):
    """
    Returns ``True`` is an array contains numeric values.

    :param array a: An array.
    :return: bool
    """

    import numpy as np

    if isinstance(a, str):
        return False

    if np.issubdtype(a.dtype, np.number):
        return True

    return False


def _equal_value(a, b, close):
    import numpy as np

    if isinstance(a, str):
        if isinstance(b, str):
            return a == b
        else:
            return False

    if a.size != b.size:
        return False

    if list(a.shape) != list(b.shape):
        return False

    if np.issubdtype(a.dtype, np.floating):
        if close:
            return np.allclose(a, b)
        if not np.issubdtype(b.dtype, np.floating):
            return False
        if np.allclose(a, b):
            return True
        return False

    if np.issubdtype(a.dtype, np.integer):
        if close:
            return np.allclose(a, b)
        if not np.issubdtype(b.dtype, np.integer):
            return False
        if a.shape != b.shape:
            return False
        if np.all(np.equal(a, b)):
            return True
        return False

    if a.dtype == np.bool_:
        if b.dtype != np.bool_:
            return False
        if a.shape != b.shape:
            return False
        if np.all(np.equal(a, b)):
            return True
        return False

    if a.size == 1:
        if a[...] == b[...]:
            return True
        else:
            return False

    if close:
        return np.allclose(np.array(list(a[...])), np.array(list(b[...])))

    return np.all(np.array(list(a[...])) == np.array(list(b[...])))


def _equal(a, b, attrs, matching_dtype, shallow, close):
    if attrs:
        for key in a.attrs:
            if key not in b.attrs:
                return False
            if matching_dtype:
                if a.attrs[key].dtype != b.attrs[key].dtype:
                    return False
            if shallow:
                return True
            if not _equal_value(a.attrs[key], b.attrs[key], close):
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

    return _equal_value(a, b, close)


def equal(
    source: h5py.File,
    dest: h5py.File,
    source_dataset: str,
    dest_dataset: str = None,
    root: str = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
    close: bool = False,
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
    :param close: Use ``np.isclose`` also on ``float``-``int`` matches.
    """

    if not dest_dataset:
        dest_dataset = source_dataset

    if root is not None:
        dest_dataset = join(root, dest_dataset, root=True)

    if source_dataset not in source:
        raise OSError(f'"{source_dataset:s} not in {source.filename:s}')

    if dest_dataset not in dest:
        raise OSError(f'"{dest_dataset:s} not in {dest.filename:s}')

    return _equal(source[source_dataset], dest[dest_dataset], attrs, matching_dtype, shallow, close)


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
    a: h5py.File,
    b: h5py.File,
    paths_a: list[str],
    paths_b: list[str],
    attrs: bool,
    max_depth: int,
    fold: str[list],
) -> type[list[str], list[str]]:
    """
    Default paths for :py:func:`compare`.
    """

    if fold:
        if isinstance(fold, str):
            fold = [fold]

    symbol = "/..." + str(uuid.uuid4())
    fold_a = []
    fold_b = []

    if paths_b is None and paths_a is not None:
        paths_b = paths_a

    if paths_a is None:
        if attrs:
            paths_a = getdatapaths(a, max_depth=max_depth, fold=fold, fold_symbol=symbol)
        else:
            paths_a = list(getdatasets(a, max_depth=max_depth, fold=fold, fold_symbol=symbol))

    if paths_b is None:
        if attrs:
            paths_b = getdatapaths(b, max_depth=max_depth, fold=fold, fold_symbol=symbol)
        else:
            paths_b = list(getdatasets(b, max_depth=max_depth, fold=fold, fold_symbol=symbol))

    if fold:
        fold = [join(f, symbol, root=True) for f in fold]

        for path in paths_a:
            if path in fold:
                paths_a.remove(path)
                fold_a.append(path.split(symbol)[0])

        for path in paths_b:
            if path in fold:
                paths_b.remove(path)
                fold_b.append(path.split(symbol)[0])

    return paths_a, paths_b, fold_a, fold_b


def compare_allow(
    comparison: dict[list], paths: list[str], keys: list[str] = ["->", "<-", "!="], root: str = None
) -> dict[list]:
    """
    Modify the output of :py:func:`compare` to allow specific differences.
    In practice this removes certain fields from the lists under specific keys in the dictionary.

    :param comparison: The output of :py:func:`compare`.
    :param paths: List of paths to allow.
    :param keys: List of comparison keys (``"->"``, ``"<-"``, ``"!="``).
    :param root: Path prefix for ``paths``.
    :return: The modified comparison dictionary.
    """

    ret = comparison.copy()

    if isinstance(paths, str):
        paths = [paths]

    if isinstance(keys, str):
        keys = [keys]

    if root is not None:
        paths = [join(root, path, root=True) for path in paths]

    for key in keys:
        for path in paths:
            if path in ret[key]:
                ret[key].remove(path)

    return ret


def compare(
    a: h5py.File,
    b: h5py.File,
    paths_a: list[str] = None,
    paths_b: list[str] = None,
    attrs: bool = True,
    matching_dtype: bool = False,
    shallow: bool = False,
    only_datasets: bool = False,
    max_depth: int = None,
    fold: str | list[str] = None,
    list_folded: bool = False,
    close: bool = False,
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

    .. warning::

        Folded groups are not compared in any way!
        Use `list_folded` to include this in the output.

    :param a: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param b: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param paths_a: Paths from ``a`` to consider. Default: read from :py:func:`getdatapaths`.
    :param paths_b: Paths from ``b`` to consider. Default: read from :py:func:`getdatapaths`.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of datasets, not their values, size, or attributes.
    :param only_datasets: Compare datasets only (not groups, regardless if they have attributes).
    :param max_depth: Set a maximum depth beyond which groups are folded.
    :param fold: Specify groups that are folded.
    :param list_folded: Return folded groups under `"??"`
    :param close: Use ``np.isclose`` also on ``float``-``int`` matches.
    :return: Dictionary with difference.
    """
    ret = {"<-": [], "->": [], "!=": [], "==": []}
    paths_a, paths_b, fold_a, fold_b = _compare_paths(
        a, b, paths_a, paths_b, False if only_datasets else attrs, max_depth, fold
    )

    not_in_b = [str(i) for i in np.setdiff1d(paths_a, paths_b)]
    not_in_a = [str(i) for i in np.setdiff1d(paths_b, paths_a)]
    inboth = [str(i) for i in np.intersect1d(paths_a, paths_b)]

    for path in not_in_a:
        ret["<-"].append(path)

    for path in not_in_b:
        ret["->"].append(path)

    opts = dict(attrs=attrs, matching_dtype=matching_dtype, shallow=shallow, close=close)

    for path in inboth:
        if not equal(a, b, path, **opts):
            ret["!="].append(path)
        else:
            ret["=="].append(path)

    if list_folded:
        ret["??"] = [str(i) for i in np.unique(fold_a + fold_b)]

    return ret


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
    only_datasets: bool = True,
    max_depth: int = None,
    fold: str | list[str] = None,
    list_folded: bool = False,
    close: bool = False,
) -> tuple[dict[list], dict[list], dict[list]]:
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

    .. warning::

        Folded groups are not compared in any way!
        Use `list_folded` to include this in the output.

    :param a: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param b: HDF5-archive (as opened ``h5py.File`` or with the ``filepath``).
    :param rename: List with with renamed pairs: ``[["/a/0", "/b/1"], ...]``.
    :param paths_a: Paths from ``a`` to consider. Default: read from :py:func:`getdatapaths`.
    :param paths_b: Paths from ``b`` to consider. Default: read from :py:func:`getdatapaths`.
    :param attrs: Compare attributes (the same way at datasets).
    :param matching_dtype: Check that not only the data but also the type matches.
    :param shallow: Check only the presence of datasets, not their values, size, or attributes.
    :param regex: Use regular expressions to match ``rename``.
    :param only_datasets: Compare datasets only (not groups, regardless if they have attributes).
    :param max_depth: Set a maximum depth beyond which groups are folded.
    :param fold: Specify groups that are folded.
    :param list_folded: Return folded groups under `"??"`
    :param close: Use ``np.isclose`` also on ``float``-``int`` matches.
    :return: Dictionary with difference.
    """

    opts = dict(
        attrs=attrs,
        matching_dtype=matching_dtype,
        shallow=shallow,
        max_depth=max_depth,
        fold=fold,
        list_folded=list_folded,
        close=close,
    )

    if rename is None:
        empty = {"!=": [], "==": []}
        return compare(a, b, paths_a, paths_b, **opts), empty, empty

    paths_a, paths_b, fold_a, fold_b = _compare_paths(
        a, b, paths_a, paths_b, False if only_datasets else attrs, max_depth, fold
    )

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

    opts.pop("max_depth")
    opts.pop("fold")
    opts.pop("list_folded")

    for path_a, path_b in zip(rename_a, rename_b):
        if not equal(a, b, path_a, path_b, **opts):
            ret_a["!="].append(path_a)
            ret_b["!="].append(path_b)
        else:
            ret_a["=="].append(path_a)
            ret_b["=="].append(path_b)

    if list_folded:
        ret["??"] = [str(i) for i in np.unique(fold_a + fold_b)]

    return ret, ret_a, ret_b


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

    If you have a really big file:

    *   The ``--layer`` option can be much faster than searching the entire file.

    *   Search only ``--datasets`` when folding can be much faster.
        The ``getgroups`` function does search the entire depth.
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
    opts = dict(root=args.root, max_depth=args.max_depth, fold=args.fold)

    if not os.path.isfile(args.source):
        raise OSError(f'"{args.source}" does not exist')

    with h5py.File(args.source, "r") as source:
        if args.layer is not None:
            paths = sorted(join(args.layer, i, root=True) for i in source[args.layer])
        else:
            paths = list(getdatasets(source, **opts))
            if not args.datasets:
                paths += getgroups(source, has_attrs=True, **opts)
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
        "--close", action="store_true", help="Use ``np.isclose`` also on ``float``-``int`` matches."
    )
    parser.add_argument(
        "--shallow",
        action="store_true",
        help="Only check for the presence of datasets and attributes. Do not check their values.",
    )
    parser.add_argument("-D", "--datasets", action="store_true", help="Print only datasets")
    parser.add_argument("-d", "--max-depth", type=int, help="Maximum depth to display")
    parser.add_argument("-f", "--fold", action="append", help="Fold paths")
    parser.add_argument("-r", "--renamed", nargs=2, action="append", help="Renamed paths.")
    parser.add_argument("-R", "--renamed-yaml", type=str, help="YAML file with renamed paths.")
    parser.add_argument("-c", "--colors", default="dark", help="Color theme: dark/light/none")
    parser.add_argument("--table", default="SINGLE_BORDER", help="Table theme")
    parser.add_argument("-I", "--input", action="store_true", help="Header identical to input")
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument("a", help="Path to HDF5-file.")
    parser.add_argument("b", help="Path to HDF5-file.")
    return parser


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

    if filecmp.cmp(args.a, args.b):
        print("Files are identical")
        return 0

    if args.renamed_yaml is not None:
        with open(args.renamed_yaml) as file:
            ret = yaml.load(file.read(), Loader=yaml.FullLoader)
        assert type(ret) is dict
        if args.renamed is None:
            args.renamed = []
        args.renamed += [[key, ret[key]] for key in ret]

    with h5py.File(args.a, "r") as a, h5py.File(args.b, "r") as b:
        comp, r_a, r_b = compare_rename(
            a,
            b,
            rename=args.renamed,
            matching_dtype=args.dtype,
            shallow=args.shallow,
            regex=True,
            only_datasets=args.datasets,
            fold=args.fold,
            max_depth=args.max_depth,
            list_folded=True,
            close=args.close,
        )

    def def_row(arg, colors):
        if colors == "none":
            if arg[1] == "!=":
                return arg
            if arg[1] == "->":
                return [arg[0], arg[1], ""]
            if arg[1] == "<-":
                return ["", arg[1], arg[2]]
            if arg[1] == "??":
                return [arg[0], arg[1], arg[2]]
            if arg[1] != "==":
                raise ValueError(f"Unknown operator {arg[1]}")

        if arg[1] == "!=":
            opts = dict(color="cyan", attrs=["bold"])
            return [colored(arg[0], **opts), arg[1], colored(arg[2], **opts)]
        if arg[1] == "->":
            return [colored(arg[0], "red", attrs=["bold", "concealed"]), arg[1], ""]
        if arg[1] == "<-":
            return ["", arg[1], colored(arg[2], "green", attrs=["bold"])]
        if arg[1] == "??":
            opts = dict(color="magenta", attrs=["bold"])
            return [colored(arg[0], **opts), arg[1], colored(arg[2], **opts)]
        if arg[1] != "==":
            raise ValueError(f"Unknown operator {arg[1]}")

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

    if len(out.rows) == 0:
        print("No differences found")
        return

    cols = [args.a, args.b]

    if not args.input:
        sizes = [max(len(row[0]) for row in out.rows), max(len(row[2]) for row in out.rows)]

        if (len(cols[0]) > sizes[0] or len(cols[1]) > sizes[1]) and (
            len(cols[0]) + len(cols[1]) > 90
        ):
            trial = [os.path.abspath(i) for i in cols]
            s = SequenceMatcher(None, *trial).get_matching_blocks()[0].size
            for i in range(2):
                n = len(trial[i][s:].split(os.sep))
                cols[i] = os.path.join(*(["..."] + trial[i].split(os.sep)[-n:]))

    out.field_names = [cols[0], "", cols[1]]
    print(out.get_string())


def _G5modify_parser():
    """
    Return parser for :py:func:`G5modify`.
    """

    desc = "Modify a variable."
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("-v", "--version", action="version", version=version)
    parser.add_argument(
        "--shape", type=str, help="Shape of the dataset separated by commas (only for new dataset)."
    )
    parser.add_argument(
        "--dtype", type=str, default="f", help="Data type of the dataset (only for new dataset)."
    )
    parser.add_argument("file", help="Filepath of the HDF5-file.")
    parser.add_argument("path", help="Path in the HDF5-file.")
    parser.add_argument("values", nargs="*", type=float, help="Values to set.")
    return parser


def G5modify(args: list[str]):
    """
    Command-line tool to print datasets from a file, see ``--help``.
    :param args: Command-line arguments (should be all strings).
    """

    parser = _G5modify_parser()
    args = parser.parse_args(args)

    if not os.path.isfile(args.file):
        raise OSError(f'"{args.file}" does not exist')

    with h5py.File(args.file, "r+") as file:
        if args.path not in file:
            shape = [len(args.values)]
            if args.shape:
                shape = [int(i) for i in args.shape.split(",")]
            assert np.prod(shape) == len(args.values)
            file.create_dataset(args.path, shape=shape, dtype=args.dtype)

        else:
            assert len(args.values) == file[args.path].size

        file[args.path][:] = np.array(args.values).reshape(file[args.path].shape)


def _G5print_cli():
    G5print(sys.argv[1:])


def _G5list_cli():
    G5list(sys.argv[1:])


def _G5compare_cli():
    G5compare(sys.argv[1:])


def _G5modify_cli():
    G5modify(sys.argv[1:])
