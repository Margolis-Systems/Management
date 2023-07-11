from wia_scan import *

device = prompt_choose_device_and_connect()
for i in range(1000000):
    press_any_key_to_continue()
    pillow_image = scan_side(device=device)
    filename = f'{i}.jpeg'
    pillow_image.save(filename, subsampling=0, optimize=True, progressive=True, quality=80)

