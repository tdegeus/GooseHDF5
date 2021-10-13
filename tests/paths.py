import os
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


class Test_itereator(unittest.TestCase):
    """
    Tests.
    """

    def test_getdatasets(self):

        dirname = "mytest"
        filename = "foo.h5"
        filepath = os.path.join(dirname, filename)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        Datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(filepath, "w") as file:

            for d in Datasets:
                file[d] = [0, 1, 2]

            paths = list(g5.getdatasets(file))
            paths_c = list(g5.getdatasets(file, root="/c"))

        self.assertEqual(sorted(Datasets), sorted(paths))
        self.assertEqual(sorted([Datasets[-1]]), sorted(paths_c))

        shutil.rmtree(dirname)

    def test_getgroups(self):

        dirname = "mytest"
        filename = "foo.h5"
        filepath = os.path.join(dirname, filename)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        Datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(filepath, "w") as file:

            for d in Datasets:
                file[d] = [0, 1, 2]

            self.assertEqual(g5.getgroups(file), ["/b", "/c", "/c/d"])
            self.assertEqual(g5.getgroups(file, root="/c"), ["/c/d"])

        shutil.rmtree(dirname)

    def test_getgroups_attrs(self):

        dirname = "mytest"
        filename = "foo.h5"
        filepath = os.path.join(dirname, filename)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        Datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(filepath, "w") as file:

            for d in Datasets:
                file[d] = [0, 1, 2]

            meta = file.create_group("meta")
            meta.attrs["version"] = 0

            self.assertEqual(g5.getgroups(file, has_attrs=True), ["/meta"])

        shutil.rmtree(dirname)

    def test_compare(self):

        dirname = "mytest"
        filename_a = "foo.h5"
        filename_b = "bar.h5"
        filepath_a = os.path.join(dirname, filename_a)
        filepath_b = os.path.join(dirname, filename_b)

        if not os.path.isdir(dirname):
            os.makedirs(dirname)

        with h5py.File(filepath_a, "w") as source:
            with h5py.File(filepath_b, "w") as other:

                # NumPy array

                a = np.random.random(25)

                source["/a/equal"] = a
                source["/a/not_equal"] = a

                other["/a/equal"] = a
                other["/a/not_equal"] = np.random.random(25)

                # single number

                b = float(np.random.random(1))

                source["/b/equal"] = b
                source["/b/not_equal"] = b

                other["/b/equal"] = b
                other["/b/not_equal"] = float(np.random.random(1))

                # string

                c = "foobar"

                source["/c/equal"] = c
                source["/c/not_equal"] = c

                other["/c/equal"] = c
                other["/c/not_equal"] = "foobar2"

                # attribute

                d = np.random.random(25)

                source["/d/equal"] = d
                source["/d/equal"].attrs["key"] = d
                source["/d/not_equal"] = d
                source["/d/not_equal"].attrs["key"] = d

                other["/d/equal"] = d
                other["/d/equal"].attrs["key"] = d
                other["/d/not_equal"] = d
                other["/d/not_equal"].attrs["key"] = np.random.random(25)

                # dtyoe

                e = (100.0 * np.random.random(25)).astype(int)

                source["/e/equal"] = e
                source["/e/not_equal"] = e

                other["/e/equal"] = e
                other["/e/not_equal"] = e.astype(float)

                # dtyoe attribute

                f = (100.0 * np.random.random(25)).astype(int)

                source["/f/equal"] = f
                source["/f/equal"].attrs["key"] = f
                source["/f/not_equal"] = f
                source["/f/not_equal"].attrs["key"] = f

                other["/f/equal"] = f
                other["/f/equal"].attrs["key"] = f
                other["/f/not_equal"] = f
                other["/f/not_equal"].attrs["key"] = f.astype(float)

                # attribute (not present)

                meta = source.create_group("/meta")
                meta.attrs["version"] = 0

                # attribute (not equal)

                meta = source.create_group("/meta_not_equal")
                meta.attrs["version"] = 0

                meta = other.create_group("/meta_not_equal")
                meta.attrs["version"] = 1

                # attribute (equal)

                meta = source.create_group("/meta_equal")
                meta.attrs["version"] = 1

                meta = other.create_group("/meta_equal")
                meta.attrs["version"] = 1

                # check

                ret = g5.compare(source, other)

        expected_output = {
            "!=": [
                "/a/not_equal",
                "/b/not_equal",
                "/c/not_equal",
                "/d/not_equal",
                "/e/not_equal",
                "/f/not_equal",
                "/meta_not_equal",
            ],
            "->": ["/meta"],
            "==": [
                "/a/equal",
                "/b/equal",
                "/c/equal",
                "/d/equal",
                "/e/equal",
                "/f/equal",
                "/meta_equal",
            ],
        }

        for key in expected_output:
            expected_output[key] = sorted(expected_output[key])

        for key in ret:
            ret[key] = sorted(ret[key])

        self.assertEqual(expected_output, ret)

        shutil.rmtree(dirname)


if __name__ == "__main__":

    unittest.main()
