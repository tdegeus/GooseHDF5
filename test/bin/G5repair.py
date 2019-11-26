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

run("G5repair a.hdf5 b.hdf5")

expected_output = sorted(['/foo', '/bar'])

output = sorted(run("G5list b.hdf5"))

os.remove('a.hdf5')
os.remove('b.hdf5')

if output != expected_output:
  print('output = ')
  print(output)
  print('expected output = ')
  print(expected_output)
  raise IOError('Test failed')

