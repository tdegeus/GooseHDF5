import os
import pathlib
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


basedir = pathlib.Path(__file__).parent / "mytest"


class Test_itereator(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(self):
        """
        Create a temporary directory for the test files.
        """
        os.makedirs(basedir, exist_ok=True)

    @classmethod
    def tearDownClass(self):
        """
        Remove the temporary directory.
        """
        shutil.rmtree(basedir)

    def test_copy_plain(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_softlinks(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]
        links = ["/mylink/a", "/mylink/b/foo", "/mylink/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for link, d in zip(links, datasets):
                    source[d] = np.random.rand(10)
                    source[link] = h5py.SoftLink(d)

                g5.copy(source, dest, datasets + links, expand_soft=False)

                for path in datasets + links:
                    self.assertTrue(g5.equal(source, dest, path))
                for path in datasets:
                    self.assertNotIsInstance(dest.get(path, getlink=True), h5py.SoftLink)
                for path in links:
                    self.assertIsInstance(dest.get(path, getlink=True), h5py.SoftLink)

    def test_copy_expand_softlinks(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]
        links = ["/mylink/a", "/mylink/b/foo", "/mylink/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for link, d in zip(links, datasets):
                    source[d] = np.random.rand(10)
                    source[link] = h5py.SoftLink(d)

                g5.copy(source, dest, datasets + links)

                for path in datasets + links:
                    self.assertTrue(g5.equal(source, dest, path))
                for path in datasets + links:
                    self.assertNotIsInstance(dest.get(path, getlink=True), h5py.SoftLink)

    def test_copy_skip(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, datasets + ["/nonexisting"], skip=True)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_nonrecursive(self):

        datasets = ["/a", "/b/foo", "/b/bar", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, ["/a", "/b", "/c/d/foo"], recursive=False)

                for path in ["/a", "/c/d/foo"]:
                    self.assertTrue(g5.equal(source, dest, path))

                self.assertTrue(g5.exists(dest, "/b"))
                self.assertFalse(g5.exists(dest, "/b/foo"))
                self.assertFalse(g5.exists(dest, "/b/bar"))

    def test_copy_recursive(self):

        datasets = ["/a", "/b/foo", "/b/bar", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                g5.copy(source, dest, ["/a", "/b", "/c/d/foo"])

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_attrs(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                meta = source.create_group("/meta")
                meta.attrs["version"] = np.random.rand(10)

                datasets += ["/meta"]
                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_groupattrs(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[d] = np.random.rand(10)

                source["/b"].attrs["version"] = np.random.rand(10)

                datasets += ["/b"]
                g5.copy(source, dest, datasets)

                for path in datasets:
                    self.assertTrue(g5.equal(source, dest, path))

    def test_copy_root(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]
        source_pre = "/my/source"
        dest_pre = "/your/dest"

        with h5py.File(basedir / "foo_1.h5", "w") as source:
            with h5py.File(basedir / "bar_1.h5", "w") as dest:

                for d in datasets:
                    source[g5.join(source_pre, d)] = np.random.rand(10)

                g5.copy(source, dest, datasets, source_root=source_pre, root=dest_pre)

                for path in datasets:
                    s = g5.join(source_pre, path)
                    d = g5.join(dest_pre, path)
                    self.assertTrue(g5.equal(source, dest, s, d))


if __name__ == "__main__":

    unittest.main()
