import h5py
import numpy as np

import GooseHDF5 as g5

with h5py.File("foo.h5", "w") as data:

    data["/a"] = np.arange(5)
    data["/b/c"] = np.arange(5)
    data["/d/e/f"] = np.arange(5)

with h5py.File("foo.h5", "r") as data:

    paths = list(g5.getdatasets(data))
    paths.remove("/d/e/f")

    with h5py.File("bar.h5", "w") as ret:
        g5.copy(data, ret, paths)
        ret["/d/e/f"] = data["/d/e/f"][...] * 2
