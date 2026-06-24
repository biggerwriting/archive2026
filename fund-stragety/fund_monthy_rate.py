import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import os

# ==========================================
# 1. 数据读取与清洗
# ==========================================
FILE_PATH = 'sh510300.json'

if not os.path.exists(FILE_PATH):
    print(f"错误：找不到文件 {FILE_PATH}，请确保文件在当前目录下。")
    # 为了演示，生成一个假的测试文件（如果文件不存在）
    # (此处省略生成代码，假设用户已有文件)
    exit()

try:
    df = pd.read_json(FILE_PATH)
    # 转换时间戳
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    df = df.sort_values('date')
    df.set_index('date', inplace=True)
except Exception as e:
    print(f"数据读取失败: {e}")
    exit()

# ==========================================
# 2. 核心逻辑：日频转月频 (Resample)
# ==========================================
# 'ME' 代表 Month End (月末)，.last() 取该月最后一个有效数据
# 注意：pandas旧版本可能使用 'M'
monthly_df = df['close'].resample('ME').last().to_frame(name='close')

# 计算当月收益率 (Pct Change)
monthly_df['monthly_return'] = monthly_df['close'].pct_change()

# 计算当月年化收益率 (假设该月收益率维持12个月)
# 公式: (1 + r)^12 - 1
monthly_df['annualized_return'] = (1 + monthly_df['monthly_return']) ** 12 - 1

# 去除第一个月 (因为没有上个月的数据，收益率为 NaN)
monthly_df.dropna(inplace=True)

# 打印前几行看看数据
print("--- 月度数据预览 ---")
print(monthly_df.head())

# ==========================================
# 3. 绘图 (三轴图：条形图 + 双折线)
# ==========================================
# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

fig, ax1 = plt.subplots(figsize=(14, 8))

# --- 轴1 (左轴): 当月收益率 (条形图) ---
# 根据涨跌设置颜色：红涨绿跌
colors = ['#d62728' if x >= 0 else '#2ca02c' for x in monthly_df['monthly_return']]
ax1.set_xlabel('日期')
ax1.set_ylabel('当月收益率 (柱状图)', color='black', fontweight='bold')
# width=20 控制柱子宽度，根据数据量调整
bars = ax1.bar(monthly_df.index, monthly_df['monthly_return'], color=colors, width=20, label='当月收益率', alpha=0.6)
ax1.tick_params(axis='y', labelcolor='black')
ax1.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))
# 添加0轴线
ax1.axhline(y=0, color='gray', linewidth=1, linestyle='-')

# --- 轴2 (右轴1): 基金净值 (折线图) ---
ax2 = ax1.twinx()
color_nav = '#ff7f0e' # 橙色
ax2.set_ylabel('基金净值 (NAV)', color=color_nav, fontweight='bold')
line_nav = ax2.plot(monthly_df.index, monthly_df['close'], color=color_nav, linewidth=2.5, label='基金净值走势')
ax2.tick_params(axis='y', labelcolor=color_nav)

# --- 轴3 (右轴2): 当月年化收益率 (折线图) ---
ax3 = ax1.twinx()
# 将第三个轴向右平移 60 像素，避免重叠
ax3.spines["right"].set_position(("outward", 60))
color_ann = '#1f77b4' # 蓝色
ax3.set_ylabel('当月年化收益率 (折射情绪)', color=color_ann, fontweight='bold')
# 使用虚线，透明度低一点，因为这个数据波动很大
line_ann = ax3.plot(monthly_df.index, monthly_df['annualized_return'], color=color_ann, linestyle='--', linewidth=1, alpha=0.7, label='当月年化收益率')
ax3.tick_params(axis='y', labelcolor=color_ann)
ax3.yaxis.set_major_formatter(mtick.PercentFormatter(1.0))

# --- 限制 Y 轴范围 (可选，防止年化数据太夸张压缩了其他图形) ---
# 如果某个月涨了20%，年化就是800%，会把图拉得很丑，限制一下
ax3.set_ylim(-2, 2) # 限制在 -200% 到 200% 之间

# --- 合并图例 ---
# 柱状图的图例处理稍微特殊一点
lines = [bars] + line_nav + line_ann
labels = ['当月收益率 (左轴)', '基金净值 (右轴1)', '当月年化 (右轴2)']
ax1.legend(lines, labels, loc='upper left')

plt.title('沪深300ETF (510300) 月度绩效归因分析')
plt.grid(True, axis='x', alpha=0.3) # 只显示X轴网格
fig.tight_layout()
plt.show()