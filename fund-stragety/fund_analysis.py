import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
from datetime import timedelta

# ==========================================
# 1. 设置中文字体 (防止绘图乱码)
# ==========================================
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans', 'Liberation Sans', 'SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 数据处理与计算核心逻辑
# ==========================================

def load_data(json_file_path=None):
    """
    读取数据并转换为DataFrame。
    如果 json_file_path 为 None，则使用模拟数据。
    """
    if json_file_path:
        # 如果提供了文件路径，从JSON文件中读取数据
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # --- 模拟数据 (如果你没有文件，用这个测试) ---
        print("未提供文件路径，使用模拟数据...")
        # 使用预定义的数据列表作为模拟数据
        data = [
            {"净值日期": 1519862400000, "累计净值": 1.379},
            {"净值日期": 1522540800000, "累计净值": 1.450},
            {"净值日期": 1525132800000, "累计净值": 1.520}, # 高点
            {"净值日期": 1527811200000, "累计净值": 1.300}, # 大跌
            {"净值日期": 1530403200000, "累计净值": 1.250}, # 底部
            {"净值日期": 1533081600000, "累计净值": 1.400},
            {"净值日期": 1535760000000, "累计净值": 1.600}
        ]
        # ----------------------------------------

    # 使用读取的数据或模拟数据创建DataFrame
    df = pd.DataFrame(data)
    # 将毫秒时间戳转换为 datetime 对象，生成新的日期列 'date'
    df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
    # 将 '累计净值' 映射为新的列 'value'
    df['value'] = df['累计净值']
    # 按日期排序并重置索引，确保数据按时间顺序排列
    df = df.sort_values('date').reset_index(drop=True)
    return df[['date', 'value']]

def calculate_metrics(df_slice):
    """
    计算给定数据片段的指标：收益率、最大回撤、回撤持续时间
    """
    if df_slice.empty:
        return None

    # 1. 区间收益率
    start_val = df_slice.iloc[0]['value']
    end_val = df_slice.iloc[-1]['value']
    return_rate = (end_val - start_val) / start_val

    # 2. 最大回撤计算
    # 计算截止当前的累计最大值
    df_slice = df_slice.copy()
    df_slice['cummax'] = df_slice['value'].cummax()
    # 计算回撤率
    df_slice['drawdown'] = (df_slice['value'] - df_slice['cummax']) / df_slice['cummax']
    
    max_drawdown = df_slice['drawdown'].min() # 这是一个负数或0

    # 3. 动态回撤时间 (寻找最大回撤发生的 峰值日期 到 谷底日期)
    # 找到最大回撤发生的那个谷底的索引
    valley_idx = df_slice['drawdown'].idxmin()
    valley_date = df_slice.loc[valley_idx, 'date']
    
    # 在谷底之前，找到那个对应的最高点（cummax等于当时value的时刻）
    # 我们只看谷底之前的数据
    temp_before_valley = df_slice.loc[:valley_idx]
    # 找到最高点的位置 (即 cummax 第一次达到该值的位置，或者就是谷底对应的cummax值)
    peak_val = df_slice.loc[valley_idx, 'cummax']
    # 在谷底之前，最后一次出现这个最高点的时间
    peak_idx = temp_before_valley[temp_before_valley['value'] == peak_val].index[-1]
    peak_date = df_slice.loc[peak_idx, 'date']

    drawdown_days = (valley_date - peak_date).days

    return {
        'return_rate': return_rate,
        'max_drawdown': max_drawdown,
        'dd_start': peak_date,
        'dd_end': valley_date,
        'dd_days': drawdown_days
    }

# ==========================================
# 3. 可视化与交互逻辑
# ==========================================

