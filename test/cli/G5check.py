import subprocess
import os
import h5py
import numpy as np

# support function
# ----------------

def run(cmd):
  out = list(filter(None, subprocess.check_output(cmd,shell=True).decode('utf-8').split('\n')))
  return [i.rstrip() for i in out]

# create file
# -----------

with h5py.File('a.hdf5', 'w') as source:
  source['/a'] = np.random.random(25)

# run test
# --------

output = run("G5check a.hdf5")

expected_output = []

os.remove('a.hdf5')

if output != expected_output:
  print('output = ')
  print(output)
  print('expected output = ')
  print(expected_output)
  raise IOError('Test failed')





