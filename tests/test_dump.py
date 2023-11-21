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

    def test_ExtendableList_nocontext(self):
        data = np.random.random([100])

        with h5py.File("foo.h5", "w") as file:
            g5.ExtendableList(file, "foo", data.dtype).append(data[0]).flush()
            self.assertTrue(np.allclose(data[0], file["foo"][...]))

    def test_ExtendableList_append(self):
        data = np.random.random([100])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype, buffer=9) as dset:
                for d in data:
                    dset.append(d)
            self.assertTrue(np.allclose(data, file["foo"][...]))

    def test_ExtendableList_append_list(self):
        data = np.random.random([10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype, buffer=9) as dset:
                for d in data:
                    dset.append(d)
            self.assertTrue(np.allclose(data.ravel(), file["foo"][...]))

    def test_ExtendableList_add(self):
        data = np.random.random([10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype, buffer=9) as dset:
                for d in data:
                    dset += d
            self.assertTrue(np.allclose(data.ravel(), file["foo"][...]))

    def test_ExtendableList_setitem(self):
        data = np.random.random([100])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                with self.assertRaises(AssertionError):
                    dset[0, 0] = 100
                with self.assertRaises(AssertionError):
                    dset.setitem([0, 0], 100)
            self.assertEqual(file["foo"].size, 0)

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[0] = data[0]
            self.assertEqual(file["foo"].shape, (1,))
            self.assertTrue(np.allclose(data[0], file["foo"][0]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[2] = data[2]
            self.assertEqual(file["foo"].shape, (3,))
            self.assertTrue(np.allclose(data[2], file["foo"][2]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[0] = data[0]
                dset[1] = data[1]
                dset[2] = data[2]
            self.assertEqual(file["foo"].shape, (3,))
            self.assertTrue(np.allclose(data[:3], file["foo"][:3]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[30:] = data[30:]
            self.assertEqual(file["foo"].shape, (100,))
            self.assertTrue(np.allclose(data[30:], file["foo"][30:]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[10:20] = data[10:20]
            self.assertEqual(file["foo"].shape, (20,))
            self.assertTrue(np.allclose(data[10:20], file["foo"][10:20]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[10:20:2] = data[10:20:2]
            self.assertEqual(file["foo"].shape, (20,))
            self.assertTrue(np.allclose(data[10:20:2], file["foo"][10:20:2]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[10::2] = data[10:20:2]
            self.assertEqual(file["foo"].shape, (20,))
            self.assertTrue(np.allclose(data[10:20:2], file["foo"][10:20:2]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[:] = data[:10]
            self.assertEqual(file["foo"].shape, (10,))
            self.assertTrue(np.allclose(data[:10], file["foo"][...]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[...] = data[:10]
            self.assertEqual(file["foo"].shape, (10,))
            self.assertTrue(np.allclose(data[:10], file["foo"][...]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableList(file, "foo", data.dtype) as dset:
                dset[:] = data[:10]
                dset[10:20] = data[10:20]
                dset[20:30:2] = data[20:30:2]
                dset[21:30:2] = data[21:30:2]
                dset[30:] = data[30:]
            self.assertEqual(file["foo"].shape, data.shape)
            self.assertTrue(np.allclose(data, file["foo"][...]))

    def test_ExtendableList_existing(self):
        dataset = np.random.random([10, 100])

        with h5py.File("foo.h5", "w") as file:
            for data in dataset:
                with g5.ExtendableList(file, "foo", data.dtype, buffer=9) as dset:
                    for d in data:
                        dset.append(d)
            self.assertTrue(np.allclose(dataset.ravel(), file["foo"][...]))

    def test_ExtendableSlice_append(self):
        data = np.random.random([6, 10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", data.shape[1:], data.dtype) as dset:
                for d in data:
                    dset.append(d)
            self.assertTrue(np.allclose(data, file["foo"][...]))

    def test_ExtendableSlice_setitem(self):
        data = np.random.random([6, 10, 10])

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", data.shape[1:], data.dtype) as dset:
                for i in range(data.shape[0]):
                    dset[i] = data[i]
            self.assertTrue(np.allclose(data, file["foo"][...]))

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", data.shape[1:], data.dtype) as dset:
                pass
            with g5.ExtendableSlice(file, "foo") as dset:
                for i in range(data.shape[0]):
                    dset[i] = data[i]
            self.assertTrue(np.allclose(data, file["foo"][...]))

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

    def test_ExtendableSlice_maxshape(self):
        data = np.random.random([6, 10, 10])
        add = np.random.random([6, 10, 3])
        total = np.concatenate([data, add], axis=2)
        shape = data.shape[1:]
        maxshape = [None, None]

        with h5py.File("foo.h5", "w") as file:
            with g5.ExtendableSlice(file, "foo", shape, data.dtype, maxshape=maxshape) as dset:
                for d in data:
                    dset.append(d)
            file["foo"].resize(total.shape)
            file["foo"][..., data.shape[-1] :] = add
            self.assertTrue(np.allclose(total, file["foo"][...]))


if __name__ == "__main__":
    unittest.main()
