import pages


class Images:
    @staticmethod
    def gen_qr(data):
        import qrcode
        qr = qrcode.QRCode(
            version=1,
            box_size=20,
            border=5)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        name = 'qrcode001.png'
        img.save('static\\img\\qr_'+name)
        return name

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
        return formated.encode('utf-8')

    @staticmethod
    def create_shape_plot(shape, data):
        import os
        from PIL import Image, ImageDraw, ImageFont
        from pages import shapes
        positions = shapes[shape]['positions']
        static_dir = os.path.dirname(__file__)+'\\static\\'
        img_dir = static_dir + 'images\\shapes\\' + str(shape) + '.png'
        if os.path.exists(img_dir):
            img = Image.open(img_dir)
        else:
            img = Image.open(static_dir + 'images\\shapes\\0.png')
        draw = ImageDraw.Draw(img)
        for index in range(len(data)):
            bbox = draw.textbbox(positions[index], data[str(index + 1)], font=ImageFont.truetype("segoeui.ttf", 14))
            draw.rectangle(bbox, fill="white")
            draw.text(positions[index], data[str(index + 1)], font=ImageFont.truetype("segoeui.ttf", 14), fill="black")
        file_out = static_dir + 'img\\temp_'+str(shape)+'.png'
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


class Printers:
    @staticmethod
    def word_print(filename=""):
        import os
        word_full_path = "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE"
        printer_name = "HP8F170F (HP DeskJet 3700 series)"
        os.system('RUNDLL32 PRINTUI.DLL,PrintUIEntry /y /n "'+printer_name+'"&"'+word_full_path+'" /q /n "'+filename +
                  '" /mFilePrintDefault /mFileCloseOrExit')


