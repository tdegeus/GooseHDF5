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
    source["/foo"] = np.random.random(25)
    source["/bar"] = np.random.random(25)


run("G5repair a.hdf5 b.hdf5")

expected_output = sorted(["/foo", "/bar"])

output = sorted(run("G5list b.hdf5"))

os.remove("a.hdf5")
os.remove("b.hdf5")

if output != expected_output:
    print("output = ")
    print(output)
    print("expected output = ")
    print(expected_output)
    raise OSError("Test failed")
