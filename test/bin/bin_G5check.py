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
  source['/a'] = np.random.random(25)

# run test
# --------

output = run("../../bin/G5check a.hdf5")

os.remove('a.hdf5')

if output != []:
  raise IOError('Test failed')


