#!/usr/bin/env python3

import pandas as pd

def test_fund_040026():
    """测试获取基金040026历史净值数据的各种方法"""
    
    # 先检查akshare是否可用
    try:
        import akshare as ak
        print(f"✓ akshare版本: {ak.__version__}")
    except ImportError:
        print("✗ 未安装akshare")
        return
    
    code = "040026"
    print(f"\n正在测试获取基金 {code} 的历史净值数据...")
    
    # 1. 先查看基金基本信息
    print("\n1. 查看基金基本信息...")
    try:
        fund_info = ak.fund_name_em()
        fund_row = fund_info[fund_info['基金代码'] == code]
        if not fund_row.empty:
            print(f"   ✓ 找到基金: {fund_row.iloc[0]['基金名称']}")
            print(f"   基金类型: {fund_row.iloc[0]['基金类型']}")
        else:
            print(f"   ✗ 未找到基金 {code}")
            return
    except Exception as e:
        print(f"   ✗ 获取基金信息失败: {e}")
    
    # 2. 尝试不同的接口获取历史净值
    interfaces_to_test = [
        {
            'name': 'fund_open_fund_hist_em (东方财富开放式基金历史净值)',
            'func': lambda: ak.fund_open_fund_hist_em(symbol=code, period="after_adjustment", adjust="1"),
            'desc': '最常用的基金净值接口'
        },
        {
            'name': 'fund_em_open_fund_info (东方财富基金信息)', 
            'func': lambda: ak.fund_em_open_fund_info(fund=code, indicator="累计净值"),
            'desc': '基金信息接口'
        },
        {
            'name': 'fund_em_open_fund_info (单位净值)',
            'func': lambda: ak.fund_em_open_fund_info(fund=code, indicator="单位净值"),
            'desc': '基金单位净值接口'
        },
    ]
    
    for i, interface in enumerate(interfaces_to_test, 2):
        print(f"\n{i}. 尝试 {interface['name']}...")
        print(f"   描述: {interface['desc']}")
        
        try:
            # 检查接口是否存在
            func_name = interface['func'].__code__.co_names[0]
            if not hasattr(ak, func_name):
                print(f"   ✗ 接口 {func_name} 不存在")
                continue
                
            df = interface['func']()
            
            if df is None or df.empty:
                print(f"   ✗ 获取数据为空")
            else:
                print(f"   ✓ 成功获取数据 (形状: {df.shape})")
                print(f"   列名: {df.columns.tolist()}")
                
                # 显示前几行数据
                print(f"   数据预览:")
                print(df.head())
                
                # 尝试标准化处理
                print(f"   正在标准化处理...")
                processed_df = standardize_fund_data(df, code)
                if not processed_df.empty:
                    print(f"   ✓ 处理成功，处理后形状: {processed_df.shape}")
                    return processed_df
                
        except Exception as e:
            print(f"   ✗ 失败: {e}")
    
    print(f"\n所有接口尝试失败，无法获取基金 {code} 的数据")
    return None

def standardize_fund_data(df, code):
    """标准化基金数据格式"""
    
    # 创建副本避免修改原始数据
    df = df.copy()
    
    # 处理日期列
    date_col = None
    for col in ['净值日期', 'date', '日期']:
        if col in df.columns:
            date_col = col
            break
    
    if not date_col:
        print(f"     无法找到日期列，可用列: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # 处理净值列
    nav_col = None
    for col in ['累计净值', '单位净值', 'close', '净值']:
        if col in df.columns:
            nav_col = col
            break
    
    if not nav_col:
        print(f"     无法找到净值列，可用列: {df.columns.tolist()}")
        return pd.DataFrame()
    
    # 标准化处理
    try:
        df['date'] = pd.to_datetime(df[date_col])
        df['nav'] = pd.to_numeric(df[nav_col], errors='coerce')
        
        # 删除空值
        df = df.dropna(subset=['date', 'nav'])
        
        if df.empty:
            print(f"     处理后数据为空")
            return pd.DataFrame()
        
        # 设置日期索引并排序
        df = df.set_index('date').sort_index()
        
        # 只保留净值列
        result = pd.DataFrame({code: df['nav']})
        
        print(f"     日期范围: {result.index[0]} 到 {result.index[-1]}")
        print(f"     净值范围: {result[code].min():.4f} 到 {result[code].max():.4f}")
        
        return result
        
    except Exception as e:
        print(f"     数据处理失败: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    result_df = test_fund_040026()
    
    if result_df is not None and not result_df.empty:
        print(f"\n🎉 成功获取并处理基金数据！")
        print(f"保存数据到文件...")
        
        # 保存到CSV文件
        filename = "fund_040026_nav.csv"
        result_df.to_csv(filename)
        print(f"数据已保存到 {filename}")
        
        # 显示基本统计信息
        code = result_df.columns[0]
        print(f"\n基本统计:")
        print(f"总天数: {len(result_df)}")
        print(f"开始日期: {result_df.index[0]}")
        print(f"结束日期: {result_df.index[-1]}")
        print(f"当前净值: {result_df[code].iloc[-1]:.4f}")
        
        # 计算收益率
        total_return = (result_df[code].iloc[-1] / result_df[code].iloc[0] - 1) * 100
        print(f"总收益率: {total_return:.2f}%")
    else:
        print("\n❌ 未能成功获取基金数据")
        print("\n可能的原因:")
        print("1. akshare版本过低或不兼容")
        print("2. 基金代码不正确或基金已停止运作")
        print("3. 网络连接问题")
        print("4. 数据源暂时不可用")
        
        print("\n解决方案:")
        print("1. 更新akshare: pip install --upgrade akshare")
        print("2. 检查基金代码是否正确")
        print("3. 等待一段时间后重试")
        print("4. 尝试其他数据源")