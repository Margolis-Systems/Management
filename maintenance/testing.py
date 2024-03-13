import sys
from datetime import datetime

import os
import piles
import reports

sys.path.insert(1, 'C:\\Server')
import configs

mongo = configs.mongo
# all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'},'info.costumer_name':{'$regex':'דניה סיבוס'},'info.costumer_site':{'$regex':'אומאמי'}}))
all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'}}))
order = mongo.read_collection_one('orders', {'order_id': '4304'})

def find_not_updated():
    hist = []
    for order in all_orders:
        cur_status = order['info']['status']
        if cur_status in ['Delivered']:
            for r in order['rows']:
                if r['status'] not in ['Delivered', 'Finished']:
                    if order['order_id'] not in hist and int(order['order_id']) > 679:
                        hist.append(order['order_id'])
                    print(order['order_id'], r['job_id'])
                    print(cur_status, r['status'], '\n')
    print(hist)
    print(len(hist))


def fix_status(orders_list=None):
    if orders_list is None:
        orders_list = all_orders
    for order in orders_list:
        flag = False
        for r in order['rows']:
            if 'order_status_' in r['status']:
                print(order['order_id'], r['job_id'], r['status'].split('_')[-1], r['status'])
                r['status'] = r['status'].split('_')[-1]
                flag = True
        if flag:
            mongo.update_one('orders', {'order_id': order['order_id']}, order, '$set')


def validate_log():
    for order in all_orders:
        logg = list(mongo.read_collection_list('logs', {'title': 'order_status_change', 'operation.order_id':order['order_id']}))
        if logg:
            if logg[-1]['operation']['status'] != order['info']['status']:
                print(order['order_id'],order['info']['status'],logg[-1]['operation']['status'])


def csv_for_yosi_azulai():
    import csv
    data = []
    total = 0
    for order in all_orders:
        for r in order['rows']:
            if r['diam'] == '36':
                line = [order['order_id'],r['job_id'],r['diam'],r['length'],r['weight']]
                total += int(r['', '', '', 'TOTAL WEIGHT:', 'weight'])
                data.append(line)

    data.append([total])
    with open('c:\\Server\\1.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

adata = [
    {
        "order_id": "4658",
        "job_id": "1",
        "status": "NEW",
        "date_created": "2024-03-13 07:52:05",
        "x_length": [
            "240"
        ],
        "x_pitch": [
            "15"
        ],
        "y_length": [
            "390"
        ],
        "y_pitch": [
            "15"
        ],
        "trim_x_start": "5",
        "trim_x_end": "5",
        "trim_y_start": "5",
        "trim_y_end": "5.0",
        "mkt": "2005020000",
        "quantity": "20",
        "diam_x": "8",
        "diam_y": "8",
        "length": "400",
        "width": "250",
        "x_bars": "27",
        "y_bars": "17",
        "x_weight": 26.86,
        "y_weight": 27.06,
        "description": "H250X27X8WBX(15) V400X17X8WBX(15)",
        "unit_weight": 53.92,
        "weight": 1078.4
    }]

import functions
from PIL import Image, ImageDraw, ImageFont


def create_mesh_plot(data):
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
    im.show()
    # im.save(configs.net_print_dir + "Picture\\" + file_name)
    # return file_name


# for i in adata:
create_mesh_plot(adata[0])
