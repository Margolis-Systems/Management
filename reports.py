from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_PARAGRAPH_ALIGNMENT
from docx.oxml import OxmlElement

import main
import orders
import functions
import configs

import math
import os
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
        formatted = 'BF2D@Hj @r' + data['order_id'] + '@i@p' + data['job_id']
        if 'length' in data.keys():
            formatted += '@l' + str(int(float(data['length'])*10))
        if 'quantity' in data.keys():
            formatted += '@n' + str(data['quantity'])
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
    def create_shape_plot(shape, text=[], enable_text_plot=True):
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
        file_name = configs.net_print_dir + "Picture\\" + functions.ts(mode="file_name") + ".png"
        if not text:
            text = list(range(1, len(positions)))
        if shape.isdigit():
            if shape not in ['331', '332']:
                draw.line(positions, fill="black", width=3)
            else:
                draw.ellipse([(5, 5), (55, 55)],outline='black', width=3)
                positions = [(10,30),(20,30),(200,30)]
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
        im.save(file_name)
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
                    elif item[0] == 'e':
                        decode['weight'] = item[1:]
                    elif item[0] == 'd':
                        decode['diam'] = item[1:]
            return decode
        return {}

    @staticmethod
    def create_pile_plot(data, testing=False):
        size = (710, 520)
        font_size = 16
        # font_dir = os.getcwd()+'\\fonts\\upheavtt.ttf'
        font_dir = 'C:\\Windows\\Fonts\\arial.ttf'
        file_name = configs.net_print_dir + "Picture\\" + functions.ts(mode="file_name") + ".png"
        im = Image.new('RGBA', size, 'white')
        draw = ImageDraw.Draw(im)
        spiral = []
        pitch = []
        # bend = 0
        # if 'bend' in data:
        #     # spiral = [data['bend_len']]
        #     bend = int(data['bend_len'])
        #     data['spiral'] = str(int(data['spiral']) - int(data['bend_len']))
        #     # pitch = ['']

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
            draw.line([(675-cfa, 80), (690, 135)], fill="black", width=3)
            draw.line([(675-cfa, 200), (690, 145)], fill="black", width=3)
            # draw.text((655, 130), 'CFA', fill="black", font=ImageFont.truetype(font_dir, font_size))
        # Draw length line
        draw.line([(15, 50), (675, 50)], fill="black", width=3)
        draw.line([(15, 45), (15, 55)], fill="black", width=3)
        pos = 15
        for i in range(len(spiral)):
            break_line = pos+int(int(spiral[i])/int(data['length'])*660)
            if break_line > 675-cfa:
                break_line = 675-cfa
            draw.text((pos+int(int(spiral[i])/int(data['length'])*660/2)-20, 30), spiral[i], fill="black", font=ImageFont.truetype(font_dir, font_size))
            draw.text((pos+int(int(spiral[i])/int(data['length'])*660/2)-20, 60), pitch[i], fill="black", font=ImageFont.truetype(font_dir, font_size))
            draw.line([(break_line, 45), (break_line, 55)], fill="black", width=3)
            if pitch[i]:
                s = pos
                ptch = int(pitch[i][1:])
                while s < break_line-2*ptch:
                    draw.line([(s, 80), (s + ptch, 200)], fill="black", width=3)
                    if s+2*ptch > break_line:
                        draw.line([(s + ptch, 200), (break_line, 80)], fill="black", width=3)
                    else:
                        draw.line([(s + ptch, 200), (s + 2*ptch, 80)], fill="black", width=3)
                    s += 2*ptch
                draw.line([(s, 80), (break_line, 200)], fill="black", width=3)
                draw.line([(pos, 80), (pos, 200)], fill="black", width=3)
            pos = break_line
        if cfa == 0:
            draw.line([(pos, 80), (pos, 200)], fill="black", width=3)
        # Draw pile
        draw.line([(15,80),(675-cfa,80)], fill="black", width=3)
        draw.line([(15,200),(675-cfa,200)], fill="black", width=3)
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
            pipe_decript = u'{} X @{} X {} [{}]'.format(data['pipes'], data['pipe_diam'], data['length'], data['pipe_thick'])
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
        # draw.text((500, 500), 'fff', fill="black", direction='rtl', font=ImageFont.truetype(font_dir, font_size))
        if testing:
            im.show()
        else:
            im.save(file_name)
        return file_name


