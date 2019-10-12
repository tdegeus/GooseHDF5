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
  source['/b/a'] = np.random.random(25)
  source['/b/b/a'] = np.random.random(25)

# run test
# --------

output = run("G5list a.hdf5")

os.remove('a.hdf5')

if output != ['/a', '/b/a', '/b/b/a']:
  raise IOError('Test failed')


