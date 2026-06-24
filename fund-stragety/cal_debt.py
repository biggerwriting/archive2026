import pandas as pd
from datetime import datetime

# 原始账目数据 (日期, 金额) 
# 负数表示小王借出(增加债务)，正数表示小林归还(减少债务)
transactions = [
    # 2023年
    ("2023-03-15", -20000), ("2023-03-31", 2000), ("2023-04-28", 2000),
    ("2023-05-31", 2000), ("2023-06-12", -2500), ("2023-08-10", 1000),
    ("2023-09-08", 2000), ("2023-10-10", 2000), ("2023-10-16", -2500),
    ("2023-11-11", 1000), ("2023-12-08", 1000), ("2023-12-12", -2300),
    # 2024年
    ("2024-01-10", 1000), ("2024-01-31", 1300), ("2024-02-24", -3000),
    ("2024-03-08", 1000), ("2024-04-03", 1000), ("2024-05-10", -8000),
    # 开始计息阶段
    ("2024-07-29", 1052.5), ("2024-10-10", 1052.5), ("2024-10-21", -1000),
    # 2025年
    ("2025-01-18", 1052.5), ("2025-03-17", 1052.5), ("2025-04-09", -1000),
    ("2025-04-12", -1500), ("2025-04-19", 1552.5), ("2025-04-21", -1000),
    ("2025-04-26", -500), ("2025-05-04", -1000), ("2025-05-14", -500),
    ("2025-05-23", -1000), ("2025-06-12", -300), ("2025-06-16", -500),
    ("2025-06-19", -500), ("2025-06-25", -600), ("2025-06-27", -1000),
    ("2025-07-11", 1000), ("2025-07-16", -600), ("2025-07-18", -700),
    ("2025-07-21", -200), ("2025-09-06", 500), ("2025-09-19", -1000),
    ("2025-09-29", 1000), ("2025-10-08", -237), ("2025-10-12", 240),
    ("2025-11-28", -200)
]

def calculate_debt(trans_list, target_date_str, interest_start_date_str):
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    interest_start_date = datetime.strptime(interest_start_date_str, "%Y-%m-%d")
    annual_rate = 0.03
    
    principal = 0.0      # 未还本金
    total_interest = 0.0 # 累计未付利息
    last_date = None
    
    # 按照日期排序确保计算准确
    sorted_trans = sorted([(datetime.strptime(d, "%Y-%m-%d"), amt) for d, amt in trans_list])

    for current_date, amount in sorted_trans:
        # 如果当前日期超过了目标日期，停止处理
        if current_date > target_date:
            break
            
        # 1. 计算利息（仅在2024-05-10之后）
        if last_date and last_date >= interest_start_date:
            days = (current_date - last_date).days
            # 利息 = 本金 * 年利率 * (天数/365)
            daily_interest = principal * annual_rate * (days / 365.0)
            total_interest += daily_interest
        elif last_date and current_date > interest_start_date:
            # 跨越了计息开始日的情况
            days = (current_date - interest_start_date).days
            daily_interest = principal * annual_rate * (days / 365.0)
            total_interest += daily_interest
            
        # 2. 处理变动
        if amount < 0:
            # 借出：直接增加本金
            principal += abs(amount)
        else:
            # 归还：先还利息，剩下的还本金
            if amount <= total_interest:
                total_interest -= amount
            else:
                remaining_pay = amount - total_interest
                total_interest = 0
                principal -= remaining_pay
        
        last_date = current_date

    # 最后计算从最后一笔交易到 2026-01-15 的利息
    if last_date < target_date:
        days = (target_date - last_date).days
        total_interest += principal * annual_rate * (days / 365.0)

    return principal, total_interest