class Bartender:
    @staticmethod
    def net_print(order_id, printer, print_type, disable_weight=False, select_jobs=[], split=''):
        # Format data
        rows, info = orders.get_order_data(order_id, reverse=False, split=split)
        info['order_split'] = split
        if select_jobs:
            rlen = len(rows)
            for i in range(rlen):
                index = rlen - 1 - i
                if rows[index]['job_id'] not in select_jobs:
                    rows.pop(index)
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
                    if 'bend1' in row or 'bend2' in row or 'bend3' in row:
                        template_row["tb" + str(3 + i)] += ' + כיפוף'
                    if 'חיתוך' in row:
                        template_row["tb" + str(3 + i)] += ' + חיתוך'
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
                if row['element'] and print_type != 'test_page':
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
                    pile_fix = round(float(row['weight']) / int(row['quantity']))
                if 'pack_quantity' in row and 'label' in print_type:
                    pack_rows = []
                    row['quantity'] = int(row['quantity'])
                    row['pack_quantity'] = int(row['pack_quantity'])
                    total_packs = math.ceil(row['quantity']/row['pack_quantity'])
                    pack_index = 1
                    while row['quantity'] > 0:
                        pack_row = row.copy()
                        if row['quantity'] - row['pack_quantity'] >= 0:
                            pack_row['quantity'] = row['pack_quantity']
                            if 'unit_weight' not in pack_row:
                                pack_row['unit_weight'] = pile_fix
                            pack_row['weight'] = round(float(pack_row['unit_weight'])*row['pack_quantity'])
                            pack_row['pack_num'] = '{}/{}'.format(pack_index, total_packs)
                        else:
                            pack_row['pack_num'] = '{}/{}'.format(pack_index, total_packs)
                            pack_row['weight'] = round(float(pack_row['unit_weight'])*row['quantity'])
                        pack_rows.append(pack_row)
                        pack_index += 1
                        row['quantity'] -= row['pack_quantity']
                    _rows.extend(pack_rows)
                    continue
                _rows.append(row)
            rows = _rows.copy()
            index = 0
            for row in rows:
                if row['job_id'] == "0":
                    break
                line = {}
                kora = {'temp_select': 1, 'z15': 0, 'z16': 0, 'img_dir': 'kora', 'order_split': split}
                for obj in row:
                    line[obj] = row[obj]
                for obj in info:
                    line[obj] = info[obj]
                if 'shape_data' in line:
                    line['img_dir'] = Images.create_shape_plot(line['shape'], line['shape_data']).split('\\')[-1].replace('.png', '')
                    if ((len(row['shape_data']) > 2) and (row['weight'] / int(row['quantity']) <= 2) \
                            and row['shape'] not in ['332', '49', '59']) or row['shape'] in configs.circle:
                        line['circle'] = 'כן'
                elif 'shape' in line:
                    line['img_dir'] = Images.create_shape_plot(line['shape'], [line['shape']]).split('\\')[
                        -1].replace('.png', '')
                    line['temp_select'] = 1
                line['barcode_data'] = Images.format_qr_data(line)
                if 'element' in line:
                    if len(line['element']) > 0:
                        if line['element'][0] == 'ק' and line['element'] not in element_buf:# and 'label' in print_type:
                            item_to_copy = ['order_id', 'element', 'costumer_name', 'comment', 'costumer_site']
                            for item in item_to_copy:
                                if item in line:
                                    kora[item] = line[item]
                            for _row in rows:
                                if _row['element'] == line['element']:
                                    kora['z15'] += 1
                                    kora['z16'] += _row['weight']
                            kora['z16'] = int(kora['z16'])
                            kora['weight'] = kora['z16']
                            kora['quantity'] = kora['z15']
                            # todo: barcode DATA
                            kora['barcode_data'] = ''
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
                    elif '_pitch' in obj and not isinstance(row[obj], str) and not isinstance(row[obj], int):
                        line[obj] = ""
                        for pit in row[obj]:
                            line[obj] += "(" + pit + ")"
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
                        line['img_dir'] = Images.create_shape_plot('405', bends).split('\\')[-1].replace('.png', '')
                    elif len(bends) == 3:
                        line['img_dir'] = Images.create_shape_plot('404', bends).split('\\')[-1].replace('.png', '')
                line['barcode_data'] = Images.format_qr_data(line)
                summary_data.append(line)
        elif 'piles' in info['type']:
            summary_data = rows.copy()
            for r in summary_data:
                r.update(info)
                r['barcode_data'] = Images.format_qr_data(r)
                for i in r:
                    if r[i] == '0':
                        r[i] = ''
                r['img_dir'] = Images.create_pile_plot(r)
        else:
            table_data = {}
            spec_keys = ['חיתוך', 'כיפוף', 'חישוק', 'חישוק מיוחד', 'ספסלים', 'ספירלים', 'תוספת_ברזל_עגול_עד_12_ממ', 'תוספת_ברזל_עגול_מעל_14_ממ',
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
                if row['shape'] in ['200']:
                    if 'חישוק מיוחד' not in special_sum.keys():
                        special_sum['חישוק מיוחד'] = {'qnt': 0, 'weight': 0}
                    special_sum['חישוק מיוחד']['qnt'] += quantity
                    special_sum['חישוק מיוחד']['weight'] += row['weight']
                elif row['shape'] in ['49','59']:
                    if 'ספסלים' not in special_sum.keys():
                        special_sum['ספסלים'] = {'qnt': 0, 'weight': 0}
                    special_sum['ספסלים']['qnt'] += quantity
                    special_sum['ספסלים']['weight'] += row['weight']
                elif (len(row['shape_data']) > 2) and (row['weight'] / int(row['quantity']) <= 2) \
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
                    if int(row['diam']) <= 12:
                        if 'תוספת_ברזל_עגול_עד_12_ממ' not in special_sum.keys():
                            special_sum['תוספת_ברזל_עגול_עד_12_ממ'] = {'qnt': 0, 'weight': 0}
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ']['qnt'] += quantity
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ']['weight'] += row['weight']
                    elif int(row['diam']) >= 14:
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
                temp[key] = table_data[str(key).replace('.0','')]
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
        file_dir = configs.net_print_dir + print_data[0]['order_id'] + "_" + functions.ts(mode="file_name") + ".txt"
        # --------- for testing ----------
        if main.session['username'] in ['baruch', 'Baruch']:
            file_dir = file_dir.replace('.txt', '.tmp')
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
        return file_dir


class Docs:
    from docx.enum.table import WD_TABLE_DIRECTION
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.text import WD_PARAGRAPH_ALIGNMENT


    @staticmethod
    def print_doc(order_id, disable_weight=False, select_jobs='', split=''):
        rows, info = orders.get_order_data(order_id, reverse=False, split=split)
        info['order_id'] = order_id
        if select_jobs:
            rlen = len(rows)
            for i in range(rlen):
                index = rlen - 1 - i
                if rows[index]['job_id'] not in select_jobs:
                    rows.pop(index)
        if not rows:
            return ''
        order_type = info['type']
        if order_type != 'regular':
            return 'static\\temp\\pdf_construct.pdf'
        # Delete all weights data
        if disable_weight:
            for r in rows:
                for i in r:
                    if 'weight' in i:
                        r[i] = ''
            for i in info:
                if 'weight' in i:
                    info[i] = ''
        file_name = Docs.fill_template(configs.reports_dir+'reports_templates\\default.docx', info)
        output_file = Docs.format_tables_data(file_name, order_type, rows)
        return output_file

    @staticmethod
    def add_summary(temp_dir, temp_dict):
        print()

    @staticmethod
    def fill_template(temp_dir, temp_dict):
        # Create timestamp
        temp_dict['print_date'] = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
        # Merge data
        doc = MailMerge(temp_dir)
        doc.merge(**temp_dict)
        file_name = configs.reports_dir+'reports_temp\\{}_{}.docx'\
            .format(main.session['order_id'], functions.ts('file_name'))
        doc.write(file_name)
        return file_name

    @staticmethod
    def format_tables_data(file_name, order_type, rows):
        import pythoncom
        doc = docx.Document(file_name)
        Docs.prevent_document_break(doc)
        tb_rows = len(rows)
        tb_cells = 4
        table = doc.add_table(tb_rows, tb_cells)
        table.direction = WD_TABLE_DIRECTION.RTL
        table.style = 'Table Grid'
        table.allow_autofit = True
        # Add data to table
        if order_type == 'regular':
            for row in range(len(rows)):  # Table data
                element = ''
                inner_id = ''
                if 'element' in rows[row]:
                    element = rows[row]['element']
                if 'inner_id' in rows[row]:
                    inner_id = rows[row]['inner_id']
                table.cell(row, 3).text = 'מספר שורה: {}\nאלמנט: {}\nמס.ברזל: {}\nקוטר: {}\nכמות: {}'\
                    .format(rows[row]['job_id'], element, inner_id,
                            rows[row]['diam'], rows[row]['quantity'])
                table.cell(row, 2).text = 'אורך חיתוך: {}\nמשקל ק"ג: {}\nמס.צורה: {}\nחישוק: {}'\
                    .format(rows[row]['length'], rows[row]['weight'], rows[row]['shape'], '')

                img_dir = Images.gen_pdf417(rows[row])
                paragraph = table.cell(row, 1).paragraphs[0]
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                run = paragraph.add_run()
                run.add_picture(img_dir, width=1800000, height=600000)

                img_dir = Images.create_shape_plot(rows[row]['shape'], rows[row]['shape_data'])
                paragraph = table.cell(row, 0).paragraphs[0]
                paragraph.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
                run = paragraph.add_run()
                run.add_picture(img_dir, width=1800000, height=600000)

            summary_data = Docs.gen_summary_data(rows, False)
            doc.add_page_break()
            tb_dictionary = {'weight': 'משקל', 'weight_per_M': 'משקל למטר', 'length': 'סה"כ אורך', 'type': 'סוג ברזל',
                             'qnt': 'כמות', 'description': 'תיאור'}
            for dt in summary_data:
                header = []
                tb_data = []
                # Add header above table
                table_header = 'סיכום משקל ברזל'  # todo: <---
                if table_header:
                    p = doc.add_paragraph()
                    p.add_run(table_header).underline = True
                    p.bold = True
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                for k in dt:
                    temp = {'description': k}
                    header.append(k)
                    order_by = ['type', 'qnt', 'length', 'weight_per_M', 'weight']
                    for o in order_by:
                        if o in dt[k]:
                            temp[o] = dt[k][o]
                            header.append(o)
                    tb_data.append(temp)
                tb_rows = len(tb_data)
                tb_cells = len(tb_data[0])
                table = doc.add_table(tb_rows+1, tb_cells)
                table.direction = WD_TABLE_DIRECTION.RTL
                table.style = 'Table Grid'
                table.allow_autofit = True
                # Add data to table
                row_keys = list(tb_data[0].keys())
                for tbx in range(tb_cells):
                    table.cell(0, tb_cells-tbx-1).text = header[tbx]
                for tbi in range(tb_rows):
                    for tbx in range(tb_cells):
                        table.cell(tbi+1, tb_cells-tbx-1).text = str(tb_data[tbi][row_keys[tbx]])
        # todo: if summary_datav->
        #  page break
        #  table
        doc.save(file_name)
        output_file = configs.reports_dir+'report_output\\'+os.path.basename(file_name).replace('docx', 'pdf')
        convert(file_name, output_file, pythoncom.CoInitialize())
        return output_file

    @staticmethod
    def prevent_document_break(document):
        tags = document.element.xpath('//w:tr')
        rows = len(tags)
        for row in range(0, rows):
            tag = tags[row]  # Specify which <w:r> tag you want
            child = OxmlElement('w:cantSplit')  # Create arbitrary tag
            tag.append(child)  # Append in the new tag

    @staticmethod
    def gen_summary_data(rows, disable_weight):
        table_data = {}
        spec_keys = ['חיתוך', 'כיפוף', 'חישוק', 'ספסלים', 'ספירלים', 'תוספת_ברזל_עגול_עד_12_ממ', 'תוספת_ברזל_עגול_מעל_14_ממ',
               'ברזל_ארוך', 'תוספת_ברזל_28_ממ_ומעלה']
        special_sum = {}
        for i in spec_keys:
            special_sum[i] = {'qnt': 0, 'weight': 0}
        total_weight = 0
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
            elif row['shape'] in ['49','59']:
                if 'ספסלים' not in special_sum.keys():
                    special_sum['ספסלים'] = {'qnt': 0, 'weight': 0}
                special_sum['ספסלים']['qnt'] += quantity
                special_sum['ספסלים']['weight'] += row['weight']
            elif (len(row['shape_data']) > 2) and (row['weight'] / int(row['quantity']) <= 2) \
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
                if int(row['diam']) <= 12:
                    if 'תוספת_ברזל_עגול_עד_12_ממ' not in special_sum.keys():
                        special_sum['תוספת_ברזל_עגול_עד_12_ממ'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_עגול_עד_12_ממ']['qnt'] += quantity
                    special_sum['תוספת_ברזל_עגול_עד_12_ממ']['weight'] += row['weight']
                elif int(row['diam']) >= 14:
                    if 'תוספת_ברזל_עגול_מעל_14_ממ' not in special_sum.keys():
                        special_sum['תוספת_ברזל_עגול_מעל_14_ממ'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['qnt'] += quantity
                    special_sum['תוספת_ברזל_עגול_מעל_14_ממ']['weight'] += row['weight']
            # Reorder diam summary list
            sort_keys = list(map(float, list(table_data.keys())))
            sort_keys.sort()
            temp = {}
            for k in sort_keys:
                key = str(k).replace('.0','')
                temp[key] = table_data[key]
            table_data = temp
            special_sum_keys = list(special_sum.keys())
            for key in special_sum_keys:
                if special_sum[key]['qnt'] == 0:
                    del special_sum[key]
        return table_data, special_sum


if __name__ == '__main__':
    orderr = main.mongo.read_collection_one('orders', {'order_id':'1605'})
    print(Docs.gen_summary_data(orderr['rows'], False))
