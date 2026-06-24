import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import os

# ==========================================
# 1. 数据准备
# ==========================================
FILE_PATH = 'sh510300.json'
if not os.path.exists(FILE_PATH):
    print("错误：找不到文件，请检查路径")
    exit()

df = pd.read_json(FILE_PATH)
df['date'] = pd.to_datetime(df['date'], unit='ms')
df = df.sort_values('date')
df.set_index('date', inplace=True)

# 重采样为月度数据（取每月最后一个交易日的收盘价）
monthly_df = df['close'].resample('ME').last().to_frame()

# ==========================================
# 2. 策略回测逻辑
# ==========================================
TARGET_VALUE = 10000  # 目标恒定市值

# 初始化变量
# 策略A: 恒定市值策略
strategy_cash_in = 0    # 累计投入本金
strategy_cash_out = 0   # 累计取出收益
strategy_shares = 0     # 当前持有份额
strategy_history = []   # 记录每月的状态

# 策略B: 买入持有策略 (Lump Sum)
# 假设第一天买入10000元，之后不动
hold_shares = 0

# --- 初始建仓 (第一个月) ---
start_price = monthly_df.iloc[0]['close']
start_date = monthly_df.index[0]

# 策略A建仓
strategy_shares = TARGET_VALUE / start_price
strategy_cash_in += TARGET_VALUE

# 策略B建仓
hold_shares = TARGET_VALUE / start_price

# 记录初始状态
strategy_history.append({
    'date': start_date,
    'price': start_price,
    'net_invest': TARGET_VALUE, # 当前净投入
    'total_cash_in': TARGET_VALUE,
    'total_cash_out': 0,
    'monthly_profit': 0,
    'year': start_date.year
})

# --- 月度循环 (从第二个月开始) ---
for date, row in monthly_df.iloc[1:].iterrows():
    price = row['close']
    
    # 1. 计算当前市值
    current_value = strategy_shares * price
    
    # 2. 计算与目标的差额
    diff = TARGET_VALUE - current_value
    
    money_change = 0 # 本月资金变动 (正数为投入，负数为取出)
    
    if diff > 0:
        # 亏损了，市值不足1万 -> 补仓
        # 买入对应价值的份额
        shares_to_buy = diff / price
        strategy_shares += shares_to_buy
        strategy_cash_in += diff
        money_change = -diff # 记为支出
    elif diff < 0:
        # 盈利了，市值超过1万 -> 止盈
        # 卖出对应价值的份额
        shares_to_sell = abs(diff) / price
        strategy_shares -= shares_to_sell
        strategy_cash_out += abs(diff)
        money_change = abs(diff) # 记为收入
    
    # 记录数据
    strategy_history.append({
        'date': date,
        'price': price,
        'net_invest': strategy_cash_in - strategy_cash_out, # 净投入
        'total_cash_in': strategy_cash_in,
        'total_cash_out': strategy_cash_out,
        'monthly_profit': money_change, # 正数为取出的利润，负数为追加的本金
        'year': date.year
    })

# 转为 DataFrame 方便分析
res_df = pd.DataFrame(strategy_history)
res_df.set_index('date', inplace=True)

# ==========================================
# 3. 结果计算
# ==========================================
# --- A. 策略总收益 ---
final_price = monthly_df.iloc[-1]['close']
# 策略A最终价值 = 手里的1万市值 + 拿出来的钱 - 投进去的钱
strategy_final_asset = (strategy_shares * final_price) + strategy_cash_out
strategy_return_rate = (strategy_final_asset - strategy_cash_in) / strategy_cash_in

# --- B. 买入持有总收益 ---
hold_final_asset = hold_shares * final_price
hold_return_rate = (hold_final_asset - TARGET_VALUE) / TARGET_VALUE

# --- C. 最大投入金额 ---
max_invest = res_df['total_cash_in'].max()

# --- D. 每年收益率计算 ---
# 逻辑：(当年取出的钱 - 当年投入的钱) / 10000(基准本金)
# 这是一个近似的 Yield 计算，表示每年这1万元为你产生了多少现金流
yearly_stats = res_df.groupby('year')['monthly_profit'].sum() / TARGET_VALUE

