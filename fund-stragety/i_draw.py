import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
from datetime import timedelta
import matplotlib.ticker as ticker


# 中文字体设置
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


# ==========================================
# 2. 数据处理
# ==========================================
def load_data(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
      

    df = pd.DataFrame(data)
    # 关键：将毫秒时间戳转为 datetime 对象
    df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
    df['value'] = df['累计净值']
    df = df.sort_values('date').reset_index(drop=True)

    # --- 核心：计算全历史的动态回撤曲线 ---
    # 1. 计算截止当前的累计最大值
    df['cummax'] = df['value'].cummax()
    # 2. 计算回撤幅度 (当前值 - 历史高点) / 历史高点
    df['drawdown'] = (df['value'] - df['cummax']) / df['cummax']

    return df

# ==========================================
# 3. 选区指标计算逻辑
# ==========================================
def calculate_metrics(df_slice):
    """
    计算选中区间的特定指标。
    注意：这里的最大回撤是基于“选中区间内”的最高点计算的，
    而不是基于全历史最高点（这符合区间分析的逻辑）。
    """
    if df_slice.empty or len(df_slice) < 2:
        return None

    # 1. 区间收益率
    start_val = df_slice.iloc[0]['value']
    end_val = df_slice.iloc[-1]['value']
    return_rate = (end_val - start_val) / start_val

    # 2. 区间内最大回撤
    # 在这个局部区间内，重新计算cummax
    local_cummax = df_slice['value'].cummax()
    local_drawdown = (df_slice['value'] - local_cummax) / local_cummax
    max_drawdown = local_drawdown.min()

    # 3. 寻找最大回撤的起止时间
    valley_idx = local_drawdown.idxmin() # 坑底索引
    valley_date = df_slice.loc[valley_idx, 'date']
    
    # 找坑底对应的峰值
    # 只看坑底之前的数据
    temp_before = df_slice.loc[:valley_idx]
    peak_val = local_cummax.loc[valley_idx]
    # 找到最后一次出现该峰值的索引
    peak_idx = temp_before[temp_before['value'] == peak_val].index[-1]
    peak_date = df_slice.loc[peak_idx, 'date']
    
    dd_days = (valley_date - peak_date).days

    return {
        'return_rate': return_rate,
        'max_drawdown': max_drawdown,
        'dd_start': peak_date,
        'dd_end': valley_date,
        'dd_days': dd_days,
        'start_val': start_val,
        'end_val': end_val
    }


# ==========================================
# 4. 可视化 (关键修改部分)
# ==========================================
def plot_fund_trend(df):
    
    # 创建两个子图：上图占3份高度，下图占1份高度
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, 
                                   gridspec_kw={'height_ratios': [3, 1]})
    plt.subplots_adjust(hspace=0.05) # 减小子图间距

    # 绘制主曲线
    ax.plot(df['date'], df['value'], '-', label='累计净值', color='#1f77b4', linewidth=1)
    
    # --- 关键修改 1: 强制设置 X 轴范围 ---
    # 使用数据的第一个日期和最后一个日期作为边界
    ax.set_xlim(df['date'].min(), df['date'].max())
    
    # --- 关键修改 2: 优化日期显示格式 ---
    # 设置日期格式为 年-月-日
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    # 自动调整刻度密度
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    # 自动旋转日期标签，防止重叠
    fig.autofmt_xdate()

    ax.set_title('基金净值走势分析', fontsize=14)
    ax.set_ylabel('累计净值')
    ax.grid(True, linestyle='--', alpha=0.5)

     
    # 初始化：用于显示选区最大回撤的连线
    dd_line, = ax.plot([], [], 'g--', linewidth=2, marker='o', label='选区最大回撤段')
    
    # 信息展示框
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.9)
    text_box = ax.text(0.02, 0.90, "请在图中拖动鼠标框选...", transform=ax.transAxes, 
                        verticalalignment='top', bbox=props, fontsize=10)

    # -----------------------------
    # 下图：动态回撤曲线 (Drawdown)
    # -----------------------------
    ax2.plot(df['date'], df['drawdown'], color='gray', linewidth=1, alpha=0.8)
    # 填充颜色：0轴以下填充红色
    ax2.fill_between(df['date'], df['drawdown'], 0, color='red', alpha=0.1, label='水下幅度')
    
    ax2.set_ylabel('回撤幅度', fontsize=12)
    ax2.set_xlabel('日期', fontsize=12)
    
    # 格式化Y轴为百分比
    ax2.yaxis.set_major_formatter(ticker.PercentFormatter(xmax=1, decimals=0))
    # 添加0轴线
    ax2.axhline(0, color='black', linewidth=1, linestyle='-')
    
    # 格式化X轴日期
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    fig.autofmt_xdate()

    plt.legend(loc='lower right')


    # 强制设置X轴范围
    ax.set_xlim(df['date'].min(), df['date'].max())

    # -----------------------------
    # 交互逻辑
    # -----------------------------
    def onselect(xmin, xmax):
        # 转换时间
        start_date = mdates.num2date(xmin).replace(tzinfo=None)
        end_date = mdates.num2date(xmax).replace(tzinfo=None)
        
        # 边界修正
        start_date = max(start_date, df['date'].min())
        end_date = min(end_date, df['date'].max())

        # 筛选数据
        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df_sub = df.loc[mask]
        
        metrics = calculate_metrics(df_sub)
        
        if metrics:
            # 更新文本
            msg = (
                f"【选定区间分析】\n"
                f"时间: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
                f"区间收益率: {metrics['return_rate']:.2%}\n"
                f"区间最大回撤: {metrics['max_drawdown']:.2%}\n"
                f"回撤形成耗时: {metrics['dd_days']} 天\n"
                f"(高点: {metrics['dd_start'].strftime('%Y-%m-%d')} -> 低点: {metrics['dd_end'].strftime('%Y-%m-%d')})"
            )
            text_box.set_text(msg)
            
            # 在主图上画出最大回撤的那一段
            p1_x = metrics['dd_start']
            p1_y = df_sub[df_sub['date'] == metrics['dd_start']]['value'].values[0]
            p2_x = metrics['dd_end']
            p2_y = df_sub[df_sub['date'] == metrics['dd_end']]['value'].values[0]
            
            dd_line.set_data([p1_x, p2_x], [p1_y, p2_y])
            
            # 可选：在副图高亮选区（这里选择不操作副图，保持副图展示全貌更清晰）
        
        fig.canvas.draw_idle()

    # 创建选区工具 (只在 ax1 主图上操作)
    span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                        props=dict(alpha=0.3, facecolor='#2ca02c'), 
                        interactive=True, drag_from_anywhere=True)

    plt.show()

if __name__ == "__main__":
    # 替换为你的文件路径，例如: load_data('fund.json')
    df = load_data('data/fund_040026_history_add.json') 
    plot_fund_trend(df)