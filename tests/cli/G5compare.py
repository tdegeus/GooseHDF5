import os
import subprocess

import h5py
import numpy as np
import prettytable


def run(cmd):
    out = list(filter(None, subprocess.check_output(cmd, shell=True).decode("utf-8").split("\n")))
    return [i.rstrip().replace("\r", "") for i in out]


with h5py.File("a.hdf5", "w") as source:
    with h5py.File("b.hdf5", "w") as other:

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

        # alias

        d = np.random.random(25)

        source["/d/equal"] = d
        other["/e/equal"] = d

        # attribute

        f = np.random.random(25)

        source["/f/equal"] = f
        source["/f/equal"].attrs["key"] = f
        source["/f/not_equal"] = f
        source["/f/not_equal"].attrs["key"] = f

        other["/f/equal"] = f
        other["/f/equal"].attrs["key"] = f
        other["/f/not_equal"] = f
        other["/f/not_equal"].attrs["key"] = np.random.random(25)

        # meta (not present)

        meta = source.create_group("/meta")
        meta.attrs["version"] = 0

        # meta (present)

        meta = source.create_group("/present")
        meta.attrs["version"] = 0

        meta = other.create_group("/present")
        meta.attrs["version"] = 1


output = sorted(run("G5compare -c none --table PLAIN_COLUMNS a.hdf5 b.hdf5 -r /d/equal /e/equal"))
output = [i.strip() for i in output]

out = prettytable.PrettyTable()
out.set_style(prettytable.PLAIN_COLUMNS)
out.field_names = ["a.hdf5", "", "b.hdf5"]
out.align = "l"
out.add_row(["/a/not_equal", "!=", "/a/not_equal"])
out.add_row(["/b/not_equal", "!=", "/b/not_equal"])
out.add_row(["/c/not_equal", "!=", "/c/not_equal"])
out.add_row(["/f/not_equal", "!=", "/f/not_equal"])
out.add_row(["/present", "!=", "/present"])
out.add_row(["/meta", "->", ""])
expected_output = [i.strip() for i in sorted(out.get_string().split("\n"))]

os.remove("a.hdf5")
os.remove("b.hdf5")

for i in range(len(output)):
    if output[i] != expected_output[i]:
        print("|" + output[i] + "|")
        print("|" + expected_output[i] + "|")
        raise OSError("Test failed")