def plot_fund_trend(df, start_date=None, end_date=None, recent_years=None):
    """
    绘制基金趋势图
    
    参数:
    df: 数据框，包含date和value列
    start_date: 起始日期，格式如 '2020-01-01' 或 datetime对象
    end_date: 结束日期，格式如 '2024-01-01' 或 datetime对象  
    recent_years: 只显示最近N年的数据，如 3 表示最近3年
    """
    
    # 数据筛选逻辑
    df_plot = df.copy()
    
    if recent_years:
        # 显示最近N年
        end_date = df_plot['date'].max()
        start_date = end_date - pd.DateOffset(years=recent_years)
        
    if start_date or end_date:
        # 应用日期筛选
        if start_date:
            if isinstance(start_date, str):
                start_date = pd.to_datetime(start_date)
            df_plot = df_plot[df_plot['date'] >= start_date]
            
        if end_date:
            if isinstance(end_date, str):
                end_date = pd.to_datetime(end_date)
            df_plot = df_plot[df_plot['date'] <= end_date]
    
    # 创建一个图形和子图
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # 绘制主曲线，显示累计净值
    line, = ax.plot(df_plot['date'], df_plot['value'], '-', label='累计净值', color='#1f77b4')
    
    # 格式化 X 轴日期显示
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))  # 设置日期格式
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # 自动定位日期
    
    # 设置图表标题及轴标签
    ax.set_title('基金净值走势 (请用鼠标在图表中框选区域)', fontsize=14)
    ax.set_xlabel('日期')
    ax.set_ylabel('累计净值')
    ax.grid(True, linestyle='--', alpha=0.5)  # 添加网格线
    
    # 用于显示结果的文本框，初始内容提示用户框选区域
    text_box = ax.text(0.02, 0.95, "请框选时间范围...", transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 高亮显示最大回撤区间的线段（初始化为空）
    dd_line, = ax.plot([], [], 'r--', linewidth=2, label='选中区域最大回撤段')

    # 定义框选结束后的回调函数
    def onselect(xmin, xmax):
        """
        当用户框选结束时触发的回调函数
        """
        # 将 matplotlib 的 float 日期转换为 pandas timestamp
        start_date = mdates.num2date(xmin).replace(tzinfo=None)  # 框选的起始日期
        end_date = mdates.num2date(xmax).replace(tzinfo=None)  # 框选的结束日期
        
        # 根据框选的时间范围筛选数据
        mask = (df_plot['date'] >= start_date) & (df_plot['date'] <= end_date)
        df_sub = df_plot.loc[mask]
        
        # 如果选中的数据不足以进行分析，给出提示
        if len(df_sub) < 2:
            text_box.set_text("选区数据太少，无法计算")
            fig.canvas.draw_idle()
            return

        # 计算选中区间的指标
        metrics = calculate_metrics(df_sub)
        
        if metrics:  # 如果指标计算成功
            # 更新文本框内容，显示分析结果
            msg = (
                f"选中范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
                f"---------------------------\n"
                f"区间收益率: {metrics['return_rate']:.2%}\n"  # 显示区间收益率
                f"最大回撤: {metrics['max_drawdown']:.2%}\n"  # 显示最大回撤
                f"回撤形成耗时: {metrics['dd_days']} 天\n"  # 回撤持续时间
                f"(从 {metrics['dd_start'].strftime('%Y-%m-%d')} 跌至 {metrics['dd_end'].strftime('%Y-%m-%d')})"
            )
            text_box.set_text(msg)
            
            # 将最大回撤的区间用红色虚线标记出来
            p1_x = metrics['dd_start']  # 最大回撤起点日期
            p1_y = df_sub[df_sub['date'] == metrics['dd_start']]['value'].values[0]  # 起点值
            p2_x = metrics['dd_end']  # 最大回撤终点日期
            p2_y = df_sub[df_sub['date'] == metrics['dd_end']]['value'].values[0]  # 终点值
            
            # 更新回撤线段的坐标
            dd_line.set_data([p1_x, p2_x], [p1_y, p2_y])
            
        else:  # 如果指标计算失败
            text_box.set_text("计算错误")

        fig.canvas.draw_idle()  # 更新图表

    # 创建 SpanSelector 工具，用于支持鼠标框选交互
    span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                        props=dict(alpha=0.3, facecolor='green'), interactive=True, drag_from_anywhere=True)

    # 添加图例，设置其位置
    plt.legend(loc='lower right')
    plt.show()
    
    # 保持 span 对象的引用，避免被垃圾回收导致交互失效
    return span
import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates

