import bcrypt
from reports import Bartender as bt
import db_handler
import pandas as pd
mongo = db_handler.DBHandle()

import pages

rows, info = pages.get_order_data("1")
bt.print_label(rows, info)
