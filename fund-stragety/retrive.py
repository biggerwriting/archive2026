import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
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

# 重采样为月度数据
monthly_df = df['close'].resample('ME').last().to_frame()

# ==========================================
# 2. 策略回测引擎
# ==========================================
INITIAL_CAPITAL = 10000

# --- 策略 A：恒定市值 (Value Averaging) ---
# 逻辑：总财富 = 账户市值(1万) + 累计落袋现金(卖出-买入)
strat_a_wealth = []
strat_a_cash_flow = 0 # 累计净现金流 (正=赚的钱拿出来了，负=又投钱进去了)
shares_a = 0

# 初始建仓
p0 = monthly_df.iloc[0]['close']
shares_a = INITIAL_CAPITAL / p0
strat_a_cash_flow = -INITIAL_CAPITAL # 初始流出 10000
strat_a_wealth.append(INITIAL_CAPITAL) # 初始财富 10000

for date, row in monthly_df.iloc[1:].iterrows():
    price = row['close']
    current_val = shares_a * price
    
    # 目标是维持 10000 元市值
    diff = INITIAL_CAPITAL - current_val
    
    # 交易操作
    # diff > 0: 需要补仓 (买入)，现金流减少
    # diff < 0: 需要止盈 (卖出)，现金流增加
    shares_change = diff / price
    shares_a += shares_change
    
    # 记录现金流变动 (卖出得钱是+，买入花钱是-)
    # 注意：diff 是缺口，如果缺口是正的，我们要花钱买，所以 cash_flow 减去 diff
    # 如果缺口是负的(多了)，我们卖出换钱，cash_flow 加上 abs(diff)
    strat_a_cash_flow -= diff 
    
    # 计算当前“总财富” (股票市值 + 现金账户余额)
    # 股票市值永远是 10000 (除非最后清仓，这里简化为账面价值)
    # 但为了严谨，我们用 actual shares * price (会有微小误差) + cash flow
    # 这里的 cash flow 包含了初始投入的 -10000
    # 所以 Total Wealth = 当前市值(10000) + (累计卖出 - 累计买入 - 初始投入) + 初始本金补正
    # 简化公式：Total Wealth = 当前市值 + 累计净现金流(不含初始) 
    # 更直观的公式：净值 = (当前持仓市值) + (累计提现 - 累计追加 - 初始投入)
    # 我们定义 "Total Wealth" 为当前变现价值：
    # Wealth = 10000 (手里的票) + (strat_a_cash_flow + 10000) (口袋里的钱)
    # 解释：strat_a_cash_flow 是扣除初始1万后的累计进出。
    # 如果 strat_a_cash_flow 是 -2000，说明我又投了2000，总投入12000。
    # 此时财富 = 10000(票) - 2000(额外投入)？不对。
    # 正确逻辑：
    # 收益 = (当前市值 + 累计卖出) - (累计买入)
    # 收益 = 当前市值 + 累计净现金流
    # 总财富 = 初始本金 + 收益
    total_wealth = (shares_a * price) + (strat_a_cash_flow + INITIAL_CAPITAL)
    strat_a_wealth.append(total_wealth)

# --- 策略 B：买入持有 (Buy and Hold) ---
strat_b_wealth = []
shares_b = INITIAL_CAPITAL / p0

strat_b_wealth.append(INITIAL_CAPITAL)
for date, row in monthly_df.iloc[1:].iterrows():
    price = row['close']
    strat_b_wealth.append(shares_b * price)

# 合并数据
res = pd.DataFrame({
    'Strategy_A': strat_a_wealth,
    'Strategy_B': strat_b_wealth
}, index=monthly_df.index)

res['Year'] = res.index.year

# ==========================================
# 3. 指标计算
# ==========================================

# --- A. 年度收益计算 ---
# 每年收益 = 年末总财富 - 年初总财富
# 每年收益率 = (年末 - 年初) / 年初
yearly_stats = []
years = res['Year'].unique()

for year in years:
    df_year = res[res['Year'] == year]
    
    # 获取年初财富 (如果是第一年，取第一条；否则取上一年的最后一条)
    # 为了简化，我们取该年第一条和最后一条近似
    start_wealth_a = df_year.iloc[0]['Strategy_A']
    end_wealth_a = df_year.iloc[-1]['Strategy_A']
    
    start_wealth_b = df_year.iloc[0]['Strategy_B']
    end_wealth_b = df_year.iloc[-1]['Strategy_B']
    
    # 如果不是第一年，应该用去年的最后一天作为起点更精确
    # 这里为了代码简单，使用当年第一天作为基准
    
    profit_a = end_wealth_a - start_wealth_a
    ret_a = profit_a / start_wealth_a
    
    profit_b = end_wealth_b - start_wealth_b
    ret_b = profit_b / start_wealth_b
    
    yearly_stats.append({
        'Year': year,
        'Profit_A': profit_a,
        'Return_A': ret_a,
        'Profit_B': profit_b,
        'Return_B': ret_b
    })

