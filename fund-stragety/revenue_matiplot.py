import matplotlib.pyplot as plt
import numpy as np

# 数据
holdings = ['1天', '1周', '1月', '3月', '6月', '1年']
avg_return = [2.91, 14.36, 60.07, 193.09, 396.73, 741.23]
median_return = [0.00, 17.81, 39.14, 59.30, 110.86, 362.42]
max_loss = [-1000.52, -2205.38, -3473.43, -4224.59, -3245.61, -4173.27]
max_gain = [999.13, 2893.69, 3325.57, 5014.15, 10073.84, 14896.62]
win_rate = [49.49, 52.78, 52.92, 52.83, 52.49, 55.34]

x = np.arange(len(holdings))
width = 0.4

fig, ax1 = plt.subplots(figsize=(12, 7))

# --- 左轴：收益金额 ---
# 平均收益柱状图
bars = ax1.bar(x - width/2, avg_return, width, label='平均收益', color='#2878B5')
# 中位数收益柱状图（可改为散点+折线）
ax1.scatter(x, median_return, s=80, color='#F39C12', zorder=5, label='收益中位数')
ax1.plot(x, median_return, color='#F39C12', linestyle='--', alpha=0.7)

# 误差线：最大亏损 ~ 最大收益
for i in range(len(x)):
    # 亏损段（红色）
    ax1.vlines(x[i], max_loss[i], 0, colors='#E74C3C', alpha=0.5, linewidth=2)
    # 盈利段（绿色）
    ax1.vlines(x[i], 0, max_gain[i], colors='#2ECC71', alpha=0.5, linewidth=2)
    # 端点标记
    ax1.plot(x[i], max_loss[i], 'rv', markersize=6)
    ax1.plot(x[i], max_gain[i], 'g^', markersize=6)

ax1.set_ylabel('收益金额（元）', fontsize=12)
ax1.set_xlabel('持有期', fontsize=12)
ax1.set_xticks(x)
ax1.set_xticklabels(holdings)
ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.5)

# 平均收益数值标注
for i, v in enumerate(avg_return):
    ax1.text(i - width/2, v + 30, f'{v:.0f}', ha='center', va='bottom', fontsize=9)

# --- 右轴：正收益概率 ---
ax2 = ax1.twinx()
ax2.plot(x, win_rate, color='#27AE60', marker='o', linewidth=3, label='正收益概率')
ax2.set_ylabel('正收益概率（%）', fontsize=12)
ax2.set_ylim(45, 60)
ax2.grid(False)

# 概率数值标注
for i, v in enumerate(win_rate):
    ax2.text(i, v + 0.8, f'{v:.1f}%', ha='center', va='bottom', fontsize=10, color='#27AE60')

# --- 图例与标题 ---
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('不同持有期投资1万元沪深300ETF的收益风险特征\n（基于历史滚动持有模拟）', 
          fontsize=14, fontweight='bold', pad=20)

# 添加核心洞察文本框
insight_text = "🔍 关键洞察：\n"
insight_text += "• 持有1年期望收益741元，胜率55.3%，显著优于短期\n"
insight_text += "• 最大亏损并未随持有期同步放大（1年＜3月）\n"
insight_text += "• 收益分布右偏：平均＞中位数，少数大涨贡献主要收益"
plt.text(0.02, 0.02, insight_text, transform=plt.gcf().transFigure,
         fontsize=10, verticalalignment='bottom',
         bbox=dict(boxstyle='round', facecolor='#FEF9E7', alpha=0.9))

plt.tight_layout()
plt.show()