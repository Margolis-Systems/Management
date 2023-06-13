import main
import functions


def save_dl_data():
    dl_data = dict(main.request.values)
    dl_data['timestamp'] = functions.ts()
    main.mongo.insert_collection_one('data_logger', dl_data, 'PlantStatistics')
