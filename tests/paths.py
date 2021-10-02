import os
import shutil
import unittest

import h5py
import numpy as np
import GooseHDF5 as g5


class Test_itereator(unittest.TestCase):
    def test_getdatasets(self):

        dirname = "mytest"
        filename = "foo.h5"
        filepath = os.path.join(dirname, filename)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        Datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(filepath, "w") as file:

            for d in Datasets:
                file[d] = [0, 1, 2]

            paths = list(g5.getdatasets(file))
            paths_c = list(g5.getpaths(file, root="/c"))

        self.assertEqual(sorted(Datasets), sorted(paths))
        self.assertEqual(sorted([Datasets[-1]]), sorted(paths_c))

        shutil.rmtree(dirname)


if __name__ == "__main__":

    unittest.main()
