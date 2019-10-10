
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

G5merge
-------

[:download:`G5merge <../bin/G5merge>`]

.. code-block:: none

  G5merge
    Merge an entire HDF5-file into another HDF5-file: copy all datasets from <source> to some root
    in <destination>. The root is based on the path of <source>, as it is specified:

    * without extension (default)
    * only directory name (--dirname)
    * as specified (--ext)
    * apply some regex substitution (--find ... --replace ...)

  Usage:
    G5merge [options] <source> <destination>

  Arguments:
    <source>            Source HDF5-file.
    <destination>       Destination HDF5-file (appended).

  Options:
        --ext           Include extension of <source> in root.
        --dirname       Use only directory name of <source> in root.
    -f, --find=ARG      Regex search  to apply to <source>.
    -r, --replace=ARG   Regex replace to apply to <source>.
    -p, --root=ARG      Manually set root.
         --rm           Remove <source> after successful copy.
    -d, --dry-run       Dry run.
        --verbose       Verbose operations.
    -h, --help          Show help.
        --version       Show version.

.. tip::

  To merge a bunch of files one could use:

  .. code-block:: bash

    find . -iname '*.hdf5' -exec G5merge {} output.hdf5 \;

  In this case ``G5merge`` is called for each HDF5-file that is found. Note that if ``output.hdf5`` already existed, it is skipped by ``G5merge``.

G5select
--------

[:download:`G5select <../bin/G5select>`]

.. code-block:: none

  G5select
    Select datasets (or groups of datasets) from a HDF5-file and store to a new HDF5-file.

  JSON:
    The input can be a JSON file that looks like:

      {
        "/new/path" : "/old/path",
        ...
      }

  Usage:
    G5select [options] [--path ARG]... <source> <destination>

  Arguments:
    <source>          Source HDF5-file.
    <destination>     Destination HDF5-file (appended).

  Options:
    -p, --path=ARG    Pair of paths: "/destination/path;/source/path".
    -j, --json=ARG    JSON file with contains the path change.
        --sep=ARG     Set path separator. [default: ;]
    -f, --force       Force continuation, continue also if this operation discards fields.
        --verbose     Verbose operations.
    -h, --help        Show help.
        --version     Show version.

G5find
------

[:download:`G5find <../bin/G5find>`]

.. code-block:: none

  G5find
    Function, loosely based on Linux' find, that searches datasets in a HDF5 file. It allows to
    execute both file operations and basic dataset manipulations.

  Usage:
    G5find <source> [options]

  Arguments:
    <source>    HDF5-file.

  Options:
        --iname=ARG       Search for dataset, ignoring the case.
        --find=ARG        Find. [default: (.*)]
        --remove          Remove command.
        --not             Execute command only if there are no matches.
        --dry-run         Perform a dry-run.
        --verbose         Print file-path.
    -h, --help            Show help.
        --version         Show version.

.. tip::

  To remove all files that do not contain a dataset called "completed":

  .. code-block:: bash

    find . -iname '*.hdf5' -exec G5find {} --not --iname "completed" --remove \;

.. tip::

  To rename the directory that contains a HDF5-file, if that file contains a dataset called "completed":

  .. code-block:: bash

    mv_regex --dirname "(id\=[0-9]{3})([A-Z])" "\1C" `G5find --iname "completed" id=000Q/data.hdf5`

  (takes directories ``id=000Q``, ``id=001Q``, ... and renames them to ``id=000C``, ``id=001C``, ...).

G5compare
---------

[:download:`G5compare <../bin/G5compare>`]

.. code-block:: none

  G5compare
    Compare two HDF5 files. If the function does not output anything all datasets are present in both
    files, and all the content of the datasets is equals

  Usage:
    G5compare [options] <source> <other>

  Arguments:
    <source>    HDF5-file.
    <other>     HDF5-file.

  Options:
    -h, --help            Show help.
        --version         Show version.