# ==========================================
# 1. 设置中文字体
# ==========================================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 数据处理
# ==========================================
def load_data(json_file_path=None):
    if json_file_path:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # 模拟数据
        data = [
            {"净值日期": 1519862400000, "累计净值": 1.379}, # 2018-03-01
            {"净值日期": 1522540800000, "累计净值": 1.450},
            {"净值日期": 1525132800000, "累计净值": 1.520},
            {"净值日期": 1527811200000, "累计净值": 1.300},
            {"净值日期": 1530403200000, "累计净值": 1.250},
            {"净值日期": 1533081600000, "累计净值": 1.400},
            {"净值日期": 1535760000000, "累计净值": 1.600}  # 2018-09-01
        ]

    df = pd.DataFrame(data)
    # 关键：将毫秒时间戳转为 datetime 对象
    df['date'] = pd.to_datetime(df['净值日期'], unit='ms')
    df['value'] = df['累计净值']
    df = df.sort_values('date').reset_index(drop=True)
    return df[['date', 'value']]

# ==========================================
# 3. 计算逻辑 (保持不变)
# ==========================================
def calculate_metrics(df_slice):
    if df_slice.empty: return None
    
    start_val = df_slice.iloc[0]['value']
    end_val = df_slice.iloc[-1]['value']
    return_rate = (end_val - start_val) / start_val

    df_slice = df_slice.copy()
    df_slice['cummax'] = df_slice['value'].cummax()
    df_slice['drawdown'] = (df_slice['value'] - df_slice['cummax']) / df_slice['cummax']
    max_drawdown = df_slice['drawdown'].min()

    valley_idx = df_slice['drawdown'].idxmin()
    valley_date = df_slice.loc[valley_idx, 'date']
    
    temp_before_valley = df_slice.loc[:valley_idx]
    peak_val = df_slice.loc[valley_idx, 'cummax']
    peak_idx = temp_before_valley[temp_before_valley['value'] == peak_val].index[-1]
    peak_date = df_slice.loc[peak_idx, 'date']
    
    drawdown_days = (valley_date - peak_date).days

    return {
        'return_rate': return_rate,
        'max_drawdown': max_drawdown,
        'dd_start': peak_date,
        'dd_end': valley_date,
        'dd_days': drawdown_days
    }

# ==========================================
# 4. 可视化 (关键修改部分)
# ==========================================
def plot_fund_trend(df):
    fig, ax = plt.subplots(figsize=(12, 6))
    
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
    
    # 信息显示框
    text_box = ax.text(0.02, 0.95, "请拖动鼠标框选时间范围...", transform=ax.transAxes, 
                       verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    # 回撤线
    dd_line, = ax.plot([], [], 'r--', linewidth=2, label='最大回撤区间')

    def onselect(xmin, xmax):
        # 将 float 日期转回 datetime
        start_date = mdates.num2date(xmin).replace(tzinfo=None)
        end_date = mdates.num2date(xmax).replace(tzinfo=None)
        
        # 边界保护：防止框选超出数据范围
        start_date = max(start_date, df['date'].min())
        end_date = min(end_date, df['date'].max())

        mask = (df['date'] >= start_date) & (df['date'] <= end_date)
        df_sub = df.loc[mask]
        
        if len(df_sub) < 2:
            return

        metrics = calculate_metrics(df_sub)
        
        if metrics:
            msg = (
                f"范围: {start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}\n"
                f"---------------------------\n"
                f"区间收益: {metrics['return_rate']:.2%}\n"
                f"最大回撤: {metrics['max_drawdown']:.2%}\n"
                f"回撤耗时: {metrics['dd_days']} 天"
            )
            text_box.set_text(msg)
            
            # 更新回撤线
            p1_x = metrics['dd_start']
            p1_y = df_sub[df_sub['date'] == metrics['dd_start']]['value'].values[0]
            p2_x = metrics['dd_end']
            p2_y = df_sub[df_sub['date'] == metrics['dd_end']]['value'].values[0]
            dd_line.set_data([p1_x, p2_x], [p1_y, p2_y])
            
        fig.canvas.draw_idle()

    # 创建交互工具
    span = SpanSelector(ax, onselect, 'horizontal', useblit=True,
                        props=dict(alpha=0.3, facecolor='green'), interactive=True, drag_from_anywhere=True)

    plt.legend(loc='lower right')
    plt.show()
    return span

# ==========================================
# 4. 主程序入口
# ==========================================
if __name__ == "__main__":
    # 替换为你的文件路径，例如: load_data('fund.json')
    df = load_data('data/fund_040026_history_add.json') 
    span_tool = plot_fund_trend(df)
