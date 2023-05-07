import pages
import os
import configs
import math
from pathlib import Path
import time


class Images:
    @staticmethod
    def gen_pdf417(data):
        import pdf417
        import os
        data = Images.format_qr_data(data)
        _data = pdf417.encode(data)
        img = pdf417.render_image(_data)
        name = 'static\\img\\pdf417_' + pages.ts(mode='file_name') + '.png'
        while os.path.exists(name):
            name = 'static\\img\\pdf417_' + pages.ts(mode='file_name') + '.png'
        img.save(name)
        return name

    @staticmethod
    def format_qr_data(data):
        # todo: complete
        formated = 'BF2D@Hj @r' + data['order_id'] + '_' + data['job_id']
        # return "BF2D@Hj @r22071206@i@p1@l4000@n200@e710@d12@g@\nGl4000@w0@\nC68@x".encode('utf-8')
        return formated

    @staticmethod
    def create_shape_plot(shape, data):
        import os
        from PIL import Image, ImageDraw, ImageFont
        font_size = 20
        positions = configs.shapes[shape]['positions']
        static_dir = os.path.dirname(__file__)+'\\static\\'
        img_dir = static_dir + 'images\\shapes\\' + str(shape) + '.png'
        if os.path.exists(img_dir):
            img = Image.open(img_dir)
        else:
            img = Image.open(static_dir + 'images\\shapes\\0.png')
        draw = ImageDraw.Draw(img)
        for index in range(len(data)):
            positions[index][0] -= (len(str(data[index])) - 1) * 3
            text_box_pos = [positions[index][0], positions[index][1] - 2]
            bbox = draw.textbbox(text_box_pos, str(data[index]), font=ImageFont.truetype("segoeuib.ttf", font_size + 2))
            draw.rectangle(bbox, fill="white")
            draw.text(positions[index], str(data[index]), font=ImageFont.truetype("segoeui.ttf", font_size), fill="black")
        file_out = configs.net_print_dir + "Picture\\" + pages.ts(mode="file_name") + ".bmp"
        img.save(file_out)
        return file_out

    @staticmethod
    def decode_qr(qr):
        # todo: make generic for farther uses
        code = qr.split('@')
        if code:
            for item in code:
                if item:
                    if item[0] == 'r':
                        temp = item.split('_')
                        order_id = temp[0][1:]
                        job_id = temp[1]
                        return order_id, job_id
        return "", ""


