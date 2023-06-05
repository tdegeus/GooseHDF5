import contextlib
import io
import os
import pathlib
import shutil
import tempfile
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


class MyTests(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(self):
        self.origin = pathlib.Path().absolute()
        self.tempdir = tempfile.mkdtemp()
        os.chdir(self.tempdir)

    @classmethod
    def tearDownClass(self):
        os.chdir(self.origin)
        shutil.rmtree(self.tempdir)

    def test_G5list(self):
        """
        Simple tests on G5list
        """

        with h5py.File("a.h5", "w") as file:
            file["/a"] = np.random.random(25)
            file["/b/a"] = np.random.random(25)
            file["/b/b/a"] = np.random.random(25)

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5list(["a.h5"])

        output = sorted(sio.getvalue().strip().splitlines())
        expected = sorted(["/a", "/b/a", "/b/b/a"])
        self.assertEqual(output, expected)

    def test_G5list_depth(self):
        """
        Simple tests on G5list
        """

        with h5py.File("a.h5", "w") as file:
            file["/a"] = np.random.random(25)
            file["/b/a"] = np.random.random(25)
            file["/b/b/a"] = np.random.random(25)
            file["/b/c/d/a"] = np.random.random(25)

            g = file.create_group("/c/a")
            g.attrs["foo"] = True

            g = file.create_group("/d/e/a")
            g.attrs["foo"] = True

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5list(["-d", "1", "a.h5"])

        output = sorted(sio.getvalue().strip().splitlines())
        expected = sorted(["/a", "/b/...", "/c/...", "/d/..."])
        self.assertEqual(output, expected)

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5list(["-d", "2", "a.h5"])

        output = sorted(sio.getvalue().strip().splitlines())
        expected = sorted(["/a", "/b/a", "/b/b/...", "/b/c/...", "/c/a", "/d/e/..."])
        self.assertEqual(output, expected)

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5list(["-d", "3", "a.h5"])

        output = sorted(sio.getvalue().strip().splitlines())
        expected = sorted(["/a", "/b/a", "/b/b/a", "/b/c/d/...", "/c/a", "/d/e/a"])
        self.assertEqual(output, expected)

        for i in range(4, 7):
            with contextlib.redirect_stdout(io.StringIO()) as sio:
                g5.G5list(["-d", str(i), "a.h5"])
            output = sorted(sio.getvalue().strip().splitlines())
            expected = sorted(["/a", "/b/a", "/b/b/a", "/b/c/d/a", "/c/a", "/d/e/a"])
            self.assertEqual(output, expected)

    def test_G5modify_depth(self):
        """
        Simple tests on G5modify
        """

        a = np.random.random([3, 2])
        b = np.random.random([3, 2])

        with h5py.File("a.h5", "w") as file:
            file["/a"] = np.zeros_like(a)

        g5.G5modify(["a.h5", "a"] + [str(i) for i in a.ravel().tolist()])

        args = ["a.h5", "b"]
        args += [str(i) for i in b.ravel().tolist()]
        args += ["--shape=" + ",".join([str(i) for i in b.shape])]
        g5.G5modify(args)

        with h5py.File("a.h5") as file:
            self.assertTrue(np.allclose(file["a"][...], a))
            self.assertTrue(np.allclose(file["b"][...], b))


if __name__ == "__main__":
    unittest.main()
