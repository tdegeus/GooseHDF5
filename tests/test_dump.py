import os
import shutil
import unittest

import h5py

import GooseHDF5 as g5


class Test_itereator(unittest.TestCase):
    def test_dump(self):

        dirname = "mytest"
        filepath = os.path.join(dirname, "bar.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        A = {
            "foo": {"a": 1, "b": 2},
            "bar": {"a": 3, "b": 4},
        }

        paths = []

        for a in A:
            for b in A[a]:
                paths.append(f"/{a}/{b}")

        with h5py.File(filepath, "w") as file:

            g5.dump(file, A)

            self.assertEqual(sorted(g5.getdatasets(file)), sorted(paths))

            for a in A:
                for b in A[a]:
                    self.assertEqual(file[a][b][...], A[a][b])

        shutil.rmtree(dirname)


if __name__ == "__main__":

    unittest.main()
