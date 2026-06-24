import json
import pandas as pd
import os

print("调试数据合并过程...")

def load_and_debug(file_path, name):
    """读取单个文件并显示调试信息"""
    print(f"\n加载 {name}...")
    
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return None

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"  从JSON加载了 {len(data)} 条记录")
    
    df = pd.DataFrame(data)
    print(f"  DataFrame形状: {df.shape}")
    print(f"  列名: {list(df.columns)}")
    
    # 检查日期格式并相应处理
    sample_date = df['净值日期'].iloc[0]
    print(f"  示例日期值: {sample_date} (类型: {type(sample_date)})")
    
    if isinstance(sample_date, (int, float)) and sample_date > 1000000000:
        # 如果是大数字，视为毫秒时间戳
        df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
        print("  处理方式: 毫秒时间戳")
    else:
        # 否则视为字符串日期格式
        df['date'] = pd.to_datetime(df['净值日期'])
        print("  处理方式: 字符串日期")
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # 提取关键列并重命名
    if '累计净值' in df.columns:
        value_col = '累计净值'
    elif '单位净值' in df.columns:
        value_col = '单位净值'
    else:
        available_cols = list(df.columns)
        raise ValueError(f"数据文件中没有找到净值列，可用列: {available_cols}")
    
    print(f"  使用净值列: {value_col}")
    result = df[['date', value_col]].rename(columns={value_col: 'value'})
    
    print(f"  返回DataFrame形状: {result.shape}")
    print(f"  日期范围: {result['date'].min()} 到 {result['date'].max()}")
    print(f"  前3行日期: {result['date'].head(3).tolist()}")
    
    return result

# 测试两个文件的加载
file_path_1 = 'data/fund_040026_history.json'
file_path_2 = 'data/fund_510300_history.json'

df1 = load_and_debug(file_path_1, "Fund A (040026)")
df2 = load_and_debug(file_path_2, "Fund B (510300)")

if df1 is not None and df2 is not None:
    print("\n测试合并...")
    
    # 显示日期类型
    print(f"df1日期类型: {type(df1['date'].iloc[0])}")
    print(f"df2日期类型: {type(df2['date'].iloc[0])}")
    
    # 显示某些具体日期值
    print(f"df1前5个日期: {df1['date'].head(5).tolist()}")
    print(f"df2前5个日期: {df2['date'].head(5).tolist()}")
    
    # 尝试手动查找交集
    print("\n手动查找日期交集...")
    
    # 转换为字符串进行比较
    df1_dates_str = set(df1['date'].dt.strftime('%Y-%m-%d'))
    df2_dates_str = set(df2['date'].dt.strftime('%Y-%m-%d'))
    
    common_dates_str = df1_dates_str & df2_dates_str
    print(f"字符串格式的重合日期数量: {len(common_dates_str)}")
    
    if len(common_dates_str) > 0:
        print(f"前5个重合日期 (字符串): {sorted(list(common_dates_str))[:5]}")
    
    # 尝试合并
    try:
        df_merge = pd.merge(df1, df2, on='date', suffixes=('_A', '_B'), how='inner')
        print(f"\n合并结果: {len(df_merge)} 条记录")
        if len(df_merge) > 0:
            print(f"合并后前3行日期: {df_merge['date'].head(3).tolist()}")
        else:
            print("合并结果为空! 分析原因...")
            
            # 检查数据类型是否完全一致
            print(f"df1['date'] dtype: {df1['date'].dtype}")
            print(f"df2['date'] dtype: {df2['date'].dtype}")
            
            # 检查时区问题
            print(f"df1['date'] tz: {df1['date'].dt.tz}")
            print(f"df2['date'] tz: {df2['date'].dt.tz}")
            
            # 尝试使用字符串日期进行合并测试
            df1_copy = df1.copy()
            df2_copy = df2.copy()
            df1_copy['date_str'] = df1_copy['date'].dt.strftime('%Y-%m-%d')
            df2_copy['date_str'] = df2_copy['date'].dt.strftime('%Y-%m-%d')
            
            df_merge_str = pd.merge(df1_copy, df2_copy, on='date_str', suffixes=('_A', '_B'), how='inner')
            print(f"使用字符串日期合并结果: {len(df_merge_str)} 条记录")
            
    except Exception as e:
        print(f"合并时发生错误: {e}")
        import traceback
        traceback.print_exc()