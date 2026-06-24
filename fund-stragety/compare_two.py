import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import os

# ==========================================
# 1. 设置中文字体 (响应您的设置)
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
plt.style.use('seaborn-v0_8-whitegrid')

# ==========================================
# 2. 数据读取与预处理
# ==========================================
def load_data(file_path, name):
    """读取单个文件并返回处理好的DataFrame"""
    if not os.path.exists(file_path):
        print(f"警告: 文件 {file_path} 不存在，生成模拟数据用于演示...")
        return generate_mock_data(name) # 仅用于演示，实际会读取文件

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    df = pd.DataFrame(data)
    
    # 检查日期格式并相应处理
    sample_date = df['净值日期'].iloc[0]
    if isinstance(sample_date, (int, float)) and sample_date > 1000000000:
        # 如果是大数字，视为毫秒时间戳
        df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
    else:
        # 否则视为字符串日期格式
        df['date'] = pd.to_datetime(df['净值日期'])
    
    df = df.sort_values('date').reset_index(drop=True)
    
    # 提取关键列并重命名，方便后续合并
    # 检查可用的净值列名
    if '累计净值' in df.columns:
        value_col = '累计净值'
    elif '单位净值' in df.columns:
        value_col = '单位净值'
    else:
        # 如果都没有，显示可用列名并退出
        available_cols = list(df.columns)
        raise ValueError(f"数据文件中没有找到净值列，可用列: {available_cols}")
    
    return df[['date', value_col]].rename(columns={value_col: 'value'})

def generate_mock_data(seed_name):
    """生成模拟数据（仅当文件不存在时调用）"""
    import numpy as np
    dates = pd.date_range(start='2019-01-01', periods=800, freq='D')
    np.random.seed(42 if '040026' in seed_name else 1)
    returns = np.random.normal(0.0005, 0.015, len(dates))
    values = np.cumprod(1 + returns)
    return pd.DataFrame({'date': dates, 'value': values})

def process_comparison_data(file1, file2):
    """
    核心逻辑：读取两个文件，按日期取交集，并计算全量回撤
    """
    # 1. 读取数据
    df1 = load_data(file1, "Fund A")
    df2 = load_data(file2, "Fund B")

    # 2. 合并数据 (Inner Join 取交集，确保时间轴完全对齐)
    print(f"合并前: df1有{len(df1)}条记录，df2有{len(df2)}条记录")
    print(f"df1日期范围: {df1['date'].min()} 到 {df1['date'].max()}")
    print(f"df2日期范围: {df2['date'].min()} 到 {df2['date'].max()}")
    
    df_merge = pd.merge(df1, df2, on='date', suffixes=('_A', '_B'), how='inner')
    
    print(f"合并后: 有{len(df_merge)}条记录")
    
    if df_merge.empty:
        print("数据合并结果为空，检查具体原因...")
        print(f"df1前5个日期: {df1['date'].head(5).tolist()}")
        print(f"df2前5个日期: {df2['date'].head(5).tolist()}")
        
        # 检查是否有任何重合
        df1_set = set(df1['date'])
        df2_set = set(df2['date'])
        common = df1_set & df2_set
        print(f"实际重合日期数量: {len(common)}")
        
        raise ValueError("两个基金没有重合的时间段，无法对比！")

    # 3. 归一化处理 (Rebase)
    # 让两只基金在起点都变成 1.0，方便对比走势
    df_merge['norm_A'] = df_merge['value_A'] / df_merge['value_A'].iloc[0]
    df_merge['norm_B'] = df_merge['value_B'] / df_merge['value_B'].iloc[0]

    # 4. 计算全历史动态回撤 (基于原始净值计算即可，比例是一样的)
    for suffix in ['_A', '_B']:
        col_val = f'value{suffix}'
        col_dd = f'drawdown{suffix}'
        cummax = df_merge[col_val].cummax()
        df_merge[col_dd] = (df_merge[col_val] - cummax) / cummax

    return df_merge

# ==========================================
# 3. 选区指标计算
# ==========================================
def calculate_segment_metrics(df_slice, suffix):
    """计算特定片段的指标"""
    if df_slice.empty: return None
    
    val_col = f'value{suffix}'
    
    # 1. 区间收益率
    start_val = df_slice[val_col].iloc[0]
    end_val = df_slice[val_col].iloc[-1]
    ret = (end_val - start_val) / start_val
    
    # 2. 区间最大回撤
    local_cummax = df_slice[val_col].cummax()
    local_dd = (df_slice[val_col] - local_cummax) / local_cummax
    max_dd = local_dd.min()
    
    return ret, max_dd

