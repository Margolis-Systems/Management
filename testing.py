# import configs
# # Mesh
# mongo = configs.mongo
# rebar_cat = mongo.read_collection_one('data_lists', {'name': 'rebar_catalog'})
# new_data = {}
# for item in rebar_cat['data']:
#     # Catalog item
#     obj = rebar_cat['data'][item]
#     new_obj = {}
#     # Parameter in item
#     for new_item in obj:
#         if new_item not in ['diam', 'pitch']:
#             new_obj[new_item] = obj[new_item]
#         elif new_item == 'diam':
#             new_obj[new_item+'_x'] = obj[new_item]
#             new_obj[new_item+'_y'] = obj[new_item]
#         elif new_item == 'pitch':
#             new_obj['x_'+new_item] = obj[new_item].split('X')[0]
#             new_obj['y_'+new_item] = obj[new_item].split('X')[0]
#             print(obj[new_item])
#             if obj[new_item] == '10X10':
#                 new_obj['x_bars'] = 60
#                 new_obj['y_bars'] = 25
#             elif obj[new_item] == '20X20':
#                 new_obj['x_bars'] = 40
#                 new_obj['y_bars'] = 17
#             else:
#                 new_obj['x_bars'] = 30
#                 new_obj['y_bars'] = 13
#     new_data[item] = new_obj
# print(new_data)
