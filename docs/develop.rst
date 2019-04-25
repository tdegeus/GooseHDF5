
********************
Notes for developers
********************

Make changes / additions
========================

Be sure to run and verify all examples! All existing examples should pass, while new examples should be added to document and check any new functionality.

Create a new release
====================

1.  Update the version numbers by modifying ``__version__`` in ``setup.py``, ``GOOSEHDF5_VERSION_NUMBER`` in ``CMakeLists.txt`` and the version numbers in the command-line tools.

2.  Upload the changes to GitHub and create a new release there (with the correct version number).

3.  Upload the package to PyPi:

    .. code-block:: bash

      $ python3 setup.py bdist_wheel --universal
      $ twine upload dist/*

.. note::

  Get ``twine`` by

  .. code-block:: bash

    python3 -m pip install --user --upgrade twine

  Be sure to follow the possible directives about setting the user's path.

