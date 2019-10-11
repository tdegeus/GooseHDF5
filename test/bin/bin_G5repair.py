import subprocess
import os
import h5py
import numpy as np

# support function
# ----------------

def run(cmd):
  return list(filter(None, subprocess.check_output(cmd,shell=True).decode('utf-8').split('\n')))

# create file
# -----------

with h5py.File('a.hdf5', 'w') as source:
  source['/foo'] = np.random.random(25)
  source['/bar'] = np.random.random(25)

# run test
# --------

run("../../bin/G5repair a.hdf5 b.hdf5")

output = run("../../bin/G5list b.hdf5")

os.remove('a.hdf5')
os.remove('b.hdf5')

if sorted(output) != sorted(['/foo', '/bar']):
  raise IOError('Test failed')