def calculate_debt_principal_first(trans_list, target_date_str, interest_start_date_str):
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    interest_start_date = datetime.strptime(interest_start_date_str, "%Y-%m-%d")
    annual_rate = 0.03
    
    principal = 0.0      # 未还本金
    accrued_interest = 0.0 # 累计产生的总利息
    last_date = None
    
    # 排序
    sorted_trans = sorted([(datetime.strptime(d, "%Y-%m-%d"), amt) for d, amt in trans_list])

    for current_date, amount in sorted_trans:
        if current_date > target_date:
            break
            
        # 1. 计算从上一个日期到当前日期产生的利息
        if last_date and last_date >= interest_start_date:
            days = (current_date - last_date).days
            accrued_interest += principal * annual_rate * (days / 365.0)
        elif last_date and current_date > interest_start_date:
            days = (current_date - interest_start_date).days
            accrued_interest += principal * annual_rate * (days / 365.0)
            
        # 2. 处理变动
        if amount < 0:
            # 借出：增加本金
            principal += abs(amount)
        else:
            # 归还：优先还本金
            if amount <= principal:
                principal -= amount
            else:
                # 本金还清了，剩下的还利息
                remaining_pay = amount - principal
                principal = 0
                accrued_interest -= remaining_pay
        
        last_date = current_date

    # 计算最后一段日期的利息
    if last_date < target_date:
        days = (target_date - last_date).days
        accrued_interest += principal * annual_rate * (days / 365.0)

    return principal, accrued_interest
# 配置
INTEREST_START = datetime(2024, 5, 10)
TARGET_DATE = datetime(2026, 1, 15)
ANNUAL_RATE = 0.03

def generate_report(data):
    principal = 0.0
    interest_balance = 0.0
    last_date = None
    report = []

    # 排序
    sorted_data = sorted([(datetime.strptime(d, "%Y-%m-%d"), amt) for d, amt in data])
    
    # 为了计算到今天，手动在最后加一个当天的空记录
    if sorted_data[-1][0] < TARGET_DATE:
        sorted_data.append((TARGET_DATE, 0))

    for current_date, amount in sorted_data:
        days = 0
        new_interest = 0.0
        
        # 1. 计算期间利息
        if last_date:
            days = (current_date - last_date).days
            # 只有在计息开始日之后才算利息
            calc_start = max(last_date, INTEREST_START)
            if current_date > INTEREST_START:
                active_days = (current_date - calc_start).days
                if active_days > 0:
                    new_interest = principal * ANNUAL_RATE * (active_days / 365.0)
                    interest_balance += new_interest

        # 2. 处理本笔交易
        trans_type = "借出" if amount < 0 else ("归还" if amount > 0 else "截止日结算")
        abs_amt = abs(amount)
        
        if amount < 0:
            principal += abs_amt
        elif amount > 0:
            if abs_amt <= principal:
                principal -= abs_amt
            else:
                remaining_pay = abs_amt - principal
                principal = 0
                interest_balance -= remaining_pay

        # 3. 记录
        report.append({
            "日期": current_date.strftime("%Y-%m-%d"),
            "类型": trans_type,
            "变动金额": amount,
            "间隔天数": days,
            "新增利息": round(new_interest, 2),
            "剩余本金": round(principal, 2),
            "待还利息": round(max(0, interest_balance), 2),
            "总欠款": round(principal + max(0, interest_balance), 2)
        })
        
        last_date = current_date

    return pd.DataFrame(report)

# 3. 生成并导出
df = generate_report(transactions)
df.to_csv("debt_details.csv", index=False, encoding="utf-8-sig")
print("账目明细表已生成：debt_details.csv")
print(df.tail(10)) # 打印最后10笔数据预览

# 2. 执行
p_bal, i_bal = calculate_debt_principal_first(transactions, "2026-01-15", "2024-05-10")

print(f"--- 优先还本金逻辑 (截至2026-01-15) ---")
print(f"剩余待还本金: {p_bal:,.2f} 元")
print(f"剩余待还利息: {max(0, i_bal):,.2f} 元")
print(f"总计欠款: {p_bal + max(0, i_bal):,.2f} 元")


# 1. 执行计算
final_p, final_i = calculate_debt(transactions, "2026-01-15", "2024-05-10")

print(f"--- 截至 2026年1月15日 计算结果 ---")
print(f"剩余待还本金: {final_p:,.2f} 元")
print(f"累计未付利息: {final_i:,.2f} 元")
print(f"总计应收金额: {final_p + final_i:,.2f} 元")