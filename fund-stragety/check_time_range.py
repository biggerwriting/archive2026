import json
import pandas as pd

print("检查两个基金数据的时间范围...")

# 加载两个文件并检查时间范围
with open('data/fund_040026_history.json', 'r') as f:
    data1 = json.load(f)
df1 = pd.DataFrame(data1)
df1['date'] = pd.to_datetime(df1['净值日期'])
print('040026 时间范围:', df1['date'].min(), 'to', df1['date'].max())
print('040026 数据条数:', len(df1))

with open('data/fund_510300_history.json', 'r') as f:
    data2 = json.load(f)
df2 = pd.DataFrame(data2)
df2['date'] = pd.to_datetime(df2['净值日期'])
print('510300 时间范围:', df2['date'].min(), 'to', df2['date'].max())
print('510300 数据条数:', len(df2))

# 检查是否有交集
common_dates = set(df1['date']) & set(df2['date'])
print(f'重合日期数量: {len(common_dates)}')

if len(common_dates) > 0:
    print('前5个重合日期:', sorted(list(common_dates))[:5])
else:
    print('没有重合日期')
    
    # 寻找最接近的日期
    print('\n尝试寻找最接近的日期...')
    df1_dates = sorted(df1['date'])
    df2_dates = sorted(df2['date'])
    
    # 检查两个数据集最接近的日期
    closest_pair = None
    min_diff = None
    
    for d1 in df1_dates[:10]:  # 只检查前10个日期
        for d2 in df2_dates[:10]:  # 只检查前10个日期
            diff = abs((d1 - d2).days)
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_pair = (d1, d2)
    
    if closest_pair:
        print(f'最接近的日期对: {closest_pair[0]} 和 {closest_pair[1]} (相差 {min_diff} 天)')