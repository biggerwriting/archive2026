from datetime import date

# 计算国华节节高的收益率
# 1. 定义参数
p_start = 58443.55  # 期初金额
p_end = 58497.93    # 期末金额
d_start = date(2025, 12, 29)
d_end = date(2026, 1, 14)

# 2. 计算持有天数
# 两个日期对象相减，得到的是 timedelta 对象，.days 获取天数
days = (d_end - d_start).days

# 3. 计算绝对收益
profit = p_end - p_start

# 4. 计算年化收益率 (Simple Interest Annualized)
# 公式：(收益 / 本金) * (365 / 天数)
annual_rate = (profit / p_start) * (365 / days)

# 5. 输出结果
print(f"--- 计算结果 ---")
print(f"持有天数: {days} 天")
print(f"绝对收益: {profit:.2f} 元")
print(f"年化收益率: {annual_rate:.2%}")