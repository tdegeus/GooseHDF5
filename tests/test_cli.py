import os
import shutil
import subprocess
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


dirname = os.path.join(os.path.abspath(os.path.dirname(__file__)), "mytest")


def run(cmd):
    ret = subprocess.run(cmd, capture_output=True, text=True)
    return list(filter(None, [i.rstrip().replace("\r", "") for i in ret.stdout.split("\n")]))


class MyTests(unittest.TestCase):
    """ """

    @classmethod
    def setUpClass(self):
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(dirname)

    def test_G5list(self):
        """
        Simple tests on G5list
        """

        filepath = os.path.join(dirname, "a.h5")

        with h5py.File(filepath, "w") as file:
            file["/a"] = np.random.random(25)
            file["/b/a"] = np.random.random(25)
            file["/b/b/a"] = np.random.random(25)

        output = sorted(run(["G5list", filepath]))
        expected = sorted(["/a", "/b/a", "/b/b/a"])
        self.assertEqual(output, expected)

    def test_G5list_depth(self):
        """
        Simple tests on G5list
        """

        filepath = os.path.join(dirname, "a.h5")

        with h5py.File(filepath, "w") as file:
            file["/a"] = np.random.random(25)
            file["/b/a"] = np.random.random(25)
            file["/b/b/a"] = np.random.random(25)
            file["/b/c/d/a"] = np.random.random(25)

            g = file.create_group("/c/a")
            g.attrs["foo"] = True

            g = file.create_group("/d/e/a")
            g.attrs["foo"] = True

        output = sorted(run(["G5list", "-d", "1", filepath]))
        expected = sorted(["/a", "/b/...", "/c/...", "/d/..."])
        self.assertEqual(output, expected)

        output = sorted(run(["G5list", "-d", "2", filepath]))
        expected = sorted(["/a", "/b/a", "/b/b/...", "/b/c/...", "/c/a", "/d/e/..."])
        self.assertEqual(output, expected)

        output = sorted(run(["G5list", "-d", "3", filepath]))
        expected = sorted(["/a", "/b/a", "/b/b/a", "/b/c/d/...", "/c/a", "/d/e/a"])
        self.assertEqual(output, expected)

        for i in range(4, 7):
            output = sorted(run(["G5list", "-d", str(i), filepath]))
            expected = sorted(["/a", "/b/a", "/b/b/a", "/b/c/d/a", "/c/a", "/d/e/a"])
            self.assertEqual(output, expected)

    def test_G5modify_depth(self):
        """
        Simple tests on G5modify
        """

        filepath = os.path.join(dirname, "a.h5")

        a = np.random.random([3, 2])
        b = np.random.random([3, 2])

        with h5py.File(filepath, "w") as file:
            file["/a"] = np.zeros_like(a)

        g5.G5modify([filepath, "a"] + [str(i) for i in a.ravel().tolist()])

        args = [filepath, "b"]
        args += [str(i) for i in b.ravel().tolist()]
        args += ["--shape=" + ",".join([str(i) for i in b.shape])]
        g5.G5modify(args)

        with h5py.File(filepath) as file:
            self.assertTrue(np.allclose(file["a"][...], a))
            self.assertTrue(np.allclose(file["b"][...], b))


if __name__ == "__main__":
    unittest.main()
