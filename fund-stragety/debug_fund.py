#!/usr/bin/env python3

import akshare as ak
import pandas as pd

def debug_fund_code(code):
    """调试指定基金代码的具体问题"""
    print(f"调试基金代码: {code}")
    
    # 1. 尝试东方财富接口
    print("\n1. 尝试东方财富接口...")
    try:
        df = ak.fund_open_fund_hist_em(symbol=code, period="after_adjustment", adjust="1")
        print(f"   ✓ 成功获取数据")
        print(f"   数据类型: {type(df)}")
        print(f"   数据形状: {df.shape}")
        print(f"   列名: {df.columns.tolist()}")
        if not df.empty:
            print(f"   前5行数据:")
            print(df.head())
        else:
            print("   数据为空")
    except Exception as e:
        print(f"   ✗ 失败: {e}")
    
    # 2. 尝试新浪接口
    print("\n2. 尝试新浪ETF接口...")
    try:
        # 尝试不同前缀
        for prefix in ['sh', 'sz']:
            print(f"   尝试 {prefix}{code}...")
            try:
                df = ak.fund_etf_hist_sina(symbol=f"{prefix}{code}")
                print(f"     ✓ 成功获取 {prefix}{code}")
                print(f"     数据形状: {df.shape}")
                print(f"     列名: {df.columns.tolist()}")
                if not df.empty:
                    print(f"     前3行数据:")
                    print(df.head(3))
                break
            except Exception as e:
                print(f"     ✗ {prefix}{code} 失败: {e}")
    except Exception as e:
        print(f"   ✗ 新浪接口完全失败: {e}")
    
    # 3. 获取基金基本信息
    print("\n3. 尝试获取基金基本信息...")
    try:
        fund_info = ak.fund_name_em()
        fund_row = fund_info[fund_info['基金代码'] == code]
        if not fund_row.empty:
            print(f"   ✓ 找到基金信息:")
            print(f"   基金名称: {fund_row.iloc[0]['基金名称']}")
            print(f"   基金类型: {fund_row.iloc[0]['基金类型']}")
        else:
            print(f"   ✗ 未找到代码为 {code} 的基金")
    except Exception as e:
        print(f"   ✗ 获取基金信息失败: {e}")

if __name__ == "__main__":
    print("开始调试基金数据获取问题...")
    
    # 测试你遇到问题的基金
    test_codes = ["100058", "007300"]
    
    for test_code in test_codes:
        print("=" * 60)
        debug_fund_code(test_code)
        print("=" * 60)