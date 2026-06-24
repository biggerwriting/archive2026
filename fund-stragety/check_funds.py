#!/usr/bin/env python3

import akshare as ak
import pandas as pd

print('正在检查基金代码是否存在...')
try:
    fund_info = ak.fund_name_em()
    
    for code in ['007300', '100058']:
        fund_row = fund_info[fund_info['基金代码'] == code]
        if not fund_row.empty:
            print(f'✓ 找到基金 {code}: {fund_row.iloc[0]["基金名称"]} ({fund_row.iloc[0]["基金类型"]})')
        else:
            print(f'✗ 未找到基金 {code}')
            
        # 查找相似的基金代码
        similar = fund_info[fund_info['基金代码'].str.contains(code[:4], na=False)]
        if not similar.empty:
            print(f'  相似代码: {similar.iloc[0]["基金代码"]} - {similar.iloc[0]["基金名称"]}')
except Exception as e:
    print(f'获取基金信息失败: {e}')