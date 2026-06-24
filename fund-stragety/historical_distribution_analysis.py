import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# ==========================================
# 1. 设置中文字体
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

# ==========================================
# 2. 数据加载与预处理
# ==========================================
def load_data(csv_file):
    if not os.path.exists(csv_file):
        print(f"文件 {csv_file} 不存在")
        return pd.DataFrame()
    
    df = pd.read_csv(csv_file)
    df['date'] = pd.to_datetime(df['净值日期'])
    # 优先用累计净值，没有则用单位净值
    col = '累计净值' if '累计净值' in df.columns else '单位净值'
    df['value'] = df[col]
    df = df.sort_values('date').reset_index(drop=True)
    return df

# ==========================================
# 3. 核心统计逻辑
# ==========================================
def analyze_period(df, period_days, label):
    """
    计算特定持有期的统计数据
    period_days: 持有天数 (1=1天, 5=1周, 20=1月)
    """
    # 计算收益率：(当前净值 - N天前净值) / N天前净值
    # shift(period_days) 表示向前平移 N 行
    returns = df['value'].pct_change(period_days).dropna()
    
    # 1. 总体统计
    total_count = len(returns)
    if total_count == 0: return None
    
    # 2. 正收益 (赚钱)
    pos_rets = returns[returns > 0]
    prob_win = len(pos_rets) / total_count
    
    # 3. 负收益 (亏钱)
    neg_rets = returns[returns <= 0]
    prob_loss = len(neg_rets) / total_count
    
    # 4. 统计指标计算函数
    def get_stats(data_series):
        if len(data_series) == 0: return 0, 0, 0, 0
        mean_val = data_series.mean()
        median_val = data_series.median()
        # 使用 5% 和 95% 分位数来代表“常见区间”，排除极端值
        low_bound = data_series.quantile(0.05)
        high_bound = data_series.quantile(0.95)
        return mean_val, median_val, low_bound, high_bound

    pos_mean, pos_med, pos_low, pos_high = get_stats(pos_rets)
    neg_mean, neg_med, neg_low, neg_high = get_stats(neg_rets)
    
    # 5. 打印报告
    print(f"\n{'='*20} {label} (持有 {period_days} 个交易日) {'='*20}")
    print(f"【上涨概率】: {prob_win:.2%} ")
    print(f"   - 平均涨幅: {pos_mean:.2%}")
    print(f"   - 核心区间: {pos_low:.2%} 至 {pos_high:.2%} (涵盖90%的上涨情况)")
    
    print(f"【下跌概率】: {prob_loss:.2%} ")
    print(f"   - 平均跌幅: {neg_mean:.2%}")
    print(f"   - 核心区间: {neg_low:.2%} 至 {neg_high:.2%} (涵盖90%的下跌情况)")
    
    print(f"【盈亏比】: {abs(pos_mean/neg_mean):.2f} (即赚1次够亏几次)")
    
    return returns

# ==========================================
# 4. 可视化分布图
# ==========================================
def plot_distributions(ret_1d, ret_1w, ret_1m):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    bins = 50
    alpha = 0.7
    
    # 绘制直方图
    axes[0].hist(ret_1d, bins=bins, color='blue', alpha=alpha, density=True)
    axes[0].set_title('hold 1 day profits')
    
    axes[1].hist(ret_1w, bins=bins, color='orange', alpha=alpha, density=True)
    axes[1].set_title('hold 1 week profits')
    
    axes[2].hist(ret_1m, bins=bins, color='green', alpha=alpha, density=True)
    axes[2].set_title('hold 1 month profits')
    
    for ax in axes:
        ax.axvline(0, color='red', linestyle='--', linewidth=1.5, label='0轴')
        ax.set_xlabel('profit')
        ax.set_ylabel('frequency density')
        # 格式化X轴为百分比
        vals = ax.get_xticks()
        ax.set_xticklabels(['{:,.1%}'.format(x) for x in vals])
        ax.grid(True, linestyle='--', alpha=0.3)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    file_path = "data/fund_540010_akshare.csv"
    df = load_data(file_path)
    
    if not df.empty:
        print(f"数据范围: {df['date'].iloc[0].date()} 至 {df['date'].iloc[-1].date()}")
        print(f"总样本数: {len(df)} 天")
        
        # 分别计算并打印报告
        r1 = analyze_period(df, 1, "短期 - 1天")
        r5 = analyze_period(df, 5, "中期 - 1周")
        r20 = analyze_period(df, 20, "长期 - 1月")
        
        # 绘图
        plot_distributions(r1, r5, r20)