class Reports:
    @staticmethod
    def generate_order_report(order_id, convert_to_pdf=False):
        from docx2pdf import convert

        template_dir = "orders_template.docx"
        rows, info = pages.get_order_data(order_id, reverse=False)
        # File header, configured fields in word template
        if not rows:
            return None
        template_dir = Reports.fill_word_header(info, template_dir)
        # Prepare data fro table
        table_data = []
        dimensions = []
        headers = []
        if info['type'] == "regular":
            # todo: complete
            table_data = []
            dimensions = []
            headers = []
        elif "rebar" in info['type']:
            total_weight = 0
            for row in rows:
                addon = ""
                if row['מקט'] in pages.rebar_catalog.keys():
                    addon += "\n:משקל יחידה\n" + pages.rebar_catalog[row['מקט']]['משקל_יח']
                qr_code = Images.gen_pdf417(row)
                table_data.append([row['שורה'], row['מקט'], row['תיאור'], qr_code,
                                   row['כמות'] + addon,
                                   row['משקל']])
                total_weight += int(row['משקל'])
            table_data.append(["", "", "", "", "משקל כולל", total_weight])
            headers = ['שורה', 'מקט', 'תיאור', 'ברקוד', 'כמות', 'משקל']
            dimensions = [len(rows) + 1, 1, len(headers)]

        Reports.create_table(template_dir, dimensions, table_data, headers)
        # reports.generate_summary(self, template_dir, rows)

        # if convert_to_pdf:
        #     convert(template_dir)
        #     template_dir = template_dir.replace("docx", "pdf")
        return template_dir

    @staticmethod
    def create_table(doc_dir, dimensions, data, headers, col_merge=[], page_break=False):
        tb_reverse = True
        '''
        :param doc_dir: Document dir
        :param dimensions: Array of 3 fields = [ row_count, inner_rows_count, columns_count ]
        :param data: Array of arrays similar to table structure. Contains the text to be added
        :param col_merge: Array of column number to merge all inner rows.
        :param page_break: Boolean, add break or not
        '''
        import docx
        from docx.enum.table import WD_TABLE_DIRECTION

        # Open new report file
        doc = docx.Document(doc_dir)
        # Page break if required
        if page_break:
            doc.add_page_break()
        # Create new table, with some configs
        row_count, inner_rows_count, columns_count = dimensions
        table = doc.add_table(row_count * inner_rows_count + 1, columns_count)
        table.direction = WD_TABLE_DIRECTION.RTL
        table.style = 'Table Grid'
        table.allow_autofit = False
        # Add data to table
        for tb_row in range(row_count + 1):
            if tb_row == 0:
                for tb_column in range(columns_count):
                    if tb_reverse:
                        tb_column_rv = columns_count - tb_column - 1
                    else:
                        tb_column_rv = columns_count
                    table.cell(tb_row, tb_column_rv).text = headers[tb_column]
            else:
                for tb_column in range(columns_count):
                    if tb_reverse:
                        tb_column_rv = columns_count - tb_column - 1
                    else:
                        tb_column_rv = columns_count
                    # TODO: fix bug!!!
                    try:
                        temp = str(data[tb_row - 1][tb_column])
                    except:
                        temp = "zsdg"
                    if ".png" in temp:
                        cell = table.rows[(tb_row + 1) * inner_rows_count - 1].cells[tb_column_rv]
                        paragraph = cell.paragraphs[0]
                        run = paragraph.add_run()
                        run.add_picture(str(data[tb_row - 1][tb_column]), width=1800000, height=600000)
                    else:
                        # TODO: fix bug!!!
                        try:
                            table.cell((tb_row + 1) * inner_rows_count - 1, tb_column_rv).text = str(data[tb_row - 1][tb_column])
                        except:
                            print("sfdg")
                    if (tb_row % inner_rows_count + 1) == inner_rows_count and tb_column_rv in col_merge:
                        table.cell(tb_row, tb_column_rv).merge(table.cell(tb_row + 1 - inner_rows_count, tb_column_rv))
        # Save file
        doc.save(doc_dir)
        doc.save(doc_dir)

    @staticmethod
    def fill_word_header(info, template_name="orders_template.docx"):
        from mailmerge import MailMerge
        from datetime import datetime

        # Add print date to info
        info['print_date'] = datetime.strftime(datetime.now(), "%d%m%Y_%H%M%S")
        # Directories config
        template_dir = "reports\\reports_templates\\" + template_name
        template_out_dir = "reports\\report_output\\" + info['order_id'] + "_" + info['print_date'] + ".docx"
        # Merge info to file, configured fields in word template
        document = MailMerge(template_dir)
        document.merge(**info)

        document.write(template_out_dir)
        return template_out_dir

    @staticmethod
    def generate_summary(doc_dir, data, page_break=True):
        summary = {}
        total_weight = 0
        for row in data:
            if row['קוטר'] not in summary.keys():
                summary[row['קוטר']] = {'אורך': float(row['אורך']), 'משקל': float(row['משקל'])}
            else:
                summary[row['קוטר']]['אורך'] += float(row['אורך'])
                summary[row['קוטר']]['משקל'] += float(row['משקל'])
            total_weight += float(row['משקל'])
        # todo: complete
        headers = []
        dimensions = []
        Reports.create_table(doc_dir, dimensions, data, headers, page_break=page_break)
        # table = doc.add_table(len(summary) + 3, 5)
        # table.direction = WD_TABLE_DIRECTION.RTL
        # table.style = 'Table Grid'
        # table.allow_autofit = False
        # key_list = list(summary.keys())
        # table.cell(0,0).text = "סיכום משקל ברזל"
        # table.cell(0,0).merge(table.cell(0, 4))
        # for i in range(1, len(summary)+2):
        #     if i == 1:
        #         table.cell(i,0).text = 'משקל תאורטי בק"ג'
        #         table.cell(i,1).text = 'משקל למטר'
        #         table.cell(i,2).text = 'סה"כ אורך בס"מ'
        #         table.cell(i,3).text = 'קוטר ברזל'
        #         table.cell(i,4).text = 'סוג ברזל'
        #     else:
        #         table.cell(i,0).text = str(summary[key_list[i-2]]['משקל'])
        #         table.cell(i,1).text = str(weight_list[key_list[i-2]])
        #         table.cell(i,2).text = str(summary[key_list[i-2]]['אורך'])
        #         table.cell(i,3).text = str(key_list[i-2])
        # table.cell(len(summary)+2, 0).text = str(total_weight)
        # table.cell(len(summary)+2, 1).merge(table.cell(len(summary)+2, 3))
        # table.cell(len(summary)+2, 4).text = "סיכום משקל ברזל"
        #
