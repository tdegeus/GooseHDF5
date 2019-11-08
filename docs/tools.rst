
.. _tools:

******************
Command-line tools
******************

.. note::

  These tools use Python an depend ``GooseHDF5``, ``h5py``, and ``docopt``. Get these tools for example using

  .. code-block:: bash

    pip3 install h5py doctopt GooseHDF5

G5check
-------

[:download:`G5check <../bin/G5check>`]

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

[:download:`G5list <../bin/G5list>`]

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
    -h, --help            Show help.
        --version         Show version.

G5repair
--------

[:download:`G5repair <../bin/G5repair>`]

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

[:download:`G5compare <../bin/G5compare>`]

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
