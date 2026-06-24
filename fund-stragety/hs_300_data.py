import baostock as bs
import pandas as pd
lg=bs.login()
rs = bs.query_hs300_stocks()
hs300_stocks = []
while(rs.error_code=='0') & rs.next():
    hs300_stocks.append(rs.get_row_data())
    