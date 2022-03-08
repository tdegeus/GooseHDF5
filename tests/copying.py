import os
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


dirname = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mytest")


class Test_itereator(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(self):

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    @classmethod
    def tearDownClass(self):

        shutil.rmtree(dirname)

    def test_copy_plain(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:
            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_softlinks(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
        datasets = ["/a", "/b/foo", "/c/d/foo"]
        links = ["/mylink/a", "/mylink/b/foo", "/mylink/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:
            with h5py.File(destpath, "w") as dest:

                for link, d in zip(links, datasets):
                    source[d] = np.random.rand(10)
                    source[link] = h5py.SoftLink(d)

                g5.copy(source, dest, datasets + links, expand_soft=False)

                for path in datasets + links:
                    self.assertTrue(g5.equal(source, dest, path))
                for path in datasets:
                    self.assertTrue(not isinstance(dest.get(path, getlink=True), h5py.SoftLink))
                for path in links:
                    self.assertTrue(isinstance(dest.get(path, getlink=True), h5py.SoftLink))

    def test_copy_expand_softlinks(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
        datasets = ["/a", "/b/foo", "/c/d/foo"]
        links = ["/mylink/a", "/mylink/b/foo", "/mylink/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:
            with h5py.File(destpath, "w") as dest:

                for link, d in zip(links, datasets):
                    source[d] = np.random.rand(10)
                    source[link] = h5py.SoftLink(d)

                g5.copy(source, dest, datasets + links)

                for path in datasets + links:
                    self.assertTrue(g5.equal(source, dest, path))
                for path in datasets + links:
                    self.assertTrue(not isinstance(dest.get(path, getlink=True), h5py.SoftLink))

    def test_copy_skip(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:
            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, datasets + ["/nonexisting"], skip=True)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_nonrecursive(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
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

    def test_copy_recursive(self):

        sourcepath = os.path.join(dirname, "foo_1.h5")
        destpath = os.path.join(dirname, "bar_1.h5")
        datasets = ["/a", "/b/foo", "/b/bar", "/c/d/foo"]

        with h5py.File(sourcepath, "w") as source:
            with h5py.File(destpath, "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, ["/a", "/b", "/c/d/foo"])

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_attrs(self):

        sourcepath = os.path.join(dirname, "foo_2.h5")
        destpath = os.path.join(dirname, "bar_2.h5")
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

    def test_copy_groupattrs(self):

        sourcepath = os.path.join(dirname, "foo_3.h5")
        destpath = os.path.join(dirname, "bar_3.h5")
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


if __name__ == "__main__":

    unittest.main()
