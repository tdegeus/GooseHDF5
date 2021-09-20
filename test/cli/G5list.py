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
    return [i.rstrip().replace("\r", "") for i in out]


with h5py.File("a.hdf5", "w") as source:
    source["/a"] = np.random.random(25)
    source["/b/a"] = np.random.random(25)
    source["/b/b/a"] = np.random.random(25)


output = sorted(run("G5list a.hdf5"))

expected_output = sorted(["/a", "/b/a", "/b/b/a"])

os.remove("a.hdf5")

if output != expected_output:
    print("output = ")
    print(output)
    print("expected output = ")
    print(expected_output)
    raise OSError("Test failed")
