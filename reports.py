import orders
import functions
import configs
import math


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
            formatted += '@l' + str(data['length'])
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
                formatted += str(data['shape_data'][item])
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
        # print('CheckSum: ', chksm)
        # print(len(formatted))
        # print(formatted)
        return formatted

    @staticmethod
    def create_shape_plot(shape, data):
        import os
        from PIL import Image, ImageDraw, ImageFont
        font_size = 16
        positions = configs.shapes[shape]['positions']
        static_dir = os.path.dirname(__file__)+'\\static\\'
        img_dir = static_dir + 'images\\shapes\\' + str(shape) + '.png'
        if os.path.exists(img_dir):
            img = Image.open(img_dir)
        else:
            img = Image.open(static_dir + 'images\\shapes\\0.png')
        draw = ImageDraw.Draw(img)
        for i in range(len(data)):
            text_box_pos = positions[i][0], positions[i][1] - 2
            bbox = draw.textbbox(text_box_pos, str(data[i]), font=ImageFont.truetype("impact.ttf", font_size+2)) #segoeuib.ttf
            draw.rectangle(bbox, fill="white")
            draw.text(positions[i], str(data[i]), font=ImageFont.truetype("impact.ttf", font_size), fill="black")
        file_out = configs.net_print_dir + "Picture\\" + functions.ts(mode="file_name") + ".bmp"
        img.save(file_out)
        return file_out

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
                    elif item[0] == 'g':
                        print("Shape_data")
            return decode
        return {}


class Bartender:
    @staticmethod
    def net_print(order_id, printer, print_type, disable_weight=False):
        # Format data
        rows, info, additional = orders.get_order_data(order_id, reverse=False)
        bt_format = configs.bartender_formats[info['type']][print_type]
        print_data = []
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
                    line['img_dir'] = Images.create_shape_plot(line['shape'], line['shape_data']).split('\\')[-1].replace('.bmp', '')
                line['barcode_data'] = Images.format_qr_data(line)
                print_data.append(line)
        # TODO: validate!!!
        if disable_weight:
            for print_line in print_data:
                for print_item in print_line:
                    if 'weight' in print_item:
                        print_data[print_line][print_item] = ""
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
        tempfix = btw_file
        # Bar tender btw
        header = '%BTW% /AF=H:\\NetCode\\margolisys\\' + tempfix.replace('scaling_report', 'scaling_report_fix') + '.btw /D="%Trigger File Name%" /PRN=' \
                 + printer + ' /R=3 /P /DD\n%END%\n'
        file_dir = configs.net_print_dir + print_data[0]['order_id'] + "_" + functions.ts(mode="file_name") + ".txt"
        # --------- for testing ----------
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
