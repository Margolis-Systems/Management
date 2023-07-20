from wia_scan import *
import requests
import os
import sys

temp_folder = 'C:\Web_Scanner\\'
uid = '{6BDD1FC6-810F-11D0-BEC7-08002BE2092F}\\0000'
device = connect_to_device_by_uid(uid)
# Use prompt to see what is the UID
# device = prompt_choose_device_and_connect()
files = []
for i in range(100):
    try:
        # pillow_image = scan_side(device=device)
        pillow_image = scan_single_side_main()
        files.append(pillow_image)
    except:
        break
out_file_name = temp_folder + 'adi.pdf'
if files:
    files[0].save(out_file_name, save_all=True, append_images=files[1:])
r = requests.post('http://10.0.0.25:10770/order_file_upload', files={'file': (os.path.basename(out_file_name), open(out_file_name, 'rb'))})