# ==========================================
# 4. 可视化主程序
# ==========================================
def plot_comparison(df):
    # 定义两只基金的名称和颜色
    name_A = "基金 040026"
    name_B = "基金 510300"
    color_A = '#1f77b4' # 蓝
    color_B = '#ff7f0e' # 橙

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 9), sharex=True, 
                                   gridspec_kw={'height_ratios': [3, 1.2]})
    plt.subplots_adjust(hspace=0.05)

    # -----------------------------
    # 上图：归一化走势对比
    # -----------------------------
    ax1.plot(df['date'], df['norm_A'], color=color_A, lw=1.5, label=f'{name_A} (归一化)')
    ax1.plot(df['date'], df['norm_B'], color=color_B, lw=1.5, label=f'{name_B} (归一化)')
    
    ax1.set_title(f'基金走势对比: {name_A} vs {name_B}', fontsize=16, fontweight='bold')
    ax1.set_ylabel('累计收益 (起点=1.0)', fontsize=12)
    ax1.legend(loc='upper left', frameon=True, fancybox=True, framealpha=0.9)
    ax1.grid(True, linestyle='--', alpha=0.5)

    # 信息展示框 (使用等宽字体对齐)
    props = dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray')
    text_box = ax1.text(0.02, 0.85, "请拖动鼠标框选区域...", transform=ax1.transAxes, 
                        verticalalignment='top', bbox=props, fontsize=11, family='monospace')

    # -----------------------------
    # 下图：双回撤曲线对比
    # -----------------------------
    # 基金A的回撤 (填充)
    ax2.fill_between(df['date'], df['drawdown_A'], 0, color=color_A, alpha=0.3, label=f'{name_A} 回撤')
    ax2.plot(df['date'], df['drawdown_A'], color=color_A, lw=1, alpha=0.8)
    
    # 基金B的回撤 (填充)
    ax2.fill_between(df['date'], df['drawdown_B'], 0, color=color_B, alpha=0.3, label=f'{name_B} 回撤')
    ax2.plot(df['date'], df['drawdown_B'], color=color_B, lw=1, alpha=0.8)

    ax2.set_ylabel('回撤幅度', fontsize=12)
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
    ax2.legend(loc='lower left', fontsize=9)
    ax2.grid(True, linestyle='--', alpha=0.5)
    
    # 日期格式化
    ax1.set_xlim(df['date'].min(), df['date'].max())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    # -----------------------------
    # 交互逻辑
    # -----------------------------
    def onselect(xmin, xmax):
        start_date = mdates.num2date(xmin).replace(tzinfo=None)
        end_date = mdates.num2date(xmax).replace(tzinfo=None)
        
        # 边界修正
        start_date = max(start_date, df['date'].min())
        end_date = min(end_date, df['date'].max())

        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df_sub = df.loc[mask]
        
        if len(df_sub) < 2: return

        # 计算两只基金的指标
        ret_A, dd_A = calculate_segment_metrics(df_sub, '_A')
        ret_B, dd_B = calculate_segment_metrics(df_sub, '_B')
        
        # 格式化输出文本
        msg = (
            f"【区间对比】 {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
            f"{'-'*45}\n"
            f"指标          | {name_A:<10} | {name_B:<10}\n"
            f"{'-'*45}\n"
            f"区间收益率    | {ret_A:>10.2%}   | {ret_B:>10.2%}\n"
            f"区间最大回撤  | {dd_A:>10.2%}   | {dd_B:>10.2%}\n"
            f"{'-'*45}\n"
            f"收益差额      | {(ret_A - ret_B):>+10.2%} (A - B)"
        )
        text_box.set_text(msg)
        fig.canvas.draw_idle()

    # 创建选区工具
    span = SpanSelector(ax1, onselect, 'horizontal', useblit=True,
                        props=dict(alpha=0.3, facecolor='gold'), 
                        interactive=True, drag_from_anywhere=True)

    plt.show()
    return span

if __name__ == "__main__":
    # 定义文件路径
    file_path_1 = 'data/fund_040026_history.json'
    file_path_2 = 'data/fund_510300_history.json'
    
    try:
        print("正在加载并对齐数据...")
        df_all = process_comparison_data(file_path_1, file_path_2)
        print(f"数据加载完成，共 {len(df_all)} 个重合交易日。")
        span_tool = plot_comparison(df_all)
    except Exception as e:
        print(f"发生错误: {e}")
        import traceback
        traceback.print_exc()