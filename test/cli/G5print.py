import subprocess
import os
import h5py
import numpy as np

# support function
# ----------------

def run(cmd):
  out = list(filter(None, subprocess.check_output(cmd,shell=True).decode('utf-8').split('\n')))
  return out[0]

# create file
# -----------

a = np.random.random(5)

with h5py.File('a.hdf5', 'w') as source:
  source['/a'] = a

# run test
# --------

output = run('G5print a.hdf5 "/a"')

expected_output = str(a)

os.remove('a.hdf5')

if output != expected_output:
  print('output = ')
  print(output)
  print('expected output = ')
  print(expected_output)
  raise IOError('Test failed')
