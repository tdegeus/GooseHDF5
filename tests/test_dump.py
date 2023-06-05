import os
import pathlib
import shutil
import tempfile
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


class Test_iterator(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.origin = pathlib.Path().absolute()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    @classmethod
    def tearDownClass(self):
        os.chdir(self.origin)
        shutil.rmtree(self.tempdir)

    def test_dump(self):
        A = {
            "foo": {"a": 1, "b": 2},
            "bar": {"a": 3, "b": 4},
        }

        paths = []

        for a in A:
            for b in A[a]:
                paths.append(f"/{a}/{b}")

        with h5py.File("foo.h5", "w") as file:
            g5.dump(file, A)

            self.assertEqual(sorted(g5.getdatasets(file)), sorted(paths))

            for a in A:
                for b in A[a]:
                    self.assertEqual(file[a][b][...], A[a][b])


class Test_Extendable(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.origin = pathlib.Path().absolute()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    @classmethod
    def tearDownClass(self):
        os.chdir(self.origin)
        shutil.rmtree(self.tempdir)

    def test_ExtendableList_append(self):
        data = np.random.random([100])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype, chunk=9) as dset:
                for d in data:
                    dset.append(d)

            self.assertTrue(np.allclose(data, file["foo"][...]))

    def test_ExtendableList_add(self):
        data = np.random.random([10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype, chunk=9) as dset:
                for d in data:
                    dset += d

            self.assertTrue(np.allclose(data.ravel(), file["foo"][...]))

    def test_ExtendableList_existing(self):
        dataset = np.random.random([10, 100])

        with h5py.File("foo.h5", "w") as file:
            for data in dataset:
                with g5.ExtendableList(file, "foo", data.dtype, chunk=9) as dset:
                    for d in data:
                        dset.append(d)

            self.assertTrue(np.allclose(dataset.ravel(), file["foo"][...]))

    def test_ExtendableSlice_add(self):
        data = np.random.random([6, 10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", data.shape[1:], data.dtype) as dset:
                for d in data[:3, ...]:
                    dset += d

            with g5.ExtendableSlice(file, "foo") as dset:
                for d in data[3:, ...]:
                    dset += d

            self.assertTrue(np.allclose(data, file["foo"][...]))


if __name__ == "__main__":
    unittest.main()
