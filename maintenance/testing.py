import math
import sys
from datetime import datetime

import os
import piles
import reports

sys.path.insert(1, 'C:\\Server')
import configs

mongo = configs.mongo
# all_orders = list(mongo.read_collection_list('orders', {'info.costumer_id': {'$ne': '58'}, 'info.type':'rebar_special','info.status': {'$in':['NEW','Processed','Production','Inproduction']}}))
all_orders = list(mongo.read_collection_list('orders', {'info.type': {'$ne': 'integration'}}))
# order = mongo.read_collection_one('orders', {'order_id': '4304'})


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
from PIL import Image, ImageDraw,ImageFont
def create_shape_plot(shape, text=[], enable_text_plot=True, html=False):
    size = (200, 60)
    font_size = 16
    font_dir = os.getcwd()+'\\fonts\\upheavtt.ttf'
    font_dir = 'c:\\server\\fonts\\upheavtt.ttf'
    if shape.isdigit():
        _positions = []#configs.shapes[shape]['draw_positions']
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
        elif shape in ['000']:
            draw.arc([(15,30),(185,50)], 170, 360, fill='black', width=3)
            text.append('')
            text[0] = 'L = 1'
            text[1] = 'R = 2'
            # text[2] = ''
            positions = [(15,10),(100,10),(185,10),(50,90)]
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
    im.save('c:\\server\\static\\images\\shapes\\340.png')
    # if html:
    #     file_name = "static\\img\\" + functions.ts(mode="file_name") + ".png"
    #     im.save('C:\\Server\\'+file_name)
    # else:
    #     file_name = configs.net_print_dir + "Picture\\" + functions.ts(mode="file_name") + ".png"
    #     im.save(file_name)
    # return file_name
def calc_hypotenuse(length, radius):
    length = int(length)
    radius = int(radius)
    ang = 180*length/(math.pi*radius)
    hyp = radius*math.sin(math.radians(ang))/math.sin(math.radians((180-ang)/2))
    return int(hyp)


create_shape_plot('000', ['', ''])
