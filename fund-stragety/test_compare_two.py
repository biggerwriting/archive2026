import sys
import os
sys.path.append('.')

# 重新复制修复后的compare_two代码到当前文件进行测试
import json
import pandas as pd

def load_data(file_path, name):
    """读取单个文件并返回处理好的DataFrame"""
    print(f"加载 {name}: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"警告: 文件 {file_path} 不存在")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # 检查日期格式并相应处理
    sample_date = df['净值日期'].iloc[0]
    if isinstance(sample_date, (int, float)) and sample_date > 1000000000:
        # 如果是大数字，视为毫秒时间戳
        df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
    else:
        # 否则视为字符串日期格式
        df['date'] = pd.to_datetime(df['净值日期'])
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # 提取关键列并重命名，方便后续合并
    # 检查可用的净值列名
    if '累计净值' in df.columns:
        value_col = '累计净值'
    elif '单位净值' in df.columns:
        value_col = '单位净值'
    else:
        # 如果都没有，显示可用列名并退出
        available_cols = list(df.columns)
        raise ValueError(f"数据文件中没有找到净值列，可用列: {available_cols}")
    
    result = df[['date', value_col]].rename(columns={value_col: 'value'})
    
    print(f"  形状: {result.shape}")
    print(f"  日期范围: {result['date'].min()} 到 {result['date'].max()}")
    
    return result

def process_comparison_data(file1, file2):
    """
    核心逻辑：读取两个文件，按日期取交集，并计算全量回撤
    """
    print("正在处理对比数据...")
    
    # 1. 读取数据
    df1 = load_data(file1, "Fund A")
    df2 = load_data(file2, "Fund B")
    
    if df1 is None or df2 is None:
        print("数据加载失败")
        return None

    # 2. 合并数据 (Inner Join 取交集，确保时间轴完全对齐)
    print("正在进行数据合并...")
    print(f"df1形状: {df1.shape}, df2形状: {df2.shape}")
    
    df_merge = pd.merge(df1, df2, on='date', suffixes=('_A', '_B'), how='inner')
    
    print(f"合并后数据形状: {df_merge.shape}")
    
    if df_merge.empty:
        print("合并后数据为空!")
        print("df1日期样本:", df1['date'].head(5).tolist())
        print("df2日期样本:", df2['date'].head(5).tolist())
        return None

    return df_merge

# 测试
try:
    file_path_1 = 'data/fund_040026_history.json'
    file_path_2 = 'data/fund_510300_history.json'
    
    result = process_comparison_data(file_path_1, file_path_2)
    if result is not None:
        print(f"处理成功! 共 {len(result)} 个重合交易日。")
    else:
        print("处理失败!")
        
except Exception as e:
    print(f"发生错误: {e}")
    import traceback
    traceback.print_exc()