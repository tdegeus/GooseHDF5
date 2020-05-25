
.. _tools:

******************
Command-line tools
******************

G5check
-------

[:download:`G5check <../GooseHDF5/cli/G5check.py>`]

.. code-block:: none

    G5check
        Try reading datasets. In case of reading failure the path is printed (otherwise nothing is
        printed).

    Usage:
        G5check <source> [options]

    Arguments:
        <source>        HDF5-file.

    Options:
        -b, --basic     Only try getting a list of datasets, skip trying to read them.
        -h, --help      Show help.
            --version   Show version.

G5list
------

[:download:`G5list <../GooseHDF5/cli/G5list.py>`]

.. code-block:: none

    G5list
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

G5print
------

[:download:`G5print <../GooseHDF5/cli/G5print.py>`]

.. code-block:: none

    G5print
        Print datasets in a HDF5-file.

    Usage:
        G5print [options] <source> [<dataset>...]

    Arguments:
        <source>    HDF5-file.
        <dataset>   Path to the dataset.

    Options:
        -r, --regex     Evaluate dataset name as a regular expression.
        -i, --info      Print information: shape, dtype.
        -h, --help      Show help.
            --version   Show version.

G5repair
--------

[:download:`G5repair <../GooseHDF5/cli/G5repair.py>`]

.. code-block:: none

    G5repair
        Extract readable data from a HDF5-file and copy it to a new HDF5-file.

    Usage:
        G5repair [options] <source> <destination>

    Arguments:
        <source>        Source HDF5-file, possibly containing corrupted data.
        <destination>   Destination HDF5-file.

    Options:
        -f, --force     Force continuation, overwrite existing files.
        -h, --help      Show help.
            --version   Show version.

G5compare
---------

[:download:`G5compare <../GooseHDF5/cli/G5compare.py>`]

.. code-block:: none

    G5compare
      Compare two HDF5 files. If the function does not output anything all datasets are present in both
      files, and all the content of the datasets is equals

    Usage:
      G5compare [options] [--renamed ARG]... <source> <other>

    Arguments:
      <source>    HDF5-file.
      <other>     HDF5-file.

    Options:
      -r, --renamed=ARG     Renamed paths, separated by a separator (see below).
      -s, --ifs=ARG         Separator used to separate renamed fields. [default: :]
      -h, --help            Show help.
          --version         Show version.

G5repack
---------

[:download:`G5repack <../GooseHDF5/cli/G5repack.py>`]

.. code-block:: none

    G5repack
        Read and write a HDF5 file, to write it more efficiently by removing features like
        extendible datasets.

    Usage:
        G5repack [options] <source>...

    Arguments:
        <source>    HDF5-file.

    Options:
        -c, --compress  Apply compression (using the loss-less GZip algorithm).
        -h, --help      Show help.
            --version   Show version.
