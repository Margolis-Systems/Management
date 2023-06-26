import os
from PIL import Image, ImageDraw, ImageFont
from configs import mongo

# CONFIG
config = {'size': (200, 60), 'text_en': True, 'update_mongo': True}


def shape_plot(positions, file_name, text=[]):
    if not text:
        text = list(range(1, len(positions)))
    shape = file_name.split('\\')[-1].replace('.png', '')
    size = config['size']
    im = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(im)
    draw.line(pos, fill="black", width=4)
    if config['text_en']:
        text_pos = []
        for i in range(len(pos) - 1):
            position = ((positions[i][0] + positions[i + 1][0] - len(str(text[i])) * 2) / 2,
                        (positions[i][1] + positions[i + 1][1] - len(str(text[i]))) / 2 - 3)
            print(position)
            bbox = draw.textbbox((position[0] - 1, position[1]), str(text[i]))
            draw.rectangle(bbox, fill="white")
            draw.text(position, str(text[i]), fill="black")
            text_pos.append(position)
        if config['update_mongo']:
            mongo.update_one('data_lists', {'name': 'shapes_'}, {'data.' + shape + '.positions': text_pos}, '$set')
    im.save(file_name)
    im.show(file_name)


if __name__ == '__main__':
    # SIZE 200 X 60
    todo = [57, 925, 966]
    print(sorted(todo))
    x_r = 185
    x_l = 15
    y_top = 5
    y_bot = 55
    # INPUT
    pos = []
    name = '966'
    shape_plot(pos, os.getcwd() + '\\shapes\\' + name + '.png')
