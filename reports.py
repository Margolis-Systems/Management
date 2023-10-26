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
            # print(data)
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
        # if main.session['username'] == 'baruch':
        #     print(formatted)
        return formatted

    @staticmethod
    def create_shape_plot(shape, text=[], enable_text_plot=True):
        size = (200, 60)
        font_size = 16
        font_dir = os.getcwd()+'\\fonts\\upheavtt.ttf'
        if shape.isdigit():
            _positions = configs.shapes[shape]['draw_positions']
            im = Image.new('RGB', size, 'white')
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
                    # elif item[0] == 'g':
                    #     print("Shape_data")
            return decode
        return {}


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
                        # print(print("break ", row_n + indx, " > ", len(rows) - 1)
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
                        if float(row['diam_x']) >= 14 or float(row['diam_y']) >= 14:
                            template_row["tb" + str(3 + i)] = template_row["tb" + str(3 + i)].replace('דקה', 'עבה')
                        if disable_weight:
                            template_row["tb" + str(6 + i)] = '---'
                        else:
                            template_row["tb" + str(6 + i)] = round(row['weight'] / int(row['quantity']), 2)
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
                row['weight'] = round(row['weight'])
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
                if info['type'] == 'regular':
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
        else:
            table_data = {}
            spec_keys = ['חיתוך', 'כיפוף', 'חישוק', 'ספסלים', 'ספירלים', 'תוספת_ברזל_עגול_עד_12_ממ', 'תוספת_ברזל_עגול_מעל_14_ממ',
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
                    # print(special_sum['חיתוך']['weight'])
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
                        # print("break ", row + indx, " > ", len(table_data.keys()) - 1)
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
                            # print("break ", row + indx, " > ", len(special_sum) - 1)
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

    @staticmethod
    def print_doc(order_id, disable_weight=False, select_jobs='', split=''):
        print(functions.ts())
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
        print(functions.ts())
        output_file = Docs.format_tables_data(file_name, order_type, rows)
        print(functions.ts())
        return output_file

    @staticmethod
    def fill_template(temp_dir, temp_dict):
        # Create timestamp
        temp_dict['print_date'] = datetime.strftime(datetime.now(), '%d%m%Y %H:%M:%S')
        # Merge data
        doc = MailMerge(temp_dir)
        doc.merge(**temp_dict)
        file_name = configs.reports_dir+'reports_temp\\{}_{}.docx'\
            .format(main.session['order_id'], functions.ts('file_name'))
        doc.write(file_name)
        return file_name

    @staticmethod
    def format_tables_data(file_name, order_type, rows):
        dic = ['order_id', 'job_id', 'shape', 'length']
        lines = []
        import pythoncom

        # for t in configs.print_dicts:
        #     if t in order_type:
        #         dic = configs.print_dicts[t]
        for r in rows:
            new_line = {}
            for i in dic:
                if i in r:
                    new_line[i] = r[i]
            lines.append(new_line)
        doc = docx.Document(file_name)
        # align = WD_ALIGN_PARAGRAPH.RIGHT
        # if page_break:
        #     doc.add_page_break()
        #     p = doc.add_paragraph('Report number: XXXXXX')
        #     p.alignment = align
        # # Add header above table
        # if table_header:
        #     p = doc.add_paragraph()
        #     p.add_run(table_header).underline = True
        #     p.alignment = align
        # Table params
        table = doc.add_table(len(lines), len(lines[0]))
        # if conf.rtl:
        #     table.direction = WD_TABLE_DIRECTION.RTL
        table.style = 'Table Grid'
        table.allow_autofit = True
        # Add data to table
        for row in range(len(lines)):  # Table data
            # for cell in range(len(lines[0])):
            #     keys = list(lines[0].keys())
            #     table.cell(row, cell).text = lines[row][keys[cell]]
            table.cell(row, 0).text = lines[row]['order_id']
            table.cell(row, 1).text = lines[row]['job_id']
            table.cell(row, 2).text = lines[row]['shape']
            table.cell(row, 3).text = lines[row]['length']
            print(functions.ts())
        doc.save(file_name)
        output_file = configs.reports_dir+'report_output\\'+os.path.basename(file_name).replace('docx', 'pdf')
        print(functions.ts())
        convert(file_name, output_file, pythoncom.CoInitialize())
        return output_file
    # def convert_
