import os
import shutil
import unittest

import h5py

import GooseHDF5 as g5


class Test_itereator(unittest.TestCase):
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

        # shutil.rmtree(dirname)


if __name__ == "__main__":

    unittest.main()
