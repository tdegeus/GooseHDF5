import subprocess
import os
import h5py
import numpy as np

def run(cmd):
    out = list(filter(None, subprocess.check_output(cmd, shell=True).decode('utf-8').split('\n')))
    return out

a = np.random.random(1000)

with h5py.File('a.hdf5', 'w') as source:
    source['/a'] = a

output = run('G5repack -c a.hdf5')

with h5py.File('a.hdf5', 'r') as source:
    b = source['/a'][...]

os.remove('a.hdf5')

if not np.allclose(a, b):
    raise IOError('Test failed')

