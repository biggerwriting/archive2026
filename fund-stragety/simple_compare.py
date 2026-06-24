#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# 尝试导入 akshare，如果没有则使用模拟数据
try:
    import akshare as ak
    AK_AVAILABLE = True
except ImportError:
    print("警告: 未安装 akshare，将使用模拟数据进行演示")
    AK_AVAILABLE = False

# ==========================================
# 1. 配置部分
# ==========================================
# 基金代码列表
fund_codes = ['040026', '008928', '008701', '007361']

# 设置绘图风格和中文字体
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 数据获取函数（带有兼容性处理）
# ==========================================
def get_fund_data_safe(codes):
    """安全获取基金数据，处理各种兼容性问题"""
    
    if not AK_AVAILABLE:
        # 创建模拟数据用于演示
        print("使用模拟数据进行演示...")
        dates = pd.date_range('2021-01-01', periods=1000, freq='D')
        data = {}
        for i, code in enumerate(codes):
            # 生成模拟的基金净值数据
            import numpy as np
            np.random.seed(i)  # 为了可重复性
            returns = np.random.normal(0.0005, 0.015, len(dates))  # 日收益率
            nav = 1.0 * (1 + returns).cumprod()  # 净值序列
            data[f'基金{i+1}'] = pd.Series(nav, index=dates)
        
        df_merged = pd.DataFrame(data)
        print(f"模拟数据形状: {df_merged.shape}")
        return df_merged
    
    data_dict = {}
    name_dict = {}
    
    print("正在获取基金数据...")
    
    # 获取基金名称映射
    try:
        fund_info = ak.fund_name_em()
        for code in codes:
            fund_row = fund_info[fund_info['基金代码'] == code]
            if not fund_row.empty:
                name_dict[code] = fund_row.iloc[0]['基金名称']
            else:
                name_dict[code] = code
    except Exception as e:
        print(f"获取基金信息失败: {e}")
        # 使用代码作为名称
        for code in codes:
            name_dict[code] = code
    
    # 获取每个基金的数据
    for code in codes:
        df = None
        print(f"正在获取 {code} ({name_dict[code]})...")
        
        # 尝试多种接口
        interfaces_to_try = [
            ('fund_open_fund_hist_em', {'symbol': code, 'period': 'after_adjustment', 'adjust': '1'}),
            ('fund_em_open_fund_info', {'fund': code, 'indicator': '累计净值'}),
        ]
        
        for interface_name, params in interfaces_to_try:
            try:
                interface = getattr(ak, interface_name, None)
                if interface is not None:
                    df = interface(**params)
                    print(f"  ✓ 使用 {interface_name} 成功获取数据")
                    break
                else:
                    print(f"  - 接口 {interface_name} 不存在")
            except Exception as e:
                print(f"  - {interface_name} 失败: {e}")
                continue
        
        if df is not None and not df.empty:
            # 数据清洗
            try:
                # 处理日期列
                date_col = None
                for col in ['净值日期', 'date', '日期']:
                    if col in df.columns:
                        date_col = col
                        break
                
                if date_col:
                    df['date'] = pd.to_datetime(df[date_col])
                    df.set_index('date', inplace=True)
                else:
                    print(f"    ✗ 未找到日期列，跳过 {code}")
                    continue
                
                # 处理净值列
                nav_col = None
                for col in ['累计净值', '单位净值', 'close', '净值']:
                    if col in df.columns:
                        nav_col = col
                        break
                
                if nav_col:
                    df[nav_col] = pd.to_numeric(df[nav_col], errors='coerce')
                    df = df.dropna(subset=[nav_col])
                    
                    if not df.empty:
                        data_dict[name_dict[code]] = df[nav_col]
                        print(f"    ✓ 成功处理 {code} ({len(df)} 条记录)")
                    else:
                        print(f"    ✗ {code} 有效数据为空")
                else:
                    print(f"    ✗ 未找到净值列，跳过 {code}")
                    
            except Exception as e:
                print(f"    ✗ 数据处理失败: {e}")
        else:
            print(f"    ✗ 无法获取 {code} 的数据")
    
    # 合并数据
    if not data_dict:
        print("警告: 没有成功获取任何基金数据")
        return pd.DataFrame()
    
    try:
        df_merged = pd.concat(data_dict.values(), axis=1, keys=data_dict.keys(), join='inner')
        df_merged.sort_index(inplace=True)
        print(f"成功获取 {len(data_dict)} 个基金的数据，合并后形状: {df_merged.shape}")
        return df_merged
    except Exception as e:
        print(f"合并数据失败: {e}")
        return pd.DataFrame()

# ==========================================
# 3. 主程序
# ==========================================
if __name__ == "__main__":
    print("开始获取基金数据...")
    df = get_fund_data_safe(fund_codes)
    
    if df.empty:
        print("没有获取到有效数据，无法进行后续分析")
    else:
        print(f"\n数据获取成功！")
        print(f"时间范围: {df.index[0]} 到 {df.index[-1]}")
        print(f"基金数量: {df.shape[1]}")
        print(f"数据预览:")
        print(df.head())
        
        # 这里可以添加你的绘图和分析代码
        print("\n可以在此处添加绘图和分析代码...")