class Bartender:
    @staticmethod
    def net_print(order_id, printer, print_type):
        # Format data
        rows, info, aditional = pages.get_order_data(order_id, reverse=False)
        bt_format = configs.bartender_formats[info['type']][print_type]
        print_data = []
        if 'rebar' in info['type'] and print_type == 'page':
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
                        print("break ", row_n + indx, " > ", len(rows) - 1)
                        break
                    n = table_rows * row_n + indx
                    i = table_cells * indx
                    row = rows[n]
                    template_row["tb" + str(1 + i)] = row['job_id']
                    template_row["tb" + str(2 + i)] = row['mkt']
                    template_row["tb" + str(4 + i)] = row['description']
                    template_row["tb" + str(5 + i)] = row['quantity']
                    if rows[n]['mkt'] != "2005020000":
                        template_row["tb" + str(3 + i)] = "רשת סטנדרט"
                        template_row["tb" + str(6 + i)] = float(configs.rebar_catalog[row['mkt']]['unit_weight'])
                    else:
                        # template_row["tb" + str(3 + i)] = "רשת מיוחדת לפי תוכנית כוורת מרותכת דקה"
                        template_row["tb" + str(3 + i)] = "מיוחדת לפי תוכנית כוורת מרותכת דקה"
                        if int(row['diam_x']) >= 14 or int(row['diam_y']) >= 14:
                            template_row["tb" + str(3 + i)] = template_row["tb" + str(3 + i)].replace('דקה', 'עבה')
                        template_row["tb" + str(6 + i)] = int(row['weight'] / int(row['quantity']))
                    template_row["tb" + str(7 + i)] = row['weight']
                    total_weight += row['weight']
                print_data.append(template_row.copy())
            print_data.append({'temp_select': 3, 'tb1': total_weight})
        else:
            for item in rows:
                if item['job_id'] == "0":
                    break
                line = {}
                for obj in item:
                    line[obj] = item[obj]
                for obj in info:
                    line[obj] = info[obj]
                if 'shape_data' in line:
                    line['img_dir'] = Path(Images.create_shape_plot(line['shape'], line['shape_data'])).stem
                line['barcode_data'] = Images.format_qr_data(line)
                print_data.append(line)
        Bartender.bt_create_print_file(printer, bt_format[0], print_data)
        # Print additional summary info
        if len(bt_format) > 1:
            summary_data = Bartender.gen_summary_data(rows, info)
            Bartender.bt_create_print_file(printer, bt_format[1], summary_data)

    @staticmethod
    def gen_summary_data(rows, info):
        info['temp_select'] = 1
        summary_data = []
        if 'rebar' in info['type']:
            for row in rows:
                if row['job_id'] == "0":
                    break
                line = {}
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
                    elif obj == 'pitch':
                        line['x_pitch'] = row[obj].split('X')[0]
                        line['y_pitch'] = row[obj].split('X')[0]
                    elif '_pitch' in obj:
                        line[obj] = ""
                        if len(row[obj]) > 1:
                            for pit in row[obj]:
                                line[obj] += "(" + pit + ")"
                        else:
                            line[obj] += row[obj][0]
                    else:
                        line[obj] = row[obj]
                for obj in info:
                    line[obj] = info[obj]
                line['barcode_data'] = Images.format_qr_data(line)
                summary_data.append(line)
        else:
            table_data = {}
            special_sum = {}
            summary_data.append(info)
            for row in rows:
                if 'bar_type' not in row:
                    row['bar_type'] = "מצולע"
                # Summary data
                quantity = int(row['quantity'])
                if row['diam'] in table_data.keys():
                    table_data[row['diam']]['weight'] += row['weight']
                    table_data[row['diam']]['length'] += int(row['length']) * quantity
                else:
                    table_data[row['diam']] = {'weight': row['weight'], 'length': int(row['length']) * quantity,
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
                if row['shape'] in []:
                    if 'חישוק' not in special_sum.keys():
                        special_sum['חישוק'] = {'qnt': 0, 'weight': 0}
                    special_sum['חישוק']['qnt'] += quantity
                    special_sum['חישוק']['weight'] += row['weight']
                if row['shape'] in []:
                    if 'ספירלים' not in special_sum.keys():
                        special_sum['ספירלים'] = {'qnt': 0, 'weight': 0}
                    special_sum['ספירלים']['qnt'] += quantity
                    special_sum['ספירלים']['weight'] += row['weight']
                if row['shape'] in []:
                    if 'ספסלים' not in special_sum.keys():
                        special_sum['ספסלים'] = {'qnt': 0, 'weight': 0}
                    special_sum['ספסלים']['qnt'] += quantity
                    special_sum['ספסלים']['weight'] += row['weight']
                # todo: Config!!!
                x_length = 2000
                if int(row['length']) > x_length:
                    if 'ברזל_ארוך' not in special_sum.keys():
                        special_sum['ברזל_ארוך'] = {'qnt': 0, 'weight': 0}
                    special_sum['ברזל_ארוך']['qnt'] += quantity
                    special_sum['ברזל_ארוך']['weight'] += row['weight']
                if float(row['diam']) >= 28:
                    if 'תוספת_ברזל_28_ממ_ומעלה' not in special_sum.keys():
                        special_sum['תוספת_ברזל_28_ממ_ומעלה'] = {'qnt': 0, 'weight': 0}
                    special_sum['תוספת_ברזל_28_ממ_ומעלה']['qnt'] += quantity
                    special_sum['תוספת_ברזל_28_ממ_ומעלה']['weight'] += row['weight']
            # Bartender Table filler
            # Summary
            table_cells = 5
            table_rows = 3
            table_selector = 2
            for row in range(math.ceil(len(table_data.keys()) / table_rows)):
                template_row = {'temp_select': table_selector}
                for indx in range(table_rows):
                    if table_rows * row + indx >= len(table_data.keys()):
                        print("break ", row + indx, " > ", len(table_data.keys()) - 1)
                        break
                    diam = list(table_data.keys())[table_rows * row + indx]
                    template_row["tb" + str(1 + table_cells * indx)] = table_data[diam]['type']
                    template_row["tb" + str(2 + table_cells * indx)] = diam
                    template_row["tb" + str(3 + table_cells * indx)] = table_data[diam]['length']
                    template_row["tb" + str(4 + table_cells * indx)] = table_data[diam]['weight_per_M']
                    template_row["tb" + str(5 + table_cells * indx)] = int(table_data[diam]['weight'])
                summary_data.append(template_row.copy())
            # Bartender Table filler
            # Special summary
            table_selector = 3
            table_cells = 3
            table_rows = 3
            spec_sum_lines = math.ceil(len(special_sum) / table_rows)
            if spec_sum_lines:
                template_row = {'temp_select': table_selector}
                summary_data.append(template_row.copy())
                table_selector = 4
                for row in range(spec_sum_lines):
                    template_row = {'temp_select': table_selector}
                    for indx in range(table_rows):
                        if table_rows * row + indx >= len(special_sum.keys()):
                            print("break ", row + indx, " > ", len(special_sum) - 1)
                            break
                        description = list(special_sum.keys())[table_rows * row + indx]
                        template_row["tb" + str(1 + table_cells * indx)] = description.replace("_", " ")
                        template_row["tb" + str(2 + table_cells * indx)] = special_sum[description]['qnt']
                        template_row["tb" + str(3 + table_cells * indx)] = int(special_sum[description]['weight'])
                    summary_data.append(template_row.copy())
        return summary_data

    @staticmethod
    def bt_create_print_file(printer, btw_file, print_data):
        # Bar tender btw
        header = '%BTW% /AF=H:\\NetCode\\margolisys\\' + btw_file + '.btw /D="%Trigger File Name%" /PRN=' \
                 + printer + ' /R=3 /P /DD\n%END%\n'
        file_dir = configs.net_print_dir + print_data[0]['order_id'] + "_" + pages.ts(mode="file_name") + ".txt"
        # ---------todo: for testing------
        # file_dir = file_dir.replace('.txt', '.tmp')
        testing = False
        if testing:
            file_dir = "H:\\NetCode\\margolisys\\1.txt"
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
