import pages
import db_handler
import pandas as pd
mongo = db_handler.DBHandle()

order_data, page_data = pages.edit_order_data("1", "1")
print(order_data)
print("\n", page_data)
