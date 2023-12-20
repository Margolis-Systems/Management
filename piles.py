import math
import configs


def calc_weight(data_dict):
    weight = {'spiral': 0}
    total_length = 0
    for k in data_dict:
        if 'spiral' in k and data_dict[k] != '0' and 'diam' not in k:
            total_length += int(data_dict[k])
            if data_dict[k.replace('spiral', 'pitch')] != '0':
                weight['spiral'] += math.sqrt(math.pow(float(data_dict[k.replace('spiral', 'pitch')]),2)+math.pow(math.pi*float(data_dict['pile_diam']),2))*\
                                    float(data_dict[k])/float(data_dict[k.replace('spiral', 'pitch')])*configs.weights[data_dict['spiral_diam']]
    # Length * quantity * KG/M
    weight['bars'] = total_length * int(data_dict['bars']) * configs.weights[data_dict['bars_diam']]
    weight['rings'] = (int(data_dict['pile_diam'])/100 * 3.14 + 0.2) * int(data_dict['rings']) * configs.weights[data_dict['rings_diam']]
    weight['pipes'] = 0
    weight['total'] = weight['spiral'] + weight['bars'] + weight['rings'] + weight['pipes']
    return weight, total_length
