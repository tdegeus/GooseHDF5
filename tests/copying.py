import os
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


class Test_itereator(unittest.TestCase):
    def test_copy_plain(self):

        dirname = "mytest"
        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:

            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

        shutil.rmtree(dirname)

    def test_copy_nonrecursive(self):

        dirname = "mytest"
        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        datasets = ["/a", "/b/foo", "/b/bar", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:

            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, ["/a", "/b", "/c/d/foo"], recursive=False)

                for path in ["/a", "/c/d/foo"]:
                    self.assertTrue(g5.equal(source, dest, path))

                self.assertTrue(g5.exists(dest, "/b"))
                self.assertFalse(g5.exists(dest, "/b/foo"))
                self.assertFalse(g5.exists(dest, "/b/bar"))

        shutil.rmtree(dirname)

    def test_copy_recursive(self):

        dirname = "mytest"
        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        datasets = ["/a", "/b/foo", "/b/bar", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:

            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, ["/a", "/b", "/c/d/foo"])

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

        shutil.rmtree(dirname)

    def test_copy_attrs(self):

        dirname = "mytest"
        sourcepath = os.path.join(dirname, "foo_2.h5")
        destpath = os.path.join(dirname, "bar_2.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:

            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                meta = source.create_group("/meta")
                meta.attrs["version"] = np.random.rand(10)

                datasets += ["/meta"]
                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

        shutil.rmtree(dirname)

    def test_copy_groupattrs(self):

        dirname = "mytest"
        sourcepath = os.path.join(dirname, "foo_3.h5")
        destpath = os.path.join(dirname, "bar_3.h5")

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:

            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                source["/b"].attrs["version"] = np.random.rand(10)

                datasets += ["/b"]
                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

        shutil.rmtree(dirname)


if __name__ == "__main__":

    unittest.main()