# ==========================================
# 4. 文字报告输出
# ==========================================
print("="*50)
print("       恒定市值(1万元)策略回测报告")
print("="*50)
print(f"回测区间: {monthly_df.index[0].date()} 至 {monthly_df.index[-1].date()}")
print("-" * 50)
print(f"【策略 A：恒定市值策略】")
print(f"累计投入总本金:  {strategy_cash_in:,.2f} 元 (最大资金占用)")
print(f"累计取出总现金:  {strategy_cash_out:,.2f} 元")
print(f"期末持有市值:    {strategy_shares * final_price:,.2f} 元 (强制归位)")
print(f"策略总净利润:    {strategy_final_asset - strategy_cash_in:,.2f} 元")
print(f"策略总收益率:    {strategy_return_rate:.2%}")
print("-" * 50)
print(f"【策略 B：一次性买入持有】")
print(f"期初投入:       10,000.00 元")
print(f"期末市值:       {hold_final_asset:,.2f} 元")
print(f"持有总收益率:    {hold_return_rate:.2%}")
print("-" * 50)

if strategy_return_rate > hold_return_rate:
    print("结论：[恒定市值策略] 跑赢了 [买入持有]。")
    print("原因：市场处于震荡或下跌行情，高抛低吸降低了成本。")
else:
    print("结论：[买入持有] 跑赢了 [恒定市值策略]。")
    print("原因：市场处于单边上涨行情，策略过早卖出了筹码，导致踏空。")

print("\n【每年的现金流回报率 (相对于1万本金)】")
print(yearly_stats.apply(lambda x: f"{x:.2%}"))


# ==========================================
# 5. 图表展示
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(15, 12))
gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])

# --- 图1: 累计收益率对比 ---
ax1 = fig.add_subplot(gs[0])
# 计算策略的累计净值曲线 (近似)
# 策略当前净值 = (当前1万 + 累计取出 - 累计投入)
res_df['strategy_net_value'] = (TARGET_VALUE + res_df['total_cash_out'] - res_df['total_cash_in'])
# 归一化为收益率
res_df['strategy_cum_ret'] = res_df['strategy_net_value'] / res_df['total_cash_in']

# 计算持有的累计收益率
monthly_df['hold_cum_ret'] = (monthly_df['close'] - start_price) / start_price

ax1.plot(res_df.index, res_df['strategy_cum_ret'], color='#d62728', linewidth=2, label='恒定市值策略 (策略A)')
ax1.plot(monthly_df.index, monthly_df['hold_cum_ret'], color='#1f77b4', linestyle='--', label='买入持有策略 (策略B)')
ax1.axhline(0, color='gray', linewidth=0.5)
ax1.set_title('策略累计收益率对比', fontsize=14, fontweight='bold')
ax1.set_ylabel('累计收益率')
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax1.legend(loc='upper left')
ax1.grid(True, alpha=0.3)

# --- 图2: 每年现金流回报 (柱状图) ---
ax2 = fig.add_subplot(gs[1])
colors = ['#d62728' if x >= 0 else '#2ca02c' for x in yearly_stats]
bars = ax2.bar(yearly_stats.index, yearly_stats, color=colors, alpha=0.7)
ax2.set_title('年度现金流回报率 (正=净取出，负=净投入)', fontsize=12)
ax2.set_ylabel('年度回报率')
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax2.axhline(0, color='black', linewidth=0.8)
ax2.bar_label(bars, fmt='%.1f%%', padding=3)

# --- 图3: 累计投入本金变化 (最大资金压力) ---
ax3 = fig.add_subplot(gs[2])
ax3.fill_between(res_df.index, res_df['total_cash_in'], color='#ff7f0e', alpha=0.3)
ax3.plot(res_df.index, res_df['total_cash_in'], color='#ff7f0e', label='累计投入本金 (资金占用)')
ax3.axhline(TARGET_VALUE, color='gray', linestyle='--', label='初始本金 (1万)')
ax3.set_title('资金占用分析：你需要准备多少钱？', fontsize=12)
ax3.set_ylabel('金额 (元)')
ax3.legend(loc='upper left')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()