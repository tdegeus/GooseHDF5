********
Examples
********

Copy almost all files
=====================

Suppose that you want to copy all but some dataset from a file.
In that case you can use

*   :py:meth:`GooseHDF5.getdatasets` to get a list of all datasets.
*   :py:meth:`GooseHDF5.copydatasets` to copy a bunch of datasets.

Consider the following example.

.. literalinclude:: examples/copy_modify-selection.py
   :language: python

.. warning::

    The copy functions from *h5py* copy attributes as well.
    By extension also :py:meth:`GooseHDF5.copydatasets` copies all attributes.
    If you manipulate data yourself you will want to make sure that copy the relevant attributes.
