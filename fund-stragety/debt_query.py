
import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import json
import os

# 040026 基金基本信息
fund_code = "040026"
fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)

print("--- 基金基本信息 ---")
print(fund_info_df)

 

# 获取历史净值 (包含净值日期、单位净值、累计净值、日增长率等)
fund_history_df = ak.fund_open_fund_info_em(symbol="040026", indicator="累计净值走势")

print("--- 历史净值数据 (前5行) ---")
print(fund_history_df.head())


# 1. 设置基金代码
fund_code = "040026"

# 2. 调用接口获取“单位净值走势”
# indicator 可选： "单位净值走势" 或 "累计净值走势"
fund_history_df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

# 3. 查看数据结构
print("数据概览：")
print(fund_history_df.head())

# 4. 简单的数据处理（可选）
# 将日期列转换为日期对象，方便后续绘图或筛选
fund_history_df['净值日期'] = pd.to_datetime(fund_history_df['净值日期'])
fund_history_df.set_index('净值日期', inplace=True)

# 5. 筛选最近一个月的数据
recent_month = fund_history_df.tail(30)
print("\n最近 30 个交易日净值：")
print(recent_month[['单位净值', '日增长率']])



# 解决绘图中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

# 绘制单位净值曲线
fund_history_df['单位净值'].plot(figsize=(12, 6), title=f"基金 {fund_code} 历史净值走势")
plt.xlabel("日期")
plt.ylabel("净值")
plt.grid(True)
plt.show()


# 1. 获取基金历史数据
fund_code = "040026"
df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")

# 2. 数据预处理
# 将日期列转换为字符串（JSON 不原生支持 Timestamp 对象）
df['净值日期'] = df['净值日期'].astype(str)

# 3. 保存为本地 JSON 文件
# orient='records' 会生成 [{"列1": 值1, "列2": 值2}, ...] 的列表格式，最适合程序处理

# 确保data目录存在
data_dir = "data"
if not os.path.exists(data_dir):
    os.makedirs(data_dir)
    print(f"已创建目录: {data_dir}")

file_path = f"{data_dir}/fund_{fund_code}_history.json"
df.to_json(file_path, orient='records', force_ascii=False, indent=4)

print(f"数据已成功保存至: {file_path}")