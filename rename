import glob
import os

names = sorted(glob.glob('*.jpg'))
step = 1
for name in names:
    os.rename(name, 'Places365_val_' + str(step).zfill(8))
    step = step + 1
