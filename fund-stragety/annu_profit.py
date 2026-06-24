import pandas as pd
from datetime import datetime
fund_code = "540010"
# 1. 读取数据
df_read = pd.read_csv(f"data/fund_{fund_code}_akshare.csv")

# 2. 转换日期格式并按日期升序排列（确保最早的日期在前）
df_read['净值日期'] = pd.to_datetime(df_read['净值日期'])
df_read = df_read.sort_values('净值日期')

# 3. 获取起止信息
start_price = df_read['累计净值'].iloc[0]      # 初始净值
end_price = df_read['累计净值'].iloc[-1]        # 最新净值
start_date = df_read['净值日期'].iloc[0]      # 开始日期
end_date = df_read['净值日期'].iloc[-1]        # 结束日期

# 4. 计算持有天数
days = (end_date - start_date).days

# 5. 计算总收益率和年化收益率
total_return = (end_price - start_price) / start_price
annual_return = (1 + total_return) ** (365 / days) - 1

print(f"统计区间: {start_date.date()} 至 {end_date.date()}")
print(f"持有天数: {days} 天")
print(f"区间总收益率: {total_return:.2%}")
print(f"--- 历史年化收益率: {annual_return:.2%}")