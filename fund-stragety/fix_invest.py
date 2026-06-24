import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. 配置参数
# ==========================================
FILE_PATH = 'sh510300_hist_sina.json'
START_DATE = '2012-05-28'
END_DATE = '2013-01-01'
DAILY_INVEST_MONEY = 10  # 每天定投金额（元）

# ==========================================
# 2. 数据加载与预处理
# ==========================================
try:
    # 读取 JSON 文件
    df = pd.read_json(FILE_PATH)
    
    # 将时间戳转换为 datetime 对象 (unit='ms' 是关键)
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    
    # 按日期排序（防止数据乱序影响回测）
    df = df.sort_values('date')
    
    # 筛选时间段
    mask = (df['date'] >= START_DATE) & (df['date'] <= END_DATE)
    df_test = df.loc[mask].copy()
    
    if df_test.empty:
        print("错误：筛选出的数据为空，请检查日期范围或源文件。")
        exit()
        
    print(f"--- 回测区间: {df_test['date'].iloc[0].date()} 至 {df_test['date'].iloc[-1].date()} ---")
    print(f"--- 交易天数: {len(df_test)} 天 ---")

except ValueError as e:
    print(f"数据读取失败: {e}")
    exit()

# ==========================================
# 3. 策略 A：每日定投 (DCA)
# ==========================================
# 逻辑：每天花 10 元，按收盘价买入对应份额
# 份额 = 金额 / 价格 (这里忽略手续费)
df_test['dca_shares'] = DAILY_INVEST_MONEY / df_test['close']

# 计算定投总数据
dca_total_cost = len(df_test) * DAILY_INVEST_MONEY  # 总投入本金
dca_total_shares = df_test['dca_shares'].sum()      # 总持有份额
final_price = df_test['close'].iloc[-1]             # 期末价格

dca_market_value = dca_total_shares * final_price   # 期末持仓市值
dca_return_rate = (dca_market_value - dca_total_cost) / dca_total_cost

# ==========================================
# 4. 策略 B：一次性买入 (Lump Sum / 不定投)
# ==========================================
# 逻辑：为了公平对比，假设我们在第一天就拥有了“定投的总本金”，并在第一天全仓买入
start_price = df_test['close'].iloc[0]

lump_sum_shares = dca_total_cost / start_price      # 第一天能买到的份额
lump_sum_market_value = lump_sum_shares * final_price
lump_sum_return_rate = (lump_sum_market_value - dca_total_cost) / dca_total_cost

# 标的本身的涨跌幅（仅供参考）
asset_change = (final_price - start_price) / start_price

# ==========================================
# 5. 输出结果对比
# ==========================================
print("\n" + "="*30)
print("       回测结果报告")
print("="*30)

print(f"总投入本金: {dca_total_cost:.2f} 元")
print(f"期初价格:   {start_price:.3f}")
print(f"期末价格:   {final_price:.3f}")
print("-" * 30)

# 策略 A 结果
print(f"【策略 A：每日定投】")
print(f"持有份额:   {dca_total_shares:.2f} 份")
print(f"期末市值:   {dca_market_value:.2f} 元")
print(f"收益率:     {dca_return_rate:.2%}  <-- 定投收益")

print("-" * 30)

# 策略 B 结果
print(f"【策略 B：一次性买入】(假设首日投入 {dca_total_cost} 元)")
print(f"持有份额:   {lump_sum_shares:.2f} 份")
print(f"期末市值:   {lump_sum_market_value:.2f} 元")
print(f"收益率:     {lump_sum_return_rate:.2%}  <-- 标的本身涨跌幅")

print("="*30)

# 简单的结论判断
if dca_return_rate > lump_sum_return_rate:
    print("结论: 在这段时间内，[定投] 跑赢了 [一次性买入]。")
    print("原因: 期间可能经历了下跌震荡，定投摊低了成本。")
else:
    print("结论: 在这段时间内，[一次性买入] 跑赢了 [定投]。")
    print("原因: 期间可能是单边上涨行情，越买越贵导致定投成本升高。")

# ==========================================
# 6. (可选) 可视化绘图
# ==========================================
# 计算每日累计收益率曲线
df_test['dca_cum_shares'] = df_test['dca_shares'].cumsum()
df_test['dca_cum_cost'] = (pd.Series(range(1, len(df_test)+1)) * DAILY_INVEST_MONEY).values
df_test['dca_value'] = df_test['dca_cum_shares'] * df_test['close']
df_test['dca_return_pct'] = (df_test['dca_value'] / df_test['dca_cum_cost']) - 1

# 标的本身涨跌幅曲线
df_test['asset_return_pct'] = (df_test['close'] / start_price) - 1

plt.figure(figsize=(10, 6))
plt.plot(df_test['date'], df_test['dca_return_pct'], label='DCA (Daily Invest)', color='red')
plt.plot(df_test['date'], df_test['asset_return_pct'], label='Lump Sum (Hold)', color='blue', linestyle='--')
plt.axhline(y=0, color='gray', linestyle='-', alpha=0.3)
plt.title(f'DCA vs Lump Sum ({START_DATE} to {END_DATE})')
plt.legend()
plt.grid(True)
plt.show()