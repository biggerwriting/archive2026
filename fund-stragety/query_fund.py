import akshare as ak
import pandas as pd
import os
import traceback

print("开始查询基金数据...")

# 使用一个已知有效的基金代码
fund_code = "510300"  # 华安策略优选

print(f"正在查询基金 {fund_code} 信息...")

# 方法1: 尝试基金基本信息查询
try:
    print(f"尝试使用代码 {fund_code} 查询基本信息...")
    fund_info_df = ak.fund_individual_basic_info_xq(symbol=fund_code)
    if fund_info_df is not None and not fund_info_df.empty:
        print("--- 基金基本信息 ---")
        print(fund_info_df)
    else:
        print("基本信息查询返回空结果")
except Exception as e:
    print(f"基本信息查询失败，错误类型: {type(e).__name__}")
    print(f"错误信息: {str(e)}")
    
    # 尝试备用方法: 查询基金列表
    try:
        print("尝试使用 fund_name_em 查询基金列表...")
        fund_list = ak.fund_name_em()
        print(f"基金列表查询成功，共 {len(fund_list)} 条记录")
        
        # 查找特定的基金
        target_fund = fund_list[fund_list['基金代码'] == fund_code]
        if not target_fund.empty:
            print(f"\n--- {fund_code} 基金基本信息 ---")
            print(target_fund)
        else:
            # 如果找不到指定代码，显示前几行示例
            print(f"未找到 {fund_code} 基金信息，显示前5条记录作为参考:")
            print(fund_list.head(5))
            
    except Exception as e2:
        print(f"备用方法也失败: {e2}")

# 主要任务: 获取基金净值数据
print(f"\n正在获取基金 {fund_code} 的净值数据...")
try:
    # 尝试不同的指标类型
    indicators = ["单位净值走势", "累计净值走势", "日增长率"]
    
    for indicator in indicators:
        try:
            print(f"尝试获取指标: {indicator}")
            df = ak.fund_open_fund_info_em(symbol=fund_code, indicator=indicator)
            if df is not None and not df.empty:
                print(f"成功获取 {indicator} 数据，共 {len(df)} 条记录")
                
                # 2. 数据预处理
                # 将日期列转换为字符串（JSON 不原生支持 Timestamp 对象）
                if '净值日期' in df.columns:
                    df['净值日期'] = df['净值日期'].astype(str)
                    print("日期列类型转换完成")
                
                # 检查数据列
                print(f"数据列: {list(df.columns)}")
                print(f"前3行数据示例:")
                print(df.head(3))
                
                # 3. 保存为本地 JSON 文件
                # orient='records' 会生成 [{"列1": 值1, "列2": 值2}, ...] 的列表格式，最适合程序处理
                file_path = f"data/fund_{fund_code}_history.json"
                os.makedirs('data', exist_ok=True)  # 确保data目录存在
                df.to_json(file_path, orient='records', force_ascii=False, indent=4)
                
                print(f"数据已成功保存至: {file_path}")
                break
                
        except Exception as e:
            print(f"获取指标 {indicator} 失败: {e}")
    
    else:
        print("所有指标类型都获取失败")
        
except Exception as e:
    print(f"净值数据获取整体失败: {e}")
    traceback.print_exc()

print("\n查询完成!")