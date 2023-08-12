import os
import json
from PIL import Image, ImageDraw, ImageFont
from configs import mongo

# CONFIG
config = {'size': (200, 60), 'text_en': True, 'update_mongo': False, 'update_file': True}


def shape_plot(positions, file_name, text=[], enable_text_plot=True):
    if not text:
        text = list(range(1, len(positions)))
    shape = file_name.split('\\')[-1].replace('.png', '')
    size = config['size']
    im = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(im)
    draw.line(pos, fill="black", width=4)
    if enable_text_plot:
        text_pos = []
        for i in range(len(pos) - 1):
            position = ((positions[i][0] + positions[i + 1][0] - len(str(text[i])) * 6) / 2,
                        (positions[i][1] + positions[i + 1][1]) / 2 - 6)
            font_size = 16
            bbox = draw.textbbox((position[0] - 1, position[1]-2), str(text[i]), font=ImageFont.truetype("c:\\server\\fonts\\upheavtt.ttf", font_size+4))
            draw.rectangle(bbox, fill="white")
            draw.text(position, str(text[i]), fill="black", font=ImageFont.truetype("c:\\server\\fonts\\upheavtt.ttf", font_size))
            text_pos.append(position)
    im.save(file_name)
    im.show(file_name)
    if config['update_file']:
        with open('C:\\Server\\lists\\shapes.json', 'r', encoding='utf-8') as shapes_json:
            shapes = json.load(shapes_json)
        edges = len(positions) - 1
        ang = get_ang(positions)
        shapes[shape] = {'description': '---', 'edges': edges, 'positions': text_pos,
                         'draw_positions': positions, 'ang': ang}
        print(list(shapes.keys()))
        with open('C:\\Server\\lists\\shapes.json', 'w', encoding='utf-8') as shapes_json:
            json.dump(shapes, shapes_json)


def get_ang(shape_data):
    ang = []
    for ind in list(range(1, len(shape_data)-1)):
        pos1, pos2, pos3 = shape_data[ind - 1], shape_data[ind], shape_data[ind+1]
        print(pos1, pos2, pos3)
        if (pos1[0] - pos2[0] == 0 or pos1[1] - pos2[1] == 0) and (pos3[0] - pos2[0] == 0 or pos3[1] - pos2[1] == 0):
            ang.append(90)
        else:
            ang.append(45)
    return ang


def print_shapes_name():
    with open('C:\\Server\\lists\\shapes.json', 'r', encoding='utf-8') as shapes_json:
        shapes = json.load(shapes_json)
    print(list(shapes.keys()))


def print_keys():
    with open('C:\\Server\\lists\\shapes.json', 'r', encoding='utf-8') as shapes_json:
        shapes = json.load(shapes_json)
    keys = list(shapes.keys())
    keys = sorted(keys, key=int)
    print(keys)


if __name__ == '__main__':
    # print_shapes_name()
    # SIZE 200 X 60
    # INPUT
    #[  185, 20  ],  [ 60,  20 ], [60, 55 ],[ 140, 55 ], [ 140, 5 ],[15, 5]]
    # print_keys()
    pos = [(15,50),(185,50),(185,5),(90,5),(60,30),(140,30)]
    name = '20'
    shape_plot(pos, os.getcwd() + '\\shapes\\' + name + '.png')
