import json
import pandas as pd
from scipy import optimize
from datetime import datetime

# ==========================================
# 1. 核心算法：XIRR 计算函数
# ==========================================
def xirr(cashflows, dates):
    """
    计算不定期现金流的年化收益率
    :param cashflows: 现金流列表 (买入为负，卖出为正)
    :param dates: 对应的日期列表 (datetime对象)
    :return: 年化收益率 (小数，如 0.05 代表 5%)
    """
    if len(cashflows) != len(dates):
        raise ValueError("现金流和日期数量不一致")
    
    # 定义方程：sum( cashflow / (1+r)^years ) = 0
    def xnpv(rate, cashflows, dates):
        min_date = min(dates)
        return sum([
            cf / ((1 + rate) ** ((d - min_date).days / 365.0))
            for cf, d in zip(cashflows, dates)
        ])

    try:
        # 使用牛顿法求解，猜测初始收益率为 0.1 (10%)
        return optimize.newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except RuntimeError:
        return 0.0 # 无法收敛时返回0

# ==========================================
# 2. 数据解析与处理
# ==========================================
data_json = """
[
    {
        "name":"半年鑫债券",
        "code":"0001",
        "operation":[
            {
                "opt":"buyin",
                "money":"1000",
                "date":"2025-09-18"
            },{
                "opt":"sellout",
                "money":"100",
                "date":"2025-10-18"
            }
        ],
        "currentValue":1100,
        "date":"2026-01-14"
    }
]
"""

products = json.loads(data_json)

print(f"{'产品名称':<10} | {'总投入':<8} | {'总取回':<8} | {'当前持仓':<8} | {'绝对收益':<8} | {'XIRR年化收益率'}")
print("-" * 80)

for p in products:
    cashflows = []
    dates = []
    
    total_invest = 0 # 统计总投入
    total_back = 0   # 统计总取回
    
    # 1. 处理历史操作
    for op in p['operation']:
        d = datetime.strptime(op['date'], "%Y-%m-%d")
        m = float(op['money'])
        
        if op['opt'] == 'buyin':
            # 买入：现金流为负
            cashflows.append(-m)
            total_invest += m
        elif op['opt'] == 'sellout':
            # 卖出：现金流为正
            cashflows.append(m)
            total_back += m
        
        dates.append(d)
        
    # 2. 处理当前持仓 (视作今天卖出)
    current_val = float(p['currentValue'])
    current_date = datetime.strptime(p['date'], "%Y-%m-%d")
    
    cashflows.append(current_val)
    dates.append(current_date)
    
    # 3. 计算结果
    result_xirr = xirr(cashflows, dates)
    
    # 计算绝对收益 (当前价值 + 已取回 - 总投入)
    absolute_profit = (current_val + total_back) - total_invest
    
    print(f"{p['name']:<10} | {total_invest:<10} | {total_back:<10} | {current_val:<10} | {absolute_profit:<10.2f} | {result_xirr:.2%}")
