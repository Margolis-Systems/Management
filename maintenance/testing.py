import sys

import orders

sys.path.insert(1, 'C:\\Server')
import configs


mongo = configs.mongo
orders.update_order_status('Production', '1382', force=True)
