import h5py
import numpy as np

import GooseHDF5 as g5

with h5py.File("foo.h5", "w") as file:

    file["/a"] = np.arange(5)
    file["/b/c"] = np.arange(5)
    file["/d/e/f"] = np.arange(5)

with h5py.File("foo.h5", "r") as file:

    paths = list(g5.getdatasets(file))
    paths.remove("/d/e/f")

    with h5py.File("bar.h5", "w") as ret:
        g5.copy(file, ret, paths)
        ret["/d/e/f"] = file["/d/e/f"][...] * 2

        print(g5.compare(file, ret, paths))
