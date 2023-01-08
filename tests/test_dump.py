import pathlib
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5

root = pathlib.Path(__file__).parent
testdir = root / "mytest"


class Test_iterator(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        testdir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(testdir)

    def test_dump(self):

        A = {
            "foo": {"a": 1, "b": 2},
            "bar": {"a": 3, "b": 4},
        }

        paths = []

        for a in A:
            for b in A[a]:
                paths.append(f"/{a}/{b}")

        with h5py.File(testdir / "foo.h5", "w") as file:

            g5.dump(file, A)

            self.assertEqual(sorted(g5.getdatasets(file)), sorted(paths))

            for a in A:
                for b in A[a]:
                    self.assertEqual(file[a][b][...], A[a][b])


class Test_ExtendableList(unittest.TestCase):
    """
    Test the extendable list class
    """

    @classmethod
    def setUpClass(self):
        testdir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(testdir)

    def test_append(self):

        data = np.random.random([100])

        with h5py.File(testdir / "foo.h5", "w") as file:

            with g5.ExtendableList(file, "foo", data.dtype, chunk=9) as dset:
                for d in data:
                    dset.append(d)

            self.assertTrue(np.allclose(data, file["foo"][...]))

    def test_add(self):

        data = np.random.random([10, 10])

        with h5py.File(testdir / "foo.h5", "w") as file:

            with g5.ExtendableList(file, "foo", data.dtype, chunk=9) as dset:
                for d in data:
                    dset += d

            self.assertTrue(np.allclose(data.ravel(), file["foo"][...]))


if __name__ == "__main__":

    unittest.main()
