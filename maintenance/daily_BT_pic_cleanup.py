import os

directory = ['H:\\NetCode\\Picture\\', 'C:\\Server\\static\\img', 'H:\\NetCode\\temp']
for dirr in directory:
    for filename in os.listdir(dirr):
        f = os.path.join(dirr, filename)
        if os.path.isfile(f):
            if 'png' in f and f.replace(dirr, '') not in ['1.png', 'kora.png']:
                os.remove(f)
            elif 'tmp' in f:
                os.remove(f)
