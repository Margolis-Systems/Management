import os

directory = 'H:\\NetCode\\Picture\\'
for filename in os.listdir(directory):
    f = os.path.join(directory, filename)
    if os.path.isfile(f):
        if 'png' in f and f.replace(directory, '') not in ['1.png', 'kora.png']:
            os.remove(f)
