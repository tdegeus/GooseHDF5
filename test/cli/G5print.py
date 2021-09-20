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


a = np.random.random(5)

with h5py.File("a.hdf5", "w") as source:
    source["/a"] = a
    source["/a"].attrs["desc"] = "Example"

expected_output = ["desc : Example"] + [str(a)]

output = run('G5print -a a.hdf5 "/a"')

os.remove("a.hdf5")

if output != expected_output:
    print("output = ")
    print(output)
    print("expected output = ")
    print(expected_output)
    raise OSError("Test failed")
