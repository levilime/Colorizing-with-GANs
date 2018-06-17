import glob

exists = glob.glob('*.png')
for i in range(0, 10000):
    a = 'places365_' + str(i).zfill(7)  + '.png'
    if a not in exists:
        print(a)
