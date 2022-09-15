********
Examples
********

Copy part of a file
====================

Suppose that you want to copy all but some dataset from a file.
In that case you can use

*   :py:meth:`GooseHDF5.getdatapaths`
*   :py:meth:`GooseHDF5.copy`

Consider the following example.

.. literalinclude:: examples/copy_modify-selection.py
   :language: python

.. note::

   The copy functions from *h5py* copy attributes as well.
   By extension also :py:meth:`GooseHDF5.copy` copies all attributes.
