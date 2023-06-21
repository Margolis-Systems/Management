import os

from PIL import Image, ImageDraw, ImageFont

# INPUT
pos = [(5, 25), (50, 25), (50, 50)]
data = ['100', '50']

# CONFIG
config = {'size': (100, 100), 'text_en': True}


def shape_plot(positions, file_name, text=[]):
    if not text:
        text = list(range(1, len(positions)))
        print(text)
    size = config['size']
    im = Image.new('RGB', size, 'white')
    draw = ImageDraw.Draw(im)
    draw.line(pos, fill="black", width=4)
    if config['text_en']:
        for i in range(len(pos)-1):
            position = ((positions[i][0] + positions[i+1][0] - len(str(text[i])) * 2) / 2,
                        (positions[i][1] + positions[i+1][1] - len(str(text[i]))) / 2 - 3)
            bbox = draw.textbbox((position[0]-1, position[1]), str(text[i]))
            draw.rectangle(bbox, fill="white")
            draw.text(position, str(text[i]), fill="black")
    im.save(file_name)


if __name__ == '__main__':
    shape_plot(pos, os.getcwd()+'\\shapes\\test.png')
