import pandas as pd
import plotly.graph_objs as go
import numpy as np
# 按 30 求均值，看均值线的变化
# ==========================================
# 1. 数据准备
# ==========================================
def load_and_prep_data():
    # 读取数据
    df = pd.read_json('sh510300.json')
    df['date'] = pd.to_datetime(df['date'], unit='ms')
    df = df.sort_values('date')
    
    # 为了演示效果明显，我们只取最后 100 天的数据
    # 这样动画不会太长，且能看清细节
    df_tail = df.iloc[:].copy().reset_index(drop=True)
    return df_tail

df = load_and_prep_data()

# ==========================================
# 2. 制作动画帧
# ==========================================
frames = []
# 我们从第 30 天开始模拟，直到最后一天
# 模拟每一天“收盘后”，我们重新计算均值的过程
start_idx = 3000
end_idx = len(df)

print(f"正在生成 {end_idx - start_idx} 帧动画数据，请稍候...")

for i in range(start_idx, end_idx + 1):
    # 1. 截取“当前”已知的数据 (模拟当时的情况)
    current_df = df.iloc[:i].copy()
    
    # 2. 基于当前已知数据，重新计算 30日中心均线
    # 注意：这里计算出的均线，在尾部是不稳定的
    current_df['ma30_dynamic'] = current_df['close'].rolling(window=30, center=True, min_periods=1).mean()
    
    # 3. 创建这一帧的数据
    # 我们需要更新两条线：股价线 和 均线
    frame = go.Frame(
        data=[
            # Trace 0: 股价线 (不断延长)
            go.Scatter(
                x=current_df['date'],
                y=current_df['close']
            ),
            # Trace 1: 均线 (不断延长且尾部会摆动)
            go.Scatter(
                x=current_df['date'],
                y=current_df['ma30_dynamic']
            ),
            # Trace 2: 当前日期的标记点 (红点)
            go.Scatter(
                x=[current_df['date'].iloc[-1]],
                y=[current_df['close'].iloc[-1]]
            )
        ],
        name=str(i) # 帧名称
    )
    frames.append(frame)

# ==========================================
# 3. 创建初始图表 (Base Figure)
# ==========================================
# 初始状态显示 start_idx 当天的数据
init_df = df.iloc[:start_idx].copy()
init_df['ma30_dynamic'] = init_df['close'].rolling(window=30, center=True, min_periods=1).mean()

fig = go.Figure(
    data=[
        # Trace 0: 股价
        go.Scatter(
            x=init_df['date'], y=init_df['close'],
            mode='lines', name='股价 (Close)',
            line=dict(color='#1f77b4', width=2)
        ),
        # Trace 1: 动态均线
        go.Scatter(
            x=init_df['date'], y=init_df['ma30_dynamic'],
            mode='lines', name='30日中心均线 (动态)',
            line=dict(color='#ff7f0e', width=3)
        ),
        # Trace 2: 当前点标记
        go.Scatter(
            x=[init_df['date'].iloc[-1]], y=[init_df['close'].iloc[-1]],
            mode='markers', name='当前日期',
            marker=dict(color='red', size=10)
        )
    ],
    frames=frames # 把刚才生成的帧塞进去
)

# ==========================================
# 4. 配置布局与播放按钮
# ==========================================
fig.update_layout(
    title='中心移动平均线(Centered MA) 的“重绘”现象演示',
    xaxis=dict(title='日期', range=[df['date'].iloc[0], df['date'].iloc[-1]]), # 固定X轴范围防止抖动
    yaxis=dict(title='价格', range=[df['close'].min()*0.95, df['close'].max()*1.05]), # 固定Y轴范围
    template='plotly_white',
    height=600,
    # 添加播放按钮
    updatemenus=[{
        'type': 'buttons',
        'showactive': False,
        'y': 1.15, 'x': 0.1,
        'buttons': [{
            'label': '▶️ 开始播放 (观察橙色线尾部的摆动)',
            'method': 'animate',
            'args': [None, {
                'frame': {'duration': 100, 'redraw': False}, # 每帧 100ms
                'fromcurrent': True,
                'transition': {'duration': 0}
            }]
        }]
    }]
)

# 显示图表
fig.show()