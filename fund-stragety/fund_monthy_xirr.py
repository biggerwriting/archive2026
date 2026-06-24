import json
import pandas as pd
import matplotlib.pyplot as plt
from scipy import optimize
from datetime import datetime

# ==========================================
# 1. 自动生成模拟数据文件
# ==========================================
# 场景：
# 1月买入10000，2月不动，3月又买入5000，4月取出2000，之后一直持有
# 基金表现：前期震荡，后期上涨
data = {
    "operations": [
        {"date": "2025-01-01", "opt": "buyin", "money": 10000},
        {"date": "2025-03-15", "opt": "buyin", "money": 5000},
        {"date": "2025-04-20", "opt": "sellout", "money": 2000}
    ],
    "monthly_snapshots": [
        {"date": "2025-01-31", "value": 9800},  # 1月亏了
        {"date": "2025-02-28", "value": 9900},  # 2月回暖
        {"date": "2025-03-31", "value": 15100}, # 3月加仓后微涨
        {"date": "2025-04-30", "value": 13500}, # 4月取出后，剩余市值
        {"date": "2025-05-31", "value": 14000}, # 5月上涨
        {"date": "2025-06-30", "value": 14800}, # 6月大涨
        {"date": "2025-07-31", "value": 15500}  # 7月继续涨
    ]
}

with open("fund_monthly_data.json", "w", encoding='utf-8') as f:
    json.dump(data, f, indent=4)

# ==========================================
# 2. XIRR 计算函数
# ==========================================
def xirr(cashflows, dates):
    if len(cashflows) != len(dates):
        return None
    
    def xnpv(rate, cashflows, dates):
        min_date = min(dates)
        # 防止除零错误，rate 不能为 -1
        if rate <= -1.0: return float('inf')
        return sum([cf / ((1 + rate) ** ((d - min_date).days / 365.0)) for cf, d in zip(cashflows, dates)])

    try:
        return optimize.newton(lambda r: xnpv(r, cashflows, dates), 0.1)
    except (RuntimeError, OverflowError):
        return None

# ==========================================
# 3. 主逻辑：滚动计算每月指标
# ==========================================
# 读取数据
with open("fund_monthly_data.json", 'r') as f:
    raw_data = json.load(f)

ops = raw_data['operations']
snapshots = raw_data['monthly_snapshots']

# 结果存储
history_dates = []
history_xirr = []
history_actual_return = []

print(f"{'日期':<12} | {'投入本金':<10} | {'当前市值':<10} | {'实际收益率':<10} | {'年化收益率(XIRR)'}")
print("-" * 75)

# 遍历每一个月度快照
for snap in snapshots:
    snap_date_str = snap['date'][:10]
    snap_date = datetime.strptime(snap_date_str, "%Y-%m-%d")
    current_val = float(snap['value'])
    
    # --- 构建截至到当月的现金流 ---
    cashflows = []
    dates = []
    
    total_invest = 0
    total_withdraw = 0
    
    # 1. 筛选出 snapshot 日期之前(含)的所有操作
    for op in ops:
        op_date_str = op['date'][:10]
        op_date = datetime.strptime(op_date_str, "%Y-%m-%d")
        
        if op_date <= snap_date:
            m = float(op['money'])
            if op['opt'] == 'buyin':
                cashflows.append(-m)
                total_invest += m
            elif op['opt'] == 'sellout':
                cashflows.append(m)
                total_withdraw += m
            dates.append(op_date)
            
    # 2. 加入当前的市值作为“假想卖出”
    cashflows.append(current_val)
    dates.append(snap_date)
    
    # --- 计算指标 ---
    
    # A. 实际累计收益率 = (当前市值 + 已取回现金 - 总投入) / 总投入
    if total_invest > 0:
        actual_profit = (current_val + total_withdraw) - total_invest
        actual_ret = actual_profit / total_invest
    else:
        actual_ret = 0
        
    # B. 年化收益率 (XIRR)
    # 如果持有时间太短(比如少于7天)，XIRR计算会非常夸张，这里可以做个过滤或容错
    days_diff = (snap_date - min(dates)).days
    if days_diff < 7:
        xirr_val = 0 # 时间太短不计年化
    else:
        xirr_val = xirr(cashflows, dates)
        if xirr_val is None: xirr_val = 0
    
    # --- 存入列表用于绘图 ---
    history_dates.append(snap_date)
    history_xirr.append(xirr_val)
    history_actual_return.append(actual_ret)
    
    print(f"{snap_date_str:<12} | {total_invest:<10.0f} | {current_val:<10.0f} | {actual_ret:<10.2%} | {xirr_val:.2%}")

# ==========================================
# 4. 绘图 (双轴图)
# ==========================================
# 设置中文字体 (Mac通常用 Arial Unicode MS 或 Heiti TC，Windows用 SimHei)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif'] 
plt.rcParams['axes.unicode_minus'] = False # 解决负号显示问题

fig, ax1 = plt.subplots(figsize=(10, 6))

# 绘制左轴：实际收益率 (柱状图或面积图)
color1 = 'tab:blue'
ax1.set_xlabel('日期')
ax1.set_ylabel('实际累计收益率 (Actual Return)', color=color1)
ax1.plot(history_dates, history_actual_return, color=color1, marker='o', label='实际收益率', linewidth=2)
ax1.tick_params(axis='y', labelcolor=color1)
# 添加水平0线
ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

# 绘制右轴：年化收益率 (折线图)
ax2 = ax1.twinx() 
color2 = 'tab:red'
ax2.set_ylabel('年化收益率 (Annualized XIRR)', color=color2)
ax2.plot(history_dates, history_xirr, color=color2, marker='x', linestyle='--', label='年化收益率(XIRR)', linewidth=2)
ax2.tick_params(axis='y', labelcolor=color2)

# 格式化百分比显示
import matplotlib.ticker as mtick
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

plt.title('基金收益表现分析：实际收益 vs 年化收益')
fig.tight_layout()
plt.grid(True, alpha=0.3)
plt.show()