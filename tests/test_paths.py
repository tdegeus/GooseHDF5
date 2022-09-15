import os
import pathlib
import shutil
import unittest

import h5py
import numpy as np

import GooseHDF5 as g5


basedir = pathlib.Path(__file__).parent / "mytest"


class Test_iterator(unittest.TestCase):
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

    def test_getdatasets(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo.h5", "w") as file:

            for d in datasets:
                file[d] = [0, 1, 2]

            paths = list(g5.getdatasets(file))
            paths_c = list(g5.getdatasets(file, root="/c"))

        self.assertEqual(sorted(datasets), sorted(paths))
        self.assertEqual(sorted([datasets[-1]]), sorted(paths_c))


    def test_getgroups(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo.h5", "w") as file:

            for d in datasets:
                file[d] = [0, 1, 2]

            self.assertEqual(g5.getgroups(file), ["/b", "/c", "/c/d"])
            self.assertEqual(g5.getgroups(file, root="/c"), ["/c/d"])

    def test_getgroups_attrs(self):

        datasets = ["/a", "/b/foo", "/c/d/foo"]

        with h5py.File(basedir / "foo.h5", "w") as file:

            for d in datasets:
                file[d] = [0, 1, 2]

            meta = file.create_group("meta")
            meta.attrs["version"] = 0

            self.assertEqual(g5.getgroups(file, has_attrs=True), ["/meta"])

    def test_compare(self):

        with h5py.File(basedir / "a.h5", "w") as source, h5py.File(basedir / "b.h5", "w") as other:

            # NumPy array

            a = np.random.random(25)

            source["/a/equal"] = a
            source["/a/ne_data"] = a

            other["/a/equal"] = a
            other["/a/ne_data"] = np.random.random(25)

            # single number

            b = float(np.random.random(1))

            source["/b/equal"] = b
            source["/b/ne_data"] = b

            other["/b/equal"] = b
            other["/b/ne_data"] = float(np.random.random(1))

            # string

            c = "foobar"

            source["/c/equal"] = c
            source["/c/ne_data"] = c

            other["/c/equal"] = c
            other["/c/ne_data"] = "foobar2"

            # attribute

            d = np.random.random(25)

            source["/d/equal"] = d
            source["/d/equal"].attrs["key"] = d
            source["/d/ne_attr"] = d
            source["/d/ne_attr"].attrs["key"] = d

            other["/d/equal"] = d
            other["/d/equal"].attrs["key"] = d
            other["/d/ne_attr"] = d
            other["/d/ne_attr"].attrs["key"] = np.random.random(25)

            # dtyoe

            e = (100.0 * np.random.random(25)).astype(int)

            source["/e/equal"] = e
            source["/e/ne_dtype"] = e

            other["/e/equal"] = e
            other["/e/ne_dtype"] = e.astype(float)

            # dtyoe attribute

            f = (100.0 * np.random.random(25)).astype(int)

            source["/f/equal"] = f
            source["/f/equal"].attrs["key"] = f
            source["/f/ne_dtype_attr"] = f
            source["/f/ne_dtype_attr"].attrs["key"] = f

            other["/f/equal"] = f
            other["/f/equal"].attrs["key"] = f
            other["/f/ne_dtype_attr"] = f
            other["/f/ne_dtype_attr"].attrs["key"] = f.astype(float)

            # attribute (not present)

            meta = source.create_group("/meta")
            meta.attrs["version"] = 0

            # attribute (not equal)

            meta = source.create_group("/meta_ne_attr")
            meta.attrs["version"] = 0

            meta = other.create_group("/meta_ne_attr")
            meta.attrs["version"] = 1

            # attribute (equal)

            meta = source.create_group("/meta_equal")
            meta.attrs["version"] = 1

            meta = other.create_group("/meta_equal")
            meta.attrs["version"] = 1

            # check

            check_all = g5.compare(source, other)
            check_datasets = g5.compare(source, other, attrs=False)
            check_all_shallow = g5.compare(source, other, shallow=True)

        expected_all = {
            "->": ["/meta"],
            "<-": [],
            "!=": [
                "/a/ne_data",
                "/b/ne_data",
                "/c/ne_data",
                "/d/ne_attr",
                "/e/ne_dtype",
                "/f/ne_dtype_attr",
                "/meta_ne_attr",
            ],
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

        expected_all_shallow = {
            "->": expected_all["->"],
            "<-": expected_all["<-"],
            "!=": [],
            "==": expected_all["=="] + expected_all["!="],
        }

        expected_datasets = {
            "->": [],
            "<-": [],
            "!=": [
                "/a/ne_data",
                "/b/ne_data",
                "/c/ne_data",
                "/e/ne_dtype",
            ],
            "==": [
                "/a/equal",
                "/b/equal",
                "/c/equal",
                "/d/equal",
                "/d/ne_attr",
                "/e/equal",
                "/f/equal",
                "/f/ne_dtype_attr",
            ],
        }

        for key in expected_all:
            expected_all[key] = sorted(expected_all[key])

        for key in expected_all_shallow:
            expected_all_shallow[key] = sorted(expected_all_shallow[key])

        for key in expected_datasets:
            expected_datasets[key] = sorted(expected_datasets[key])

        for key in check_all:
            check_all[key] = sorted(check_all[key])

        for key in check_all_shallow:
            check_all_shallow[key] = sorted(check_all_shallow[key])

        for key in check_datasets:
            check_datasets[key] = sorted(check_datasets[key])

        self.assertEqual(expected_all, check_all)
        self.assertEqual(expected_all_shallow, check_all_shallow)
        self.assertEqual(expected_datasets, check_datasets)

    def test_truncate_print_path(self):

        path = os.path.join("path", "to", "long", "foo", "bar")

        for n in [9, 10, 20, 30]:
            self.assertLessEqual(len(g5._truncate_print_path(path, n)), n)


if __name__ == "__main__":

    unittest.main()