yearly_df = pd.DataFrame(yearly_stats).set_index('Year')

# --- B. 最大回撤计算 ---
def calculate_mdd(series):
    # 累计最大值
    roll_max = series.cummax()
    # 当前回撤
    drawdown = (series - roll_max) / roll_max
    # 最大回撤
    max_drawdown = drawdown.min()
    return max_drawdown, drawdown

mdd_a, dd_curve_a = calculate_mdd(res['Strategy_A'])
mdd_b, dd_curve_b = calculate_mdd(res['Strategy_B'])

# ==========================================
# 4. 输出文字报告
# ==========================================
total_ret_a = (res.iloc[-1]['Strategy_A'] - INITIAL_CAPITAL) / INITIAL_CAPITAL
total_ret_b = (res.iloc[-1]['Strategy_B'] - INITIAL_CAPITAL) / INITIAL_CAPITAL

print("="*60)
print(f"策略对比报告 (初始本金: {INITIAL_CAPITAL}元)")
print("="*60)
print(f"{'指标':<15} | {'策略 A (恒定市值)':<18} | {'策略 B (买入持有)':<18}")
print("-" * 60)
print(f"{'期末总财富':<15} | {res.iloc[-1]['Strategy_A']:<18,.2f} | {res.iloc[-1]['Strategy_B']:<18,.2f}")
print(f"{'总收益率':<15} | {total_ret_a:<18.2%} | {total_ret_b:<18.2%}")
print(f"{'最大回撤':<15} | {mdd_a:<18.2%} | {mdd_b:<18.2%}")
print("-" * 60)

print("\n【年度表现对比】")
print(f"{'年份':<6} | {'A收益(元)':<10} | {'A收益率':<8} | {'B收益(元)':<10} | {'B收益率':<8} | {'胜出者'}")
print("-" * 75)
for year, row in yearly_df.iterrows():
    winner = "策略A" if row['Return_A'] > row['Return_B'] else "策略B"
    print(f"{year:<6} | {row['Profit_A']:<10.0f} | {row['Return_A']:<8.2%} | {row['Profit_B']:<10.0f} | {row['Return_B']:<8.2%} | {winner}")

# ==========================================
# 5. 绘图
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig = plt.figure(figsize=(14, 12))
gs = fig.add_gridspec(3, 1, height_ratios=[2, 1, 1])

# 图1: 总财富曲线
ax1 = fig.add_subplot(gs[0])
ax1.plot(res.index, res['Strategy_A'], color='#d62728', linewidth=2, label='策略A: 恒定市值 (总财富)')
ax1.plot(res.index, res['Strategy_B'], color='#1f77b4', linestyle='--', label='策略B: 买入持有 (总财富)')
ax1.set_title('总财富曲线对比 (Total Wealth Curve)', fontsize=14, fontweight='bold')
ax1.set_ylabel('总资产 (元)')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 图2: 年度收益率对比 (柱状图)
ax2 = fig.add_subplot(gs[1])
x = np.arange(len(yearly_df))
width = 0.35
rects1 = ax2.bar(x - width/2, yearly_df['Return_A'], width, label='策略A', color='#d62728', alpha=0.8)
rects2 = ax2.bar(x + width/2, yearly_df['Return_B'], width, label='策略B', color='#1f77b4', alpha=0.8)
ax2.set_ylabel('年度收益率')
ax2.set_title('年度收益率对比')
ax2.set_xticks(x)
ax2.set_xticklabels(yearly_df.index)
ax2.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax2.legend()
ax2.axhline(0, color='black', linewidth=0.5)

# 图3: 回撤曲线
ax3 = fig.add_subplot(gs[2])
ax3.plot(res.index, dd_curve_a, color='#d62728', label=f'策略A 回撤 (最大 {mdd_a:.2%})')
ax3.plot(res.index, dd_curve_b, color='#1f77b4', linestyle='--', label=f'策略B 回撤 (最大 {mdd_b:.2%})')
ax3.fill_between(res.index, dd_curve_a, 0, color='#d62728', alpha=0.1)
ax3.fill_between(res.index, dd_curve_b, 0, color='#1f77b4', alpha=0.1)
ax3.set_title('资产回撤对比 (Drawdown)', fontsize=12)
ax3.set_ylabel('回撤幅度')
ax3.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
ax3.legend()
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()