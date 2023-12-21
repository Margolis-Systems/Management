import math
import configs


def calc_weight(data_dict):
    weight = {'spiral': 0}
    total_length = 0
    for k in data_dict:
        if 'spiral' in k and data_dict[k] != '0' and 'diam' not in k:
            total_length += int(data_dict[k])
            _p = k.replace('spiral', 'pitch')
            if _p in data_dict:
                weight['spiral'] += math.sqrt(math.pow(float(data_dict[_p]),2)+math.pow(math.pi*float(data_dict['pile_diam']),2))*\
                                    float(data_dict[k])/float(data_dict[_p])/100*configs.weights[data_dict['spiral_diam']]
    # Length * quantity * KG/M
    weight['bars'] = total_length * int(data_dict['bars']) * configs.weights[data_dict['bars_diam']]/100
    weight['rings'] = (int(data_dict['pile_diam'])/100 * 3.14 + 0.2) * int(data_dict['rings']) * configs.weights[data_dict['rings_diam']]
    for k in weight:
        if '3%' in data_dict or True:
            weight[k] *= 1.03
        weight[k] = round(weight[k]*int(data_dict['quantity']),2)
    weight['pipes'] = 0.0
    weight['pile'] = weight['spiral'] + weight['bars'] + weight['rings']
    weight['total'] = weight['pile'] + weight['pipes']
    return weight, total_length
