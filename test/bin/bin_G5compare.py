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
  with h5py.File('b.hdf5', 'w') as other:

    # NumPy array

    a = np.random.random(25)

    source['/a/equal'] = a
    source['/a/not_equal'] = a

    other['/a/equal'] = a
    other['/a/not_equal'] = np.random.random(25)

    # single number

    b = float(np.random.random(1))

    source['/b/equal'] = b
    source['/b/not_equal'] = b

    other['/b/equal'] = b
    other['/b/not_equal'] = float(np.random.random(1))

    # string

    c = 'foobar'

    source['/c/equal'] = c
    source['/c/not_equal'] = c

    other['/c/equal'] = c
    other['/c/not_equal'] = 'foobar2'

    # alias

    d = np.random.random(25)

    source['/d/equal'] = d
    other['/e/equal'] = d

# run test
# --------

output = run("../../bin/G5compare a.hdf5 b.hdf5 -r '/d/equal:/e/equal'")

os.remove('a.hdf5')
os.remove('b.hdf5')

if output != ['!= /a/not_equal', '!= /b/not_equal', '!= /c/not_equal']:
  raise IOError('Test failed')


