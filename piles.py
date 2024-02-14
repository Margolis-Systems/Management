import math
import configs

# {pipe diam: {pipe thick: 'weight per M' } }
# pipes_wt_m = {'2': {'1.5': 2.18, '2': 2.88, '2.2': 3.15, '2.65': 3.76, '2.9': 4.06, '3.25': 4.54, '3.65': 5.1, '4': 5.55},
#               '2.5': {'1.5': 2.76, '2': 3.65, '2.2': 4.01, '2.65': 4.8, '2.9': 5.24, '3.25': 5.92, '3.65': 6.52}}
pipes_wt_m = {'2': 2.5,
              '2.5': 3.25}


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
    if 'bars_len' not in data_dict:
        data_dict['bars_len'] = total_length
    weight['bars'] = int(data_dict['bars_len']) * int(data_dict['bars']) * configs.weights[data_dict['bars_diam']]/100
    if 'bars_1' in data_dict:
        if 'bars_len_1' not in data_dict:
            data_dict['bars_len_1'] = total_length
        weight['bars'] += int(data_dict['bars_len_1']) * int(data_dict['bars_1']) * configs.weights[data_dict['bars_diam_1']]/100
    weight['rings'] = (int(data_dict['pile_diam'])/100 * 3.14 + 0.2) * int(data_dict['rings']) * configs.weights[data_dict['rings_diam']]
    for k in weight:
        if '3%' in data_dict or True:
            weight[k] *= 1.03
        weight[k] = round(weight[k]*int(data_dict['quantity']),2)
    weight['pipes'] = 0
    if 'pipe_diam' in data_dict and 'pipe_thick' in data_dict:
        if data_dict['pipe_diam'] in pipes_wt_m:
            # if data_dict['pipe_thick'] in pipes_wt_m[data_dict['pipe_diam']]:
            #     # print(data_dict)
            #     weight['pipes'] = round(int(data_dict['pipe_len']) * int(data_dict['pipes']) * int(data_dict['quantity'])
            #                             * pipes_wt_m[data_dict['pipe_diam']][data_dict['pipe_thick']]/100)
            weight['pipes'] = round(int(data_dict['pipe_len']) * int(data_dict['pipes']) * int(data_dict['quantity'])
                                    * pipes_wt_m[data_dict['pipe_diam']]/100)

    weight['pile'] = weight['spiral'] + weight['bars'] + weight['rings']
    weight['total'] = weight['pile'] + weight['pipes']
    # print('wt', weight)
    return weight, total_length
