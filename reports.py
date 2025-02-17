from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement

import main
import orders
import functions
import configs

import math
import os
import shutil
from collections import OrderedDict
from datetime import datetime
from mailmerge import MailMerge
import docx
from docx.enum.table import WD_TABLE_DIRECTION
#from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx2pdf import convert
from PIL import Image, ImageDraw, ImageFont


class Images:
    @staticmethod
    def gen_pdf417(data):
        import pdf417
        import os
        data = Images.format_qr_data(data)
        _data = pdf417.encode(data)
        img = pdf417.render_image(_data)
        name = 'static\\img\\pdf417_' + functions.ts(mode='file_name') + '.png'
        while os.path.exists(name):
            name = 'static\\img\\pdf417_' + functions.ts(mode='file_name') + '.png'
        img.save(name)
        return name

    @staticmethod
    def format_qr_data(data):
        ids = main.mongo.read_collection_one('data_lists', {'name': 'ids'})
        formatted = 'BF2D@Hj @r{}@i{}@p{}'.format(data['order_id'], ids['labels'], data['job_id'])
        main.mongo.update_one('data_lists', {'name': 'ids'}, {'labels': 1}, '$inc')
        if 'length' in data.keys():
            formatted += '@l' + str(int(float(data['length'])*10))
        if 'quantity' in data.keys():
            formatted += '@n' + str(data['quantity'])
        if 'pack_quantity' in data.keys():
            formatted += '@q' + str(data['pack_quantity'])
        if 'weight' in data.keys():
            formatted += '@e' + str(data['weight'])
        if 'diam' in data.keys():
            formatted += '@d' + str(data['diam'])
        if 'shape_data' in data.keys():
            formatted += '@g@Gl'
            for item in range(len(data['shape_data'])):
                if item > 0:
                    formatted += '@l'
                if isinstance(data['shape_data'][item], int):
                    formatted += str(int(data['shape_data'][item]) * 10)
                elif data['shape_data'][item].isdigit():
                    formatted += str(int(data['shape_data'][item])*10)
                if 'shape_ang' in data.keys():
                    if item < len(data['shape_ang']):
                        formatted += '@w' + str(data['shape_ang'][item])
                        continue
                formatted += '@w0'
        formatted += '@C'
        chksm = 0
        for char in formatted:
            chksm += ord(char)
        chksm = 96 - (chksm % 32)
        formatted += str(chksm) + '@'
        return formatted

    @staticmethod
    def create_shape_plot(shape, text=[], enable_text_plot=True, html=False, file_name=''):
        size = (200, 60)
        font_size = 16
        font_dir = os.getcwd()+'\\fonts\\upheavtt.ttf'
        if shape.isdigit():
            _positions = configs.shapes[shape]['draw_positions']
            im = Image.new('RGBA', size, 'white')
        else:
            im = Image.open(os.getcwd()+'\\static\\images\\specials\\girders.png')
            _positions = [[0, 25], [200, 25]]
        draw = ImageDraw.Draw(im)
        positions = []
        for i in _positions:
            positions.append(tuple(i))
        if not text:
            text = list(range(1, len(positions)))
        if shape.isdigit():
            if shape in ['331', '332']:
                draw.ellipse([(5, 5), (55, 55)],outline='black', width=3)
                positions = [(10,30),(20,30),(200,30)]
            elif shape in ['340']:
                draw.arc([(15,30),(185,50)], 170, 360, fill='black', width=3)
                text.append(Images.calc_hypotenuse(text[0],text[1]))
                text[0] = 'L = {}'.format(text[0])
                text[1] = 'R = {}'.format(text[1])
                text[2] = 'PtP = {}'.format(text[2])
                positions = [(15,10),(100,10),(185,10),(50,90)]
            elif shape == '400':
                draw.line(positions, fill="black", width=3)
                draw.arc([(15, 30), (185, 50)], 170, 360, fill='black', width=3)
                draw.line(positions, fill="black", width=3)
                positions = []
            elif shape == '401':
                draw.line(positions, fill="black", width=3)
                draw.arc([(15, 30), (185, 50)], 170, 360, fill='black', width=3)
                draw.line(positions, fill="black", width=3)
                positions = []
            elif shape == '150':
                positions = [(40,50),(15,50),(0,0),(185,50),(50,50),(50,30)]
                draw.line(positions[0:2], fill="black", width=3)
                draw.arc((15, 5, 185, 100), 180, 360, fill='black', width=3)
                draw.line(positions[3:6], fill="black", width=3)
                positions = [(40,50),(15,50),(185,-10),(0,110),(100,-30)]
            elif shape == '151':
                positions = [(40,50),(15,50),(15,30),(0,0),(185,30),(185,50),(50,50),(50,30)]
                draw.line(positions[0:3], fill="black", width=3)
                draw.arc((15, 5, 185, 60), 180, 360, fill='black', width=3)
                draw.line(positions[4:8], fill="black", width=3)
                positions = [(40,50),(15,50),(15,30),(185,-10),(185,90),(0,10),(100,70)]
            else:
                draw.line(positions, fill="black", width=3)
        if enable_text_plot:
            text_pos = []
            for i in range(len(positions) - 1):
                if i >= len(text):
                    break
                position = ((positions[i][0] + positions[i + 1][0] - len(str(text[i])) * 6) / 2,
                            (positions[i][1] + positions[i + 1][1]) / 2 - 6)
                bbox = draw.textbbox((position[0] - 1, position[1]-2), str(text[i]), font=ImageFont.truetype(font_dir, font_size + 4))
                draw.rectangle(bbox, fill="white")
                draw.text(position, str(text[i]), fill="black", font=ImageFont.truetype(font_dir, font_size))
                text_pos.append(position)
        if html:
            file_name = "C:\\Server\\static\\img\\{}.png".format(functions.ts(mode="file_name"))
            # im.save({}'.format(file_name))
        elif not file_name:
            file_name = configs.net_print_dir + "Picture\\{}.png".format(functions.ts(mode="file_name"))
        im.save(file_name)
        if html:
            file_name = file_name.replace('C:\\Server', '')
        return file_name

    @staticmethod
    def decode_qr(qr):
        code = qr.split('@')
        decode = {'order_id': "", 'job_id': ""}
        if code:
            for item in code:
                if item:
                    if item[0] == 'r':
                        decode['order_id'] = item[1:]
                    elif item[0] == 'p':
                        decode['job_id'] = item[1:]
                    elif item[0] == 'l' and 'length' not in decode.keys():  # @l also in shape_data
                        decode['length'] = item[1:]
                    elif item[0] == 'n':
                        decode['quantity'] = item[1:]
                    elif item[0] == 'q':
                        decode['pack_quantity'] = item[1:]
                    elif item[0] == 'e':
                        decode['weight'] = item[1:]
                    elif item[0] == 'd':
                        decode['diam'] = item[1:]
                    elif item[0] == 'i':
                        decode['label_id'] = item[1:]
            return decode
        return {}

    @staticmethod
    def create_pile_plot(data, html=False):
        size = (710, 520)
        font_size = 16
        # font_dir = os.getcwd()+'\\fonts\\upheavtt.ttf'
        font_dir = 'C:\\Windows\\Fonts\\arial.ttf'
        file_name = functions.ts(mode="file_name") + ".png"
        im = Image.new('RGBA', size, 'white')
        draw = ImageDraw.Draw(im)
        spiral = []
        pitch = []
        ch_diam = 0
        new_diam = ''
        for k in data:
            if 'spiral' in k and 'diam' not in k:
                if data[k]:
                    spiral.append(data[k])
                    if k.replace('spiral', 'pitch') in data:
                        pitch.append('#'+data[k.replace('spiral', 'pitch')])
                    else:
                        pitch.append('')
        # CFA
        cfa = 0
        if 'CFA' in data:
            cfa = 40
            # draw.text((655, 130), 'CFA', fill="black", font=ImageFont.truetype(font_dir, font_size))
        # Draw length line
        draw.line([(15, 50), (675, 50)], fill="black", width=3)
        draw.line([(15, 45), (15, 55)], fill="black", width=3)
        pos = 15
        for i in range(len(spiral)):
            if 'ch_diam_'+str(i) in data:
                if data['ch_diam_'+str(i)]:
                    ch_diam = 20
                    if not new_diam:
                        new_diam = data['ch_diam_'+str(i)]
            break_line = pos+int(int(spiral[i])/int(data['length'])*660)
            if break_line > 675-cfa:
                break_line = 675-cfa
            draw.line([(pos, 80+ch_diam), (break_line, 80+ch_diam)], fill="black", width=3)
            draw.line([(pos, 200-ch_diam), (break_line, 200-ch_diam)], fill="black", width=3)
            draw.text((pos+int(int(spiral[i])/int(data['length'])*660/2)-20, 30), spiral[i], fill="black", font=ImageFont.truetype(font_dir, font_size))
            draw.text((pos+int(int(spiral[i])/int(data['length'])*660/2)-20, 60), pitch[i], fill="black", font=ImageFont.truetype(font_dir, font_size))
            draw.line([(break_line, 45), (break_line, 55)], fill="black", width=3)

            if pitch[i]:
                s = pos
                ptch = int(pitch[i][1:])
                while s < break_line-2*ptch:
                    draw.line([(s, 80+ch_diam), (s + ptch, 200-ch_diam)], fill="black", width=3)
                    if s+2*ptch > break_line:
                        draw.line([(s + ptch, 200-ch_diam), (break_line, 80+ch_diam)], fill="black", width=3)
                    else:
                        draw.line([(s + ptch, 200-ch_diam), (s + 2*ptch, 80+ch_diam)], fill="black", width=3)
                    s += 2*ptch
                draw.line([(s, 80+ch_diam), (break_line, 200-ch_diam)], fill="black", width=3)

            pos = break_line
        if cfa:
            draw.line([(675-cfa, 80+ch_diam), (690, 135)], fill="black", width=3)
            draw.line([(675-cfa, 200-ch_diam), (690, 145)], fill="black", width=3)
        else:
            draw.line([(pos, 80+ch_diam), (pos, 200-ch_diam)], fill="black", width=3)
        # Draw pile
        # draw.line([(15,80),(675-cfa,80)], fill="black", width=3)
        # draw.line([(15,200),(675-cfa,200)], fill="black", width=3)
        tot_bars = int(data['bars'])
        if 'bars_1' in data:
            tot_bars += int(data['bars_1'])
        if 'bend' in data:
            data['bend'] = data['bend'].replace('+ CFA', '')
            if 'bend_len' not in data:
                data['bend_len'] = '20'
            if data['bend'] == 'שושנה':
                draw.line([(15, 80), (15, 100)], fill="black", width=3)
                draw.line([(15, 200), (15, 220)], fill="black", width=3)
                draw.text((25, 90), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                draw.text((25, 210), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                for i in range(tot_bars):
                    x = round(122.5 + 67.5 * math.sin(2*math.pi*i/tot_bars))
                    y = round(427.5 + 67.5 * math.cos(2*math.pi*i/tot_bars))
                    x1 = round(122.5 + 55 * math.sin(2*math.pi*i/tot_bars+0.2))
                    y1 = round(427.5 + 55 * math.cos(2*math.pi*i/tot_bars+0.2))
                    draw.line([(x, y), (x1, y1)], fill="black", width=4)
            elif data['bend'] == 'חוץ':
                draw.line([(15, 80), (15, 60)], fill="black", width=3)
                draw.line([(15, 200), (15, 220)], fill="black", width=3)
                draw.text((25, 60), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                draw.text((25, 210), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                for i in range(tot_bars):
                    x = round(122.5 + 67.5 * math.sin(2*math.pi*i/tot_bars))
                    y = round(427.5 + 67.5 * math.cos(2*math.pi*i/tot_bars))
                    x1 = round(122.5 + 85 * math.sin(2*math.pi*i/tot_bars))
                    y1 = round(427.5 + 85 * math.cos(2*math.pi*i/tot_bars))
                    draw.line([(x, y), (x1, y1)], fill="black", width=4)
            elif data['bend'] == 'פנים':
                draw.line([(15, 80), (15, 100)], fill="black", width=3)
                draw.line([(15, 200), (15, 180)], fill="black", width=3)
                draw.text((25, 90), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                draw.text((25, 180), data['bend_len'], fill="black",
                          font=ImageFont.truetype(font_dir, font_size))
                for i in range(tot_bars):
                    x = round(122.5 + 67.5 * math.sin(2*math.pi*i/tot_bars))
                    y = round(427.5 + 67.5 * math.cos(2*math.pi*i/tot_bars))
                    x1 = round(122.5 + 45 * math.sin(2*math.pi*i/tot_bars))
                    y1 = round(427.5 + 45 * math.cos(2*math.pi*i/tot_bars))
                    draw.line([(x, y), (x1, y1)], fill="black", width=4)
            elif data['bend'] == 'טבעת חיזוק':
                draw.line([(20, 80), (20, 200)], fill="black", width=3)
                draw.line([(pos, 80 + ch_diam), (pos, 200 - ch_diam)], fill="black", width=3)
        # else:
        for i in range(tot_bars):
            x = round(122.5 + 67.5 * math.sin(2*math.pi*i/tot_bars))
            y = round(427.5 + 67.5 * math.cos(2*math.pi*i/tot_bars))
            draw.ellipse([(x-3, y-3), (x+3, y+3)], outline='black', width=4)
        # Draw length bars
            # #1
        draw.line([(15,290),(675,290)], fill="black", width=3)
        if 'bars_len' not in data:
            data['bars_len'] = data['length']
        bars_decript = u'{} X @{} X {}'.format(data['bars'], data['bars_diam'], data['bars_len'])
        draw.text((400, 270), 'מוטות אורך', direction='rtl', fill="black",
                  font=ImageFont.truetype(font_dir, font_size))
        draw.text((50, 270), bars_decript, fill="black",
                  font=ImageFont.truetype(font_dir, font_size))
            # #2
        if 'bars_1' in data:
            if 'bars_len_1' not in data:
                data['bars_len_1'] = data['length']
            draw.line([(15,330),(675*(int(data['bars_len_1'])/int(data['bars_len'])),330)], fill="black", width=3)
            bars_decript = u'{} X @{} X {}'.format(data['bars_1'], data['bars_diam_1'], data['bars_len_1'])
            draw.text((400, 310), 'מוטות אורך 2', fill="black",
                      font=ImageFont.truetype(font_dir, font_size))
            draw.text((50, 310), bars_decript, fill="black",
                      font=ImageFont.truetype(font_dir, font_size))
        # Draw pipes
        if 'pipe_len' in data:
            pipe_decript = u'{} X @{} X {}'.format(data['pipes'], data['pipe_diam'], data['pipe_len'])
            draw.line([(15,250),(675,250)], fill="black", width=3)
            draw.text((400, 230), 'צינורות', direction='rtl', fill="black",
                      font=ImageFont.truetype(font_dir, font_size))
            draw.text((50, 230), pipe_decript, fill="black",
                      font=ImageFont.truetype(font_dir, font_size))
        # Draw rings
        draw.ellipse([(415, 360), (550, 495)], outline='black', width=2)
        rings_ov = u'{} X @{}'.format(data['rings'], data['rings_diam'])
        draw.text((460, 420), 'טבעות', fill="black", direction='rtl', font=ImageFont.truetype(font_dir, font_size))
        draw.text((450, 440), rings_ov, fill="black", font=ImageFont.truetype(font_dir, font_size))
        # Pile overview
        draw.ellipse([(55, 360), (190, 495)], outline='black', width=2)

        draw.line([(123, 360), (250, 360)], fill="black", width=1)
        draw.line([(123, 495), (250, 495)], fill="black", width=1)
        draw.line([(250, 360), (250, 495)], fill="black", width=3)
        draw.line([(245, 360), (255, 360)], fill="black", width=3)
        draw.line([(245, 495), (255, 495)], fill="black", width=3)

        spiral_ov = u' @{}'.format(data['spiral_diam'])
        pile_ov = u'{}'.format(data['pile_diam'])
        draw.text((85, 420), 'קוטר ספירלה', fill="black", direction='rtl', font=ImageFont.truetype(font_dir, font_size))
        draw.text((90, 440), spiral_ov, fill="black", font=ImageFont.truetype(font_dir, font_size))
        draw.text((260, 400), 'קוטר כלונס', fill="black", direction='rtl', font=ImageFont.truetype(font_dir, font_size))
        draw.text((260, 420), pile_ov, fill="black", font=ImageFont.truetype(font_dir, font_size))
        if ch_diam:
            # draw.ellipse([(55, 360), (190, 495)], outline='black', width=2)
            draw.text((290, 420), u'{}'.format(' \ '+new_diam), fill="black", font=ImageFont.truetype(font_dir, font_size))
        # draw.text((500, 500), 'fff', fill="black", direction='rtl', font=ImageFont.truetype(font_dir, font_size))
        if html:
            file_name = 'static\\img\\' + file_name
            im.save('C:\\Server\\' + file_name)
        else:
            file_name = configs.net_print_dir + "Picture\\" + file_name
            im.save(file_name)
        return file_name

    @staticmethod
    def create_mesh_plot(data, html=False):
        size = (720, 920)
        font_size = 16
        font_dir = 'C:\\Windows\\Fonts\\arial.ttf'
        file_name = functions.ts(mode="file_name") + ".png"
        im = Image.new('RGBA', size, 'white')
        draw = ImageDraw.Draw(im)

        # wid_bar = '{}X   {}@{}'.format(data['width'], data['x_bars'], data['diam_x'], set(data['x_pitch']))
        # len_bar = '{}X   {}@{}'.format(data['length'], data['y_bars'], data['diam_y'], set(data['y_pitch']))
        # draw.ellipse([(730, 384), (738, 392)], outline='black', width=1)
        # draw.line([(729, 383), (739, 393)], fill="black", width=1)
        # draw.ellipse([(330, 866), (338, 874)], outline='black', width=1)
        # draw.line([(329, 865), (339, 875)], fill="black", width=1)

        draw.line([(20, 5), (20, 810)], fill="black", width=1)
        draw.line([(15, 5), (25, 5)], fill="black", width=1)
        draw.line([(15, 810), (25, 810)], fill="black", width=1)
        draw.text((625, 480), data['length'], fill="black", direction='rtl',
                  font=ImageFont.truetype(font_dir, font_size, encoding="utf-8"))
        draw.line([(620, 5), (620, 810)], fill="black", width=1)
        draw.line([(615, 5), (625, 5)], fill="black", width=1)
        draw.line([(615, 810), (625, 810)], fill="black", width=1)

        draw.line([(50, 840), (600, 840)], fill="black", width=1)
        draw.line([(50, 835), (50, 845)], fill="black", width=1)
        draw.line([(600, 835), (600, 845)], fill="black", width=1)
        draw.text((300, 850), data['width'], fill="black", direction='rtl',
                  font=ImageFont.truetype(font_dir, font_size, encoding="utf-8"))
        draw.line([(50, 870), (600, 870)], fill="black", width=1)
        draw.line([(50, 865), (50, 875)], fill="black", width=1)
        draw.line([(600, 865), (600, 875)], fill="black", width=1)
        x_prop = 550/float(data['width'])
        y_prop = 795/float(data['length'])
        x_start = 50
        y_start = 15
        # data['x_length'].reverse()
        # data['x_pitch'].reverse()
        if 'y_length' not in data:
            data['trim_x_start'] = '5'
            data['trim_x_end'] = '5'
            data['trim_y_start'] = str(float(data['y_pitch'])/2)
            data['trim_y_end'] = str(float(data['y_pitch'])/2)
            data['y_length'] = [str(int(float(data['length'])-float(data['trim_y_start'])-float(data['trim_y_end'])))]
            data['y_pitch'] = [data['y_pitch']]
            data['x_length'] = [str(int(float(data['width'])-float(data['trim_x_start'])-float(data['trim_x_end'])))]
            data['x_pitch'] = [data['x_pitch']]
        data['y_length'].reverse()
        data['y_pitch'].reverse()
        draw.text((x_start + int(float(data['trim_x_start'])/2), 810), data['trim_x_start'].replace('.0', ''), fill="black", direction='rtl',
                  font=ImageFont.truetype(font_dir, 12))
        draw.text((30, 5 + int(float(data['trim_y_end'])/2)), data['trim_y_end'].replace('.0', ''), fill="black", direction='rtl', font=ImageFont.truetype(font_dir, 12))
        x_start += int(float(data['trim_x_start'])*x_prop)
        y_start += int(float(data['trim_y_end'])*y_prop)
        for i in range(len(data['x_length'])):
            leng = int(data['x_length'][i])
            pitch = int(data['x_pitch'][i])
            for x in range(int(leng/pitch)):
                pos = x_start + int(float(data['x_pitch'][i])/2)
                draw.line([(x_start, 5), (x_start, 810)], fill="black", width=2)
                draw.line([(x_start, 845), (x_start, 835)], fill="black", width=1)
                draw.text((pos, 810), data['x_pitch'][i], fill="black", direction='rtl', font=ImageFont.truetype(font_dir, 12))
                x_start += int(pitch)*x_prop
        # draw.line([(x_start, 400), (620, 370)], fill="black", width=2)
        # draw.line([(620, 370), (720, 370)], fill="black", width=2)
        for i in range(len(data['y_length'])):
            leng = int(data['y_length'][i])
            pitch = int(data['y_pitch'][i])
            for x in range(int(leng/pitch)):
                # if x+i == 0:
                #     draw.line([(590, y_start), (620, 270)], fill="black", width=2)
                #     draw.line([(620, 270), (720, 270)], fill="black", width=2)
                pos = y_start + int(float(data['y_pitch'][i])/2)
                draw.line([(50, y_start), (600, y_start)], fill="black", width=2)
                draw.line([(15, y_start), (25, y_start)], fill="black", width=1)
                draw.text((30, pos), data['y_pitch'][i], fill="black", direction='rtl', font=ImageFont.truetype(font_dir, 12))
                y_start += int(pitch)*y_prop
        draw.line([(x_start, 5), (x_start, 810)], fill="black", width=2)
        draw.line([(x_start, 845), (x_start, 835)], fill="black", width=1)
        draw.text((x_start, 810), data['trim_x_end'].replace('.0', ''), fill="black", direction='rtl',
                  font=ImageFont.truetype(font_dir, 12))
        draw.line([(50, y_start), (600, y_start)], fill="black", width=2)
        draw.line([(15, y_start), (25, y_start)], fill="black", width=1)
        draw.text((30, y_start), data['trim_y_start'].replace('.0', ''), fill="black", direction='rtl', font=ImageFont.truetype(font_dir, 12))
        # im.show()
        if html:
            file_name = 'static\\img\\' + file_name
            im.save('C:\\Server\\' + file_name)
        else:
            im.save(configs.net_print_dir + "Picture\\" + file_name)
        return file_name

    @staticmethod
    def calc_hypotenuse(length, radius):
        length = int(length)
        radius = int(radius)
        ang = 180 * length / (math.pi * radius)
        hyp = radius * math.sin(math.radians(ang)) / math.sin(math.radians((180 - ang) / 2))
        return int(hyp)


class Bartender:
    @staticmethod
    def net_print(order_id, printer, print_type, disable_weight=False, select_jobs=[], split=''):
        from datetime import datetime, timedelta
        # Format data
        rows, info = orders.get_order_data(order_id, reverse=False, split=split)
        if print_type == 'label':
            if 'last_label_print' in info:
                if info['last_label_print'] > datetime.now()-timedelta(seconds=10):
                    return
            main.mongo.update_one('orders', {'order_id': order_id}, {'info.last_label_print': datetime.now()}, '$set')
        info['order_split'] = split
        if select_jobs:
            rlen = len(rows)
            for i in range(rlen):
                index = rlen - 1 - i
                if rows[index]['job_id'] not in select_jobs:
                    rows.pop(index)
        if info['type'] in ['R', 'K']:
            info['type'] = 'regular'
        bt_format = configs.bartender_formats[info['type']][print_type]
        print_data = []
        element_buf = []
        if 'date_delivery' in info:
            info['date_delivery'] = '/'.join(info['date_delivery'].split('-')[::-1])
        if 'rebar' in info['type'] and 'page' in print_type:
            info['temp_select'] = 1
            print_data.append(info)
            total_weight = 0
            table_cells = 7
            table_rows = 2
            table_selector = 2
            for row_n in range(math.ceil(len(rows) / table_rows)):
                template_row = {'temp_select': table_selector}
                for indx in range(table_rows):
                    if table_rows * row_n + indx >= len(rows):
                        break
                    n = table_rows * row_n + indx
                    i = table_cells * indx
                    row = rows[n]
                    if 'status' in row:
                        if row['status'] in ['Canceled', 'canceled']:
                            continue
                    if float(row['diam_x']) > 10:
                        row['description'] = row['description'].replace("רשת סטנדרט","מיוחדת לפי תוכנית כוורת מרותכת דקה")
                    template_row["tb" + str(1 + i)] = row['job_id']
                    template_row["tb" + str(2 + i)] = row['mkt']
                    template_row["tb" + str(4 + i)] = row['description']
                    template_row["tb" + str(5 + i)] = row['quantity']
                    if rows[n]['mkt'] != "2005020000":
                        if float(row['diam_x']) > 10:
                            row['description'] = row['description'].replace("רשת סטנדרט","מיוחדת לפי תוכנית כוורת מרותכת דקה")
                            template_row["tb" + str(3 + i)] = "מיוחדת לפי תוכנית כוורת מרותכת דקה"
                        else:
                            template_row["tb" + str(3 + i)] = "רשת סטנדרט"
                        if disable_weight:
                            template_row["tb" + str(6 + i)] = '---'
                        else:
                            template_row["tb" + str(6 + i)] = round(row['weight'] / int(row['quantity']), 2)
                    else:
                        template_row["tb" + str(3 + i)] = "מיוחדת לפי תוכנית כוורת מרותכת דקה"
                        if float(row['diam_x']) >= 18 or float(row['diam_y']) >= 18:
                            template_row["tb" + str(3 + i)] = template_row["tb" + str(3 + i)].replace('מיוחדת', 'אלמנט')
                        if float(row['diam_x']) >= 14 or float(row['diam_y']) >= 14:
                            template_row["tb" + str(3 + i)] = template_row["tb" + str(3 + i)].replace('דקה', 'עבה')
                        if disable_weight:
                            template_row["tb" + str(6 + i)] = '---'
                        else:
                            template_row["tb" + str(6 + i)] = round(row['weight'] / int(row['quantity']), 2)
                    if 'bend1' in row or 'bend2' in row or 'bend3' in row or 'כיפוף' in row:
                        template_row["tb" + str(3 + i)] += ' + כיפוף'
                        bt_format = configs.bartender_formats['rebar_special'][print_type]
                    if 'חיתוך' in row:
                        template_row["tb" + str(3 + i)] += ' + חיתוך'
                        bt_format = configs.bartender_formats['rebar_special'][print_type]
                    if disable_weight:
                        template_row["tb" + str(7 + i)] = '---'
                        total_weight = '---'
                    else:
                        template_row["tb" + str(7 + i)] = int(row['weight'])
                        total_weight += row['weight']
                print_data.append(template_row.copy())
            if isinstance(total_weight, float):
                total_weight = int(total_weight)
            print_data.append({'temp_select': 3, 'tb1': total_weight})
        else:
            el_buf = []
            _rows = []
            for row in rows:
                if 'status' in row:
                    if row['status'] in ['Canceled', 'canceled']:
                        continue
                bends = []
                if 'bend1' in row:
                    bends.append(int(row['bend1']))
                if 'bend2' in row:
                    bends.append(int(row['bend2']))
                if 'bend3' in row:
                    bends.append(int(row['bend3']))
                if bends:
                    if len(bends) == 2:
                        row['bend_img_dir'] = Images.create_shape_plot('405', bends)
                    elif len(bends) == 3:
                        row['bend_img_dir'] = Images.create_shape_plot('404', bends)
                    row['bend_img_dir'] = row['bend_img_dir'].split('\\')[-1]
                if 'status' in row:
                    if row['status'] in ['Canceled', 'canceled']:
                        continue
                    elif print_type == 'label' and row['status'] not in ['NEW', 'Processed', 'Production', 'InProduction']:
                        continue
                if 'CFA' in row:
                    if 'bend' in row:
                        row['bend'] += '+ CFA'
                    else:
                        row['bend'] = 'CFA'
                for el in row:
                    if 'weight' in el and 'unit' not in el:
                        row[el] = round(float(row[el]))
                if 'element' not in row:
                    row['element'] = ''
                if row['element'] and print_type == 'label':
                    if row['element'][0] == 'ק' and row['element'] not in el_buf:
                        for r in rows:
                            if 'element' in r:
                                if r['element'] == row['element']:
                                    _rows.append(r)
                        el_buf.append(row['element'])
                if row['element'] in el_buf:
                    continue
                if info['type'] == 'piles' and 'label' in print_type:
                    row['pack_quantity'] = 1
                if 'pack_quantity' in row:
                    if int(row['pack_quantity']) < 1:
                        del row['pack_quantity']
                if 'pack_quantity' in row and ('label' in print_type or info['type'] == 'regular'):
                    pack_rows = []
                    row['quantity'] = int(row['quantity'])
                    if not disable_weight:
                        unit_weight = float(row['weight']) / int(row['quantity'])
                    row['pack_quantity'] = int(row['pack_quantity'])
                    total_packs = math.ceil(row['quantity']/row['pack_quantity'])
                    pack_index = 1
                    while row['quantity'] > 0:
                        pack_row = row.copy()
                        if 'unit_weight' not in pack_row and not disable_weight:
                            pack_row['unit_weight'] = round(unit_weight)
                        if row['quantity'] - row['pack_quantity'] >= 0:
                            pack_row['quantity'] = row['pack_quantity']
                            # if 'unit_weight' not in pack_row and not disable_weight:
                            #     pack_row['unit_weight'] = unit_weight
                            if not disable_weight:
                                pack_row['weight'] = round(unit_weight*row['pack_quantity'])
                            pack_row['pack_num'] = '{}/{}'.format(pack_index, total_packs)
                        else:
                            pack_row['pack_num'] = '{}/{}'.format(pack_index, total_packs)
                            if not disable_weight:
                                pack_row['weight'] = round(unit_weight*row['quantity'])
                        pack_rows.append(pack_row)
                        pack_index += 1
                        row['quantity'] -= row['pack_quantity']
                    _rows.extend(pack_rows)
                    continue
                _rows.append(row)
            rows = _rows.copy()
            index = 0
            for row in rows:
                if 'status' in row:
                    if row['status'] in ['Canceled', 'canceled']:
                        continue
                if row['job_id'] == "0":
                    break
                line = {}
                kora = {'temp_select': 1, 'z15': 0, 'z16': 0, 'img_dir': 'kora', 'order_split': split}
                kora.update(info)  # Added 22.7.24 fix, when kora first row, no suply date
                try:
                    if 'unit_weight' not in row:
                        if int(row['quantity']) <= 0:
                            row['unit_weight'] = 0
                        else:
                            row['unit_weight'] = int(float(row['weight']) / int(row['quantity']))
                except Exception as e:
                    print('issue with unit weight code\n', e)
                for obj in row:
                    if disable_weight and 'weight' in obj:
                        line[obj] = '---'
                    else:
                        line[obj] = row[obj]
                for obj in info:
                    if disable_weight and 'weight' in obj:
                        line[obj] = '---'
                    else:
                        line[obj] = info[obj]
                if 'shape_data' in line:
                    file_name = configs.net_print_dir + "Picture\\{}_{}_{}.png".format(functions.ts(mode="file_name"), order_id, line['job_id'])
                    line['img_dir'] = Images.create_shape_plot(line['shape'], line['shape_data'], file_name=file_name).split('\\')[-1].replace('.png', '')
                    if ((len(row['shape_data']) > 2) and (row['weight'] / int(row['quantity']) <= 2) \
                            and row['shape'] not in ['332', '49', '59']) or row['shape'] in configs.circle:
                        line['circle'] = 'כן'
                elif 'shape' in line:
                    file_name = configs.net_print_dir + "Picture\\{}_{}_{}.png".format(functions.ts(mode="file_name"), order_id, line['job_id'])
                    line['img_dir'] = Images.create_shape_plot(line['shape'], [line['shape']], file_name=file_name).split('\\')[
                        -1].replace('.png', '')
                    line['temp_select'] = 1
                line['barcode_data'] = Images.format_qr_data(line)
                if 'element' in line:
                    if len(line['element']) > 0:
                        if line['element'][0] == 'ק' and line['element'] not in element_buf:# and 'label' in print_type:
                            item_to_copy = ['order_id', 'element', 'costumer_name', 'comment', 'costumer_site']
                            # kora['barcode_data'] = []
                            for item in item_to_copy:
                                if item in line:
                                    kora[item] = line[item]
                            for _row in rows:
                                if _row['element'] == line['element']:
                                    # kora['barcode_data'].append(_row['job_id'])
                                    kora['z15'] += 1
                                    kora['z16'] += _row['weight']
                            # kora['barcode_data'] = 'BF2D@Hj @r{}@i@p{}'.format(kora['order_id'],','.join(kora['barcode_data']))
                            kora['z16'] = int(kora['z16'])
                            kora['weight'] = kora['z16']
                            kora['quantity'] = kora['z15']
                            element_buf.append(line['element'])
                            # # Header indicator
                            if info['type'] == 'regular':
                                if index % 8 == 0:
                                    kora['z19'] = 1
                            index += 1
                            print_data.append(kora)
                # Header indicator
                if info['type'] in ['regular','piles']:
                    if index % 8 == 0:
                        line['z19'] = 1
                index += 1
                print_data.append(line.copy())
        if not print_data:
            return
        Bartender.bt_create_print_file(printer, bt_format[0], print_data)
        # Print additional summary info
        if len(bt_format) > 1:
            summary_data = Bartender.gen_summary_data(rows, info, disable_weight)
            Bartender.bt_create_print_file(printer, bt_format[1], summary_data)

    @staticmethod
    def gen_summary_data(rows, info, disable_weight):
        info['temp_select'] = 1
        if disable_weight:
            if 'total_weight' in info:
                info['total_weight'] = '---'
        summary_data = []
        if 'rebar' in info['type']:
            for row in rows:
                if 'status' in row:
                    if row['status'] in ['Canceled', 'canceled']:
                        continue
                if row['job_id'] == "0":
                    break
                line = {}
                bends = []
                for obj in row:
                    if obj == 'diam':
                        line['diam_x'] = row[obj]
                        line['diam_y'] = row[obj]
                    elif obj == 'length':
                        if 'y_length' in row.keys():
                            line['length_trim'] = '['+']['.join(row['y_length'])+']'
                        else:
                            line['length_trim'] = 600
                    elif obj == 'width':
                        if 'x_length' in row.keys():
                            line['width_trim'] = '['+']['.join(row['x_length'])+']'
                        else:
                            line['width_trim'] = 250
                    elif '_pitch' in obj and not isinstance(row[obj], str):
                        line[obj] = '(' + ')('.join(list(set(row[obj]))) + ')'
                    elif 'bend' in obj:
                        bends.append(int(row[obj]))
                    else:
                        if isinstance(row[obj], float):
                            line[obj] = round(row[obj])
                        else:
                            line[obj] = row[obj]
                for obj in info:
                    line[obj] = info[obj]
                if bends:
                    if len(bends) == 2:
                        line['bend_img_dir'] = Images.create_shape_plot('405', bends).split('\\')[-1].replace('.png', '')
                    elif len(bends) == 3:
                        line['bend_img_dir'] = Images.create_shape_plot('404', bends).split('\\')[-1].replace('.png', '')
                line['barcode_data'] = Images.format_qr_data(line)
                line['img_dir'] = Images.create_mesh_plot(row)
                summary_data.append(line)
        elif 'piles' in info['type']:
            summary_data = rows.copy()
            for r in summary_data:
                r.update(info)
                r['barcode_data'] = Images.format_qr_data(r)
                for i in r:
                    if r[i] == '0':
                        r[i] = ''
                    if disable_weight and 'weight' in i:
                        r[i] = '---'
                r['img_dir'] = Images.create_pile_plot(r)
        else:
            table_data = {}
            spec_keys = ['חיתוך', 'כיפוף', 'חישוק', 'חישוק מיוחד', 'אלמנט מיוחד חלק', 'ספסלים', 'ספירלים', 'תוספת_ברזל_עגול_עד_12_ממ', 'תוספת_ברזל_עגול_מעל_14_ממ',
                   'ברזל_ארוך', 'תוספת_ברזל_28_ממ_ומעלה']
            special_sum = {}
            for i in spec_keys:
                special_sum[i] = {'qnt': 0, 'weight': 0}
            total_weight = 0
            summary_data.append(info)
            for row in rows:
                total_weight += row['weight']
                row['length'] = int(float(row['length']))
                if 'bar_type' not in row:
                    row['bar_type'] = "מצולע"
                # Summary data
                quantity = int(row['quantity'])
                if row['diam'] in table_data.keys():
                    table_data[row['diam']]['weight'] += row['weight']
                    table_data[row['diam']]['length'] += int(row['length']) * quantity
                else:
                    table_data[row['diam']] = {'weight': row['weight'], 'length': int(float(row['length'])) * quantity,
                                               'weight_per_M': configs.weights[row['diam']], 'type': row['bar_type']}
                # Special summary data
                if row['shape'] not in ["905"]:
                    if 'חיתוך' not in special_sum.keys():
                        special_sum['חיתוך'] = {'qnt': 0, 'weight': 0}
                    special_sum['חיתוך']['qnt'] += quantity
                    special_sum['חיתוך']['weight'] += row['weight']
                if row['shape'] not in ["1", "905"]:
                    if 'כיפוף' not in special_sum.keys():
                        special_sum['כיפוף'] = {'qnt': 0, 'weight': 0}
                    special_sum['כיפוף']['qnt'] += quantity
                    special_sum['כיפוף']['weight'] += row['weight']
                if row['shape'] in ['332']:
                    if 'ספירלים' not in special_sum.keys():
                        special_sum['ספירלים'] = {'qnt': 0, 'weight': 0}
                    special_sum['ספירלים']['qnt'] += quantity
                    special_sum['ספירלים']['weight'] += row['weight']
                if row['shape'] in ['200', '201', '202', '203', '204', '205', '206']:
                    if 'חישוק מיוחד' not in special_sum.keys():
                        special_sum['חישוק מיוחד'] = {'qnt': 0, 'weight': 0}
                    special_sum['חישוק מיוחד']['qnt'] += quantity
                    special_sum['חישוק מיוחד']['weight'] += row['weight']
                elif row['shape'] in ['34', '64'] and row['bar_type'] == 'חלק':
                    if 'אלמנט מיוחד חלק' not in special_sum.keys():
                        special_sum['אלמנט מיוחד חלק'] = {'qnt': 0, 'weight': 0}
                    special_sum['אלמנט מיוחד חלק']['qnt'] += quantity
                    special_sum['אלמנט מיוחד חלק']['weight'] += row['weight']
                elif row['shape'] in ['49','59']:
                    if 'ספסלים' not in special_sum.keys():
                        special_sum['ספסלים'] = {'qnt': 0, 'weight': 0}
                    special_sum['ספסלים']['qnt'] += quantity
                    special_sum['ספסלים']['weight'] += row['weight']
                elif ((len(row['shape_data']) > 2) and (row['weight'] / int(row['quantity']) <= 2) and info['costumer_id'] not in ['143']) \
                        or row['shape'] in configs.circle:
                    if 'חישוק' not in special_sum.keys():
                        special_sum['חישוק'] = {'qnt': 0, 'weight': 0}
                    special_sum['חישוק']['qnt'] += quantity
                    special_sum['חישוק']['weight'] += row['weight']
                if int(row['length']) > 1600:
                    if 'ברזל_ארוך' not in special_sum.keys():
                        special_sum['ברזל_ארוך'] = {'qnt': 0, 'weight': 0}
                    special_sum['ברזל_ארוך']['qnt'] += quantity
                    special_sum['ברזל_ארוך']['weight'] += row['weight']
                if float(row['diam']) >= 28:
                    if 'תוספת_ברזל_28_ממ_ומעלה' not in special_sum.keys():
                        special_sum['תוספת_ברזל_28_ממ_ומעלה'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_28_ממ_ומעלה']['qnt'] += quantity
                    special_sum['תוספת_ברזל_28_ממ_ומעלה']['weight'] += row['weight']
                if row['bar_type'] == 'חלק':
                    if float(row['diam']) <= 12:
                        if 'תוספת_ברזל_עגול_עד_12_ממ' not in special_sum.keys():
                            special_sum['תוספת_ברזל_עגול_עד_12_ממ'] = {'qnt': 0, 'weight': 0}
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ']['qnt'] += quantity
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ']['weight'] += row['weight']
                    elif float(row['diam']) >= 14:
                        if 'תוספת_ברזל_עגול_מעל_14_ממ' not in special_sum.keys():
                            special_sum['תוספת_ברזל_עגול_מעל_14_ממ'] = {'qnt': 0, 'weight': 0}
                        special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['qnt'] += quantity
                        special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['weight'] += row['weight']
            # Reorder diam summary list
            # table_data = OrderedDict(table_data.items(), key=lambda t: t[0])
            li = list(table_data.keys())
            sort_keys = list(map(float, li))
            sort_keys.sort()

            temp = {}
            for key in sort_keys:
                temp[str(key).replace('.0', '')] = table_data[str(key).replace('.0', '')]
            table_data = temp
            to_del = []
            for key in special_sum:
                if special_sum[key]['qnt'] == 0:
                    to_del.append(key)
            for key in to_del:
                del special_sum[key]
            # Bartender Table filler
            # Summary
            table_cells = 5
            table_rows = 3
            table_selector = 2
            for row in range(math.ceil(len(table_data.keys()) / table_rows)):
                template_row = {'temp_select': table_selector}
                for indx in range(table_rows):
                    if table_rows * row + indx >= len(table_data.keys()):
                        break
                    diam = list(table_data.keys())[table_rows * row + indx]
                    template_row["tb" + str(1 + table_cells * indx)] = table_data[diam]['type']
                    template_row["tb" + str(2 + table_cells * indx)] = diam
                    template_row["tb" + str(3 + table_cells * indx)] = table_data[diam]['length']
                    if disable_weight:
                        template_row["tb" + str(4 + table_cells * indx)] = '---'
                        template_row["tb" + str(5 + table_cells * indx)] = '---'
                    else:
                        template_row["tb" + str(4 + table_cells * indx)] = table_data[diam]['weight_per_M']
                        template_row["tb" + str(5 + table_cells * indx)] = int(table_data[diam]['weight'])
                summary_data.append(template_row.copy())
            # Bartender Table filler
            # Special summary
            table_selector = 3
            table_cells = 3
            table_rows = 3
            spec_sum_lines = math.ceil(len(special_sum) / table_rows)
            if isinstance(total_weight, float):
                total_weight = int(total_weight)
            template_row = {'temp_select': table_selector, 'tb30': total_weight}
            if disable_weight:
                template_row['tb30'] = ''
            # Add total weight to summary
            table_selector = 4
            summary_data.append(template_row.copy())
            if spec_sum_lines:
                for row in range(spec_sum_lines):
                    template_row = {'temp_select': table_selector}
                    for indx in range(table_rows):
                        if table_rows * row + indx >= len(special_sum.keys()):
                            break
                        description = list(special_sum.keys())[table_rows * row + indx]
                        template_row["tb" + str(1 + table_cells * indx)] = description.replace("_", " ")
                        template_row["tb" + str(2 + table_cells * indx)] = special_sum[description]['qnt']
                        if disable_weight:
                            template_row["tb" + str(3 + table_cells * indx)] = '---'
                        else:
                            template_row["tb" + str(3 + table_cells * indx)] = int(special_sum[description]['weight'])
                    summary_data.append(template_row.copy())
        return summary_data

    @staticmethod
    def bt_create_print_file(printer, btw_file, print_data):
        # Bar tender btw
        header = '%BTW% /AF=H:\\NetCode\\margolisys\\' + btw_file + '.btw /D="%Trigger File Name%" /PRN=' \
                 + printer.upper() + ' /R=3 /P /DD\n%END%\n'
        file_name = print_data[0]['order_id'] + "_" + functions.ts(mode="file_name") + ".tmp"
        file_dir = os.path.join(configs.net_print_dir, 'temp', file_name)
        # --------- for testing ----------
        testing = False
        if testing:
            file_dir = "H:\\NetCode\\margolisys\\1.txt"
            # file_dir = "C:\\copy_here\\1.txt"
        # --------------------------------
        # Write btw temp file
        with open(file_dir, 'w', encoding='cp1255') as print_file:
            if not testing:
                print_file.write(header)
            for line in print_data:
                line['company_name'] = configs.company_name
                print_line = ""
                if btw_file in configs.print_dict.keys():
                    bt_dict = configs.print_dict[btw_file]
                else:
                    bt_dict = configs.print_dict["default"]
                for item in bt_dict:
                    if item in line.keys():
                        print_line += str(line[item]) + '~'
                    else:
                        print_line += '~'
                print_file.write(print_line + "\n")
            functions.log('bt_print', '{} : {}'.format(printer, print_data[0]['order_id']))
        if main.session['username'] not in ['baruch', 'Baruch']:
            shutil.copyfile(file_dir, file_dir.replace('\\temp', '').replace('.tmp', '.txt'))
        return file_dir


class Print:
    @staticmethod
    def print_template(order_id, disable_weight, select_jobs=[], split=None):
        rows, info = orders.get_order_data(order_id, reverse=False, split=split)
        order_summary = []
        rows_to_print = []
        if info['type'] == 'regular':
            order_summary = Print.gen_summary_data(rows, disable_weight, info['costumer_id'])
        for r in rows:
            if r['job_id'] in select_jobs or not select_jobs:
                if 'status' in r:
                    if r['status'] in ['Canceled', 'canceled']:
                        continue
                if info['type'] == 'regular':
                    if ((len(r['shape_data']) > 2) and (r['weight'] / int(r['quantity']) <= 2) and r['shape'] not in ['332', '49', '59']) or r['shape'] in configs.circle:
                        r['circle'] = 'כן'
                    r['img_dir'] = Images.create_shape_plot(r['shape'], r['shape_data'], html=True)
                elif 'rebar' in info['type']:
                    r['img_dir'] = Images.create_mesh_plot(r, html=True)
                    r['x_pitch'] = '(' + ')('.join(list(set(r['x_pitch']))) + ')'
                    r['y_pitch'] = '(' + ')('.join(list(set(r['y_pitch']))) + ')'
                    bends = []
                    if 'bend1' in r:
                        bends.append(int(r['bend1']))
                    if 'bend2' in r:
                        bends.append(int(r['bend2']))
                    if 'bend3' in r:
                        bends.append(int(r['bend3']))
                    if bends:
                        if len(bends) == 2:
                            r['bend_img_dir'] = Images.create_shape_plot('405', bends, html=True)
                        elif len(bends) == 3:
                            r['bend_img_dir'] = Images.create_shape_plot('404', bends, html=True)
                elif info['type'] == 'piles':
                    r['img_dir'] = Images.create_pile_plot(r, html=True)
                elif info['type'] == 'girders':
                    r['img_dir'] = Images.create_shape_plot(r['shape'], [r['shape']], html=True)
                else:
                    return '', 204
                r['pdf417_dir'] = Images.gen_pdf417(r)
                if disable_weight:
                    for k in r:
                        if 'weight' in k:
                            r[k] = ''
                rows_to_print.append(r)
        order = {'order_id': order_id, 'rows': rows_to_print, 'info': info}
        return main.render_template('/print/page/{}.html'.format(info['type']), order_data=order, summary=order_summary, print_ts=functions.ts())

    @staticmethod
    def gen_summary_data(rows, disable_weight, costumer_id):
        diams = {}
        spec_keys = ['חיתוך', 'כיפוף', 'חישוק', 'חישוק מיוחד', 'ספסלים', 'מדרגה', 'ספירלים', 'תוספת_ברזל_עגול_עד_12_ממ',
                     'תוספת_ברזל_עגול_מעל_14_ממ',
                     'ברזל_ארוך', 'תוספת_ברזל_28_ממ_ומעלה']
        special_sum = {}
        for i in spec_keys:
            special_sum[i] = {'qnt': 0, 'weight': 0}
            if disable_weight:
                special_sum[i]['weight'] = ''
        total_weight = 0
        for row in rows:
            if not disable_weight:
                total_weight += row['weight']
            row['length'] = int(float(row['length']))
            if 'bar_type' not in row:
                row['bar_type'] = "מצולע"
            # Summary data
            quantity = int(row['quantity'])
            if row['diam'] in diams.keys():
                if not disable_weight:
                    diams[row['diam']]['weight'] += row['weight']
                diams[row['diam']]['length'] += int(row['length']) * quantity
            else:
                diams[row['diam']] = {'weight': row['weight'], 'length': int(float(row['length'])) * quantity,
                                           'kgm': configs.weights[row['diam']], 'type': row['bar_type']}
                if disable_weight:
                    diams[row['diam']]['weight'] = ''
                    diams[row['diam']]['kgm'] = ''
            # Special summary data
            if row['shape'] not in ["905"]:
                if 'חיתוך' not in special_sum.keys():
                    special_sum['חיתוך'] = {'qnt': 0, 'weight': 0}
                special_sum['חיתוך']['qnt'] += quantity
                if not disable_weight:
                    special_sum['חיתוך']['weight'] += row['weight']
            if row['shape'] not in ["1", "905"]:
                if 'כיפוף' not in special_sum.keys():
                    special_sum['כיפוף'] = {'qnt': 0, 'weight': 0}
                special_sum['כיפוף']['qnt'] += quantity
                if not disable_weight:
                    special_sum['כיפוף']['weight'] += row['weight']
            if row['shape'] in ['332']:
                if 'ספירלים' not in special_sum.keys():
                    special_sum['ספירלים'] = {'qnt': 0, 'weight': 0}
                special_sum['ספירלים']['qnt'] += quantity
                if not disable_weight:
                    special_sum['ספירלים']['weight'] += row['weight']
            if row['shape'] in ['55']:
                if 'מדרגה' not in special_sum.keys():
                    special_sum['מדרגה'] = {'qnt': 0, 'weight': 0}
                special_sum['מדרגה']['qnt'] += quantity
                if not disable_weight:
                    special_sum['ספירלים']['weight'] += row['weight']
            if row['shape'] in ['200', '201', '202', '203', '204', '205', '206']:
                if 'חישוק מיוחד' not in special_sum.keys():
                    special_sum['חישוק מיוחד'] = {'qnt': 0, 'weight': 0}
                special_sum['חישוק מיוחד']['qnt'] += quantity
                if not disable_weight:
                    special_sum['חישוק מיוחד']['weight'] += row['weight']
            elif row['shape'] in ['49', '59']:
                if 'ספסלים' not in special_sum.keys():
                    special_sum['ספסלים'] = {'qnt': 0, 'weight': 0}
                special_sum['ספסלים']['qnt'] += quantity
                if not disable_weight:
                    special_sum['ספסלים']['weight'] += row['weight']
            elif ((len(row['shape_data']) > 2) and (int(row['weight']) / int(row['quantity']) <= 2) and costumer_id not in ['143']) \
                    or row['shape'] in configs.circle:
                if 'חישוק' not in special_sum.keys():
                    special_sum['חישוק'] = {'qnt': 0, 'weight': 0}
                special_sum['חישוק']['qnt'] += quantity
                if not disable_weight:
                    special_sum['חישוק']['weight'] += row['weight']
            if int(row['length']) > 1600:
                if 'ברזל_ארוך' not in special_sum.keys():
                    special_sum['ברזל_ארוך'] = {'qnt': 0, 'weight': 0}
                special_sum['ברזל_ארוך']['qnt'] += quantity
                if not disable_weight:
                    special_sum['ברזל_ארוך']['weight'] += row['weight']
            if float(row['diam']) >= 28:
                if 'תוספת_ברזל_28_ממ_ומעלה' not in special_sum.keys():
                    special_sum['תוספת_ברזל_28_ממ_ומעלה'] = {'qnt': 0, 'weight': 0}
                special_sum['תוספת_ברזל_28_ממ_ומעלה']['qnt'] += quantity
                if not disable_weight:
                    special_sum['תוספת_ברזל_28_ממ_ומעלה']['weight'] += row['weight']
            if row['bar_type'] == 'חלק':
                if int(row['diam']) <= 12:
                    if 'תוספת_ברזל_עגול_עד_12_ממ' not in special_sum.keys():
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_עגול_עד_12_ממ']['qnt'] += quantity
                    if not disable_weight:
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ']['weight'] += row['weight']
                elif int(row['diam']) >= 14:
                    if 'תוספת_ברזל_עגול_מעל_14_ממ' not in special_sum.keys():
                        special_sum['תוספת_ברזל_עגול_מעל_14_ממ'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['qnt'] += quantity
                    if not disable_weight:
                        special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['weight'] += row['weight']
        li = list(diams.keys())
        sort_keys = list(map(float, li))
        sort_keys.sort()

        temp = {}
        for key in sort_keys:
            temp[str(key).replace('.0', '')] = diams[str(key).replace('.0', '')]
        diams = temp
        return {'diams': diams, 'work': special_sum}
