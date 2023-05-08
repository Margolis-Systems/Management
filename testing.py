# import configs
# # Mesh
# mongo = configs.mongo
# rebar_cat = mongo.read_collection_one('data_lists', {'name': 'rebar_catalog'})
# new_data = {}
# for item in rebar_cat['data']:
#     # Catalog item
#     obj = rebar_cat['data'][item]
#     new_obj = {}
#     # Parameter in item
#     for new_item in obj:
#         if new_item not in ['diam', 'pitch']:
#             new_obj[new_item] = obj[new_item]
#         elif new_item == 'diam':
#             new_obj[new_item+'_x'] = obj[new_item]
#             new_obj[new_item+'_y'] = obj[new_item]
#         elif new_item == 'pitch':
#             new_obj['x_'+new_item] = obj[new_item].split('X')[0]
#             new_obj['y_'+new_item] = obj[new_item].split('X')[0]
#             print(obj[new_item])
#             if obj[new_item] == '10X10':
#                 new_obj['x_bars'] = 60
#                 new_obj['y_bars'] = 25
#             elif obj[new_item] == '20X20':
#                 new_obj['x_bars'] = 40
#                 new_obj['y_bars'] = 17
#             else:
#                 new_obj['x_bars'] = 30
#                 new_obj['y_bars'] = 13
#     new_data[item] = new_obj
# print(new_data)
import configs
import pages
mongo = configs.mongo


def create_shape_plot(shape, data):
    import os
    from PIL import Image, ImageDraw, ImageFont
    font_size = 20
    positions = mongo.read_collection_one("data_lists", {"name": "shapes"})['data'][shape]['positions']
    static_dir = os.path.dirname(__file__) + '\\static\\'
    img_dir = static_dir + 'images\\shapes\\' + str(shape) + '.png'
    if os.path.exists(img_dir):
        img = Image.open(img_dir)
    else:
        img = Image.open(static_dir + 'images\\shapes\\0.png')
    draw = ImageDraw.Draw(img)
    for index in range(len(data)):
        # positions[index][0] -= (len(str(data[index])) - 1) * 3
        text_box_pos = positions[index][0], positions[index][1] - 2
        bbox = draw.textbbox(text_box_pos, str(data[index]), font=ImageFont.truetype("segoeuib.ttf", font_size + 2))
        draw.rectangle(bbox, fill="white")
        draw.text(positions[index], str(data[index]), font=ImageFont.truetype("segoeui.ttf", font_size), fill="black")
    file_out = "C:\\netcode\\Picture\\" + pages.ts(mode="file_name") + ".bmp"
    img.save(file_out)
    return file_out


create_shape_plot("1", [100])
