import json
import pandas as pd
import matplotlib.pyplot as plt
from scipy import optimize
from datetime import datetime
import matplotlib.ticker as mtick

# ==========================================
# 1. 自动生成模拟数据文件 (增加了 nav 净值字段)
# ==========================================
data = {
    "operations": [
        {"date": "2025-01-01", "opt": "buyin", "money": 10000},
        {"date": "2025-03-15", "opt": "buyin", "money": 5000},
        {"date": "2025-04-20", "opt": "sellout", "money": 2000}
    ],
    "monthly_snapshots": [
        # 假设初始净值为 1.000
        {"date": "2025-01-31", "value": 9800,  "nav": 0.980}, # 净值跌
        {"date": "2025-02-28", "value": 9900,  "nav": 0.990}, # 净值回升
        {"date": "2025-03-31", "value": 15100, "nav": 1.020}, # 净值突破1
        {"date": "2025-04-30", "value": 13500, "nav": 1.050}, # 净值继续涨
        {"date": "2025-05-31", "value": 14000, "nav": 1.080}, 
        {"date": "2025-06-30", "value": 14800, "nav": 1.150}, # 大涨
        {"date": "2025-07-31", "value": 15500, "nav": 1.180}  
    ]
}

with open("fund_monthly_data_v2.json", "w", encoding='utf-8') as f:
    json.dump(data, f, indent=4)

# ==========================================
# 2. XIRR 计算函数 (保持不变)
# ==========================================
def xirr(cashflows, dates):
    if len(cashflows) != len(dates): return None
    def xnpv(rate, cashflows, dates):
        min_date = min(dates)
        if rate <= -1.0: return float('inf')
        return sum([cf / ((1 + rate) ** ((d - min_date).days / 365.0)) for cf, d in zip(cashflows, dates)])
    try:
        return optimize.newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except (RuntimeError, OverflowError):
        return None

# ==========================================
# 3. 数据处理
# ==========================================
with open("fund_monthly_data_v2.json", 'r') as f:
    raw_data = json.load(f)

ops = raw_data['operations']
snapshots = raw_data['monthly_snapshots']

history_dates = []
history_xirr = []
history_actual_return = []
history_nav = [] # 新增：存储净值

print(f"{'日期':<12} | {'实际收益率':<10} | {'年化收益率':<10} | {'基金净值'}")
print("-" * 60)

for snap in snapshots:
    snap_date = datetime.strptime(snap['date'][:10], "%Y-%m-%d")
    current_val = float(snap['value'])
    current_nav = float(snap.get('nav', 1.0)) # 获取净值
    
    # --- 构建现金流 ---
    cashflows = []
    dates = []
    total_invest = 0
    total_withdraw = 0
    
    for op in ops:
        op_date = datetime.strptime(op['date'][:10], "%Y-%m-%d")
        if op_date <= snap_date:
            m = float(op['money'])
            if op['opt'] == 'buyin':
                cashflows.append(-m)
                total_invest += m
            elif op['opt'] == 'sellout':
                cashflows.append(m)
                total_withdraw += m
            dates.append(op_date)
            
    cashflows.append(current_val)
    dates.append(snap_date)
    
    # --- 计算指标 ---
    if total_invest > 0:
        actual_ret = ((current_val + total_withdraw) - total_invest) / total_invest
    else:
        actual_ret = 0
        
    days_diff = (snap_date - min(dates)).days
    if days_diff < 7:
        xirr_val = 0
    else:
        xirr_val = xirr(cashflows, dates)
        if xirr_val is None: xirr_val = 0
    
    history_dates.append(snap_date)
    history_xirr.append(xirr_val)
    history_actual_return.append(actual_ret)
    history_nav.append(current_nav) # 记录净值
    
    print(f"{snap['date']:<12} | {actual_ret:<10.2%} | {xirr_val:<10.2%} | {current_nav:.3f}")

# ==========================================
# 4. 绘图 (三轴图关键代码)
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig, ax1 = plt.subplots(figsize=(12, 7))

# --- 轴1 (左): 实际收益率 ---
color1 = '#1f77b4' # 蓝色
ax1.set_xlabel('日期')
ax1.set_ylabel('实际累计收益率', color=color1, fontweight='bold')
line1 = ax1.plot(history_dates, history_actual_return, color=color1, marker='o', label='实际收益率 (左轴)', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color1)
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax1.grid(True, alpha=0.3)

# --- 轴2 (右1): 年化收益率 ---
ax2 = ax1.twinx()
color2 = '#d62728' # 红色
ax2.set_ylabel('年化收益率 (XIRR)', color=color2, fontweight='bold')
line2 = ax2.plot(history_dates, history_xirr, color=color2, marker='x', linestyle='--', label='年化收益率 (右轴)', linewidth=1.5)
ax2.tick_params(axis='y', labelcolor=color2)
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

# --- 轴3 (右2): 基金净值 (关键部分) ---
ax3 = ax1.twinx()
color3 = '#ff7f0e' # 橙色/金色
# 将第三个轴向右移动 60 个点，防止和轴2重叠
ax3.spines["right"].set_position(("outward", 60))
ax3.set_ylabel('基金单位净值 (NAV)', color=color3, fontweight='bold')
line3 = ax3.plot(history_dates, history_nav, color=color3, marker='^', linestyle='-', label='基金净值走势 (最右轴)', linewidth=2, alpha=0.8)
ax3.tick_params(axis='y', labelcolor=color3)

# --- 合并图例 ---
# 因为有三个轴，需要把图例收集到一起显示
lines = line1 + line2 + line3
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left')

plt.title('基金全景分析：净值走势 vs 个人收益表现')
fig.tight_layout() # 自动调整布局，防止最右边的轴被切掉
plt.show()