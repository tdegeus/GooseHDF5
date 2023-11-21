import contextlib
import io
import os
import pathlib
import re
import shutil
import tempfile
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


def _plain(text):
    return list(filter(None, [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]))


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

    def test_G5compare(self):
        with h5py.File("a.hdf5", "w") as source, h5py.File("b.hdf5", "w") as other:
            # NumPy array

            a = np.random.random(25)

            source["/a/equal"] = a
            source["/a/not_equal"] = a

            other["/a/equal"] = a
            other["/a/not_equal"] = np.random.random(25)

            # single number

            b = np.random.random(1)[0]

            source["/b/equal"] = b
            source["/b/not_equal"] = b

            other["/b/equal"] = b
            other["/b/not_equal"] = np.random.random(1)[0]

            # string

            c = "foobar"

            source["/c/equal"] = c
            source["/c/not_equal"] = c

            other["/c/equal"] = c
            other["/c/not_equal"] = "foobar2"

            # alias

            d = np.random.random(25)

            source["/d/equal"] = d
            other["/e/equal"] = d

            # attribute

            f = np.random.random(25)

            source["/f/equal"] = f
            source["/f/equal"].attrs["key"] = f
            source["/f/not_equal"] = f
            source["/f/not_equal"].attrs["key"] = f

            other["/f/equal"] = f
            other["/f/equal"].attrs["key"] = f
            other["/f/not_equal"] = f
            other["/f/not_equal"].attrs["key"] = np.random.random(25)

            # meta (not present)

            meta = source.create_group("/meta")
            meta.attrs["version"] = 0

            # meta (present)

            meta = source.create_group("/present")
            meta.attrs["version"] = 0

            meta = other.create_group("/present")
            meta.attrs["version"] = 1

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5compare(
                [
                    "-c",
                    "none",
                    "--table",
                    "PLAIN_COLUMNS",
                    "a.hdf5",
                    "b.hdf5",
                    "-r",
                    "/d/equal",
                    "/e/equal",
                ]
            )

        output = _plain(sio.getvalue())
        expected = [
            "/a/not_equal != /a/not_equal",
            "/b/not_equal != /b/not_equal",
            "/c/not_equal != /c/not_equal",
            "/f/not_equal != /f/not_equal",
            "/present != /present",
            "/meta ->",
        ]
        self.assertEqual(sorted(output[1:]), sorted(expected))

    def test_G5print(self):
        a = np.random.random(3)

        with h5py.File("a.hdf5", "w") as source:
            source["/a"] = a
            source["/a"].attrs["desc"] = "Example"

        with contextlib.redirect_stdout(io.StringIO()) as sio:
            g5.G5print(["a.hdf5", "/a", "-a"])

        output = sio.getvalue().splitlines()
        expected = ["desc : Example"] + [str(a)]

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
