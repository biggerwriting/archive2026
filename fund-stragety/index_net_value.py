import baostock as bs
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt

# 1. 获取沪深300 指数数据 (Baostock)
bs.login()
rs = bs.query_history_k_data_plus("sh.000300", "date,close", 
                                  start_date='2023-01-01', end_date='2023-12-31', frequency="d")
data_list = []
while (rs.error_code == '0') and rs.next():
    data_list.append(rs.get_row_data())
bs.logout()

df_index = pd.DataFrame(data_list, columns=['date', 'index_close'])
df_index['date'] = pd.to_datetime(df_index['date'])
df_index['index_close'] = df_index['index_close'].astype(float)

# 2. 获取华泰柏瑞300ETF 净值数据 (AkShare)
fund_code = "510300"
df_fund = ak.fund_etf_hist_sina('sh510300')
df_fund = df_fund[['date', 'close']]
df_fund.columns = ['date', 'fund_nav']
df_fund['date'] = pd.to_datetime(df_fund['date'])
df_fund['fund_nav'] = df_fund['fund_nav'].astype(float)

# 3. 合并数据 (按日期对齐)
# 只保留两个都有数据的日期
df_merged = pd.merge(df_index, df_fund, on='date', how='inner')
df_merged = df_merged.sort_values('date')

# 4. 计算相关系数
correlation = df_merged['index_close'].corr(df_merged['fund_nav'])
print(f"两者相关系数: {correlation:.4f} (越接近1表示越同步)")

# 5. 可视化对比 (双坐标轴)
fig, ax1 = plt.subplots(figsize=(10, 6))

color = 'tab:red'
ax1.set_xlabel('Date')
ax1.set_ylabel('Index Points (000300)', color=color)
ax1.plot(df_merged['date'], df_merged['index_close'], color=color, label='Index 300')
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  # 创建共享x轴的第二个y轴
color = 'tab:blue'
ax2.set_ylabel('ETF NAV (510300)', color=color)
ax2.plot(df_merged['date'], df_merged['fund_nav'], color=color, linestyle='--', label='ETF NAV')
ax2.tick_params(axis='y', labelcolor=color)

plt.title(f'HS300 Index vs ETF NAV (Correlation: {correlation:.4f})')
plt.show()