import json
import pandas as pd
from scipy import optimize
from datetime import datetime

# ==========================================
# 1. 核心算法：XIRR
# ==========================================
def xirr(cashflows, dates):
    if len(cashflows) != len(dates):
        raise ValueError("现金流和日期数量不一致")
    
    def xnpv(rate, cashflows, dates):
        min_date = min(dates)
        return sum([
            cf / ((1 + rate) ** ((d - min_date).days / 365.0))
            for cf, d in zip(cashflows, dates)
        ])

    try:
        # 求解方程，如果无法收敛(比如数据极端异常)返回 None
        return optimize.newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except RuntimeError:
        return None

# ==========================================
# 2. 读取与处理逻辑
# ==========================================
FILE_NAME = "investment_record.json"

try:
    with open(FILE_NAME, 'r', encoding='utf-8') as f:
        products = json.load(f)
except FileNotFoundError:
    print(f"错误：找不到文件 {FILE_NAME}")
    exit()

# 用于存储计算后的结果列表
calculated_results = []

for p in products:
    cashflows = []
    dates = []
    total_invest = 0
    total_back = 0
    
    # 2.1 构建现金流
    for op in p['operation']:
        d = datetime.strptime(op['date'], "%Y-%m-%d")
        m = float(op['money'])
        
        if op['opt'] == 'buyin':
            cashflows.append(-m)      # 买入：负现金流
            total_invest += m
        elif op['opt'] == 'sellout':
            cashflows.append(m)       # 卖出：正现金流
            total_back += m
        dates.append(d)
        
    # 2.2 加入当前持仓 (视作今日卖出)
    current_val = float(p['currentValue'])
    current_date = datetime.strptime(p['date'], "%Y-%m-%d")
    
    cashflows.append(current_val)
    dates.append(current_date)
    
    # 2.3 计算指标
    rate = xirr(cashflows, dates)
    absolute_profit = (current_val + total_back) - total_invest
    
    # 2.4 将结果存入字典
    calculated_results.append({
        "name": p['name'],
        "invest": total_invest,
        "back": total_back,
        "current": current_val,
        "profit": absolute_profit,
        "xirr": rate if rate is not None else -999.0 # 如果计算失败，给个极小值排在最后
    })

# ==========================================
# 3. 排序 (关键步骤)
# ==========================================
# key=lambda x: x['xirr'] 表示按 xirr 字段排序
# reverse=True 表示降序 (从大到小)
calculated_results.sort(key=lambda x: x['xirr'], reverse=True)

# ==========================================
# 4. 格式化输出
# ==========================================
print(f"{'排名':<4} | {'产品名称':<10} | {'总投入':<8} | {'总取回':<8} | {'当前持仓':<8}  | {'绝对收益':<8} | {'年化收益率(XIRR)'}")
print("-" * 75)

for i, res in enumerate(calculated_results):
    # 处理收益率显示的颜色/格式
    xirr_val = res['xirr']
    xirr_str = f"{xirr_val:.2%}"
    
    # 简单的控制台输出
    print(f"No.{i+1:<3} | {res['name']:<10} | {res['invest']:<10.0f} | {res['back']:<10.0f} | {res['current']:<10.2f} | {res['profit']:<10.2f} | {xirr_str}")
