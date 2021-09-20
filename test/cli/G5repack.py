import os
import subprocess

import h5py
import numpy as np


def run(cmd):
    out = list(
        filter(
            None, subprocess.check_output(cmd, shell=True).decode("utf-8").split("\n")
        )
    )
    return out


a = np.random.random(1000)
b = "foo"

with h5py.File("a.hdf5", "w") as source:
    source["/a"] = a
    source["/b"] = b

output = run("G5repack -c a.hdf5")

with h5py.File("a.hdf5", "r") as source:
    a_r = source["/a"][...]
    b_r = source["/b"].asstr()[...]

os.remove("a.hdf5")

if not np.allclose(a, a_r):
    raise OSError("Test failed")

if b != b_r:
    raise OSError("Test failed")
