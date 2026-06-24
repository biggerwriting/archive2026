import json
import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output, callback

# ==========================================
# 1. 数据加载与预处理
# ==========================================
def load_data():
    file_path = 'sh510300_hist_sina.json'
    try:
        df = pd.read_json(file_path)
        # 将毫秒时间戳转换为 datetime
        df['date'] = pd.to_datetime(df['date'], unit='ms')
        # 按日期排序
        df = df.sort_values('date')
        # 设置日期为索引，方便后续按时间切片查询
        df.set_index('date', inplace=True)
        return df
    except Exception as e:
        print(f"读取文件失败: {e}")
        return pd.DataFrame()

df = load_data()

# ==========================================
# 2. 初始化 Dash 应用
# ==========================================
app = Dash(__name__)

# 创建基础图表
def create_figure():
    fig = go.Figure()
    
    # 添加收盘价折线
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['close'],
        mode='lines',
        name='基金净值(收盘价)',
        line=dict(color='#1f77b4', width=1.5),
        hovertemplate='<b>日期</b>: %{x|%Y-%m-%d}<br><b>净值</b>: %{y:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title='华泰柏瑞沪深300ETF (510300) 历史净值趋势',
        xaxis=dict(
            title='日期',
            rangeslider=dict(visible=True), # 显示底部的范围滑块
            type='date'
        ),
        yaxis=dict(
            title='单位净值 (元)',
            fixedrange=False # 允许Y轴缩放
        ),
        hovermode="x unified", # 鼠标移动时显示竖线和数据
        dragmode='zoom',       # 默认鼠标交互模式为框选缩放
        template='plotly_white',
        height=600
    )
    return fig

# ==========================================
# 3. 页面布局
# ==========================================
app.layout = html.Div([
    # 标题区域
    html.H1("基金净值回测分析看板", style={'textAlign': 'center', 'color': '#333'}),
    
    # 统计信息面板 (悬浮在图表上方或下方)
    html.Div(id='stats-panel', style={
        'padding': '20px', 
        'backgroundColor': '#f9f9f9', 
        'border': '1px solid #ddd',
        'borderRadius': '5px',
        'margin': '10px 0',
        'fontSize': '16px',
        'lineHeight': '1.6'
    }, children="请在图表中框选或缩放以计算收益率..."),

    # 图表区域
    dcc.Graph(id='fund-graph', figure=create_figure())
])

# ==========================================
# 4. 交互逻辑 (回调函数)
# ==========================================
@callback(
    Output('stats-panel', 'children'),
    Input('fund-graph', 'relayoutData') # 监听图表的布局变化(缩放/框选)
)
def update_stats(relayoutData):
    # 默认显示全量数据
    start_date = df.index[0]
    end_date = df.index[-1]
    trigger_mode = "全量历史数据"

    # 如果用户进行了缩放或框选
    if relayoutData:
        # 情况A: 使用了 X轴 范围缩放 (Box Select 或 Range Slider)
        if 'xaxis.range[0]' in relayoutData:
            start_str = relayoutData['xaxis.range[0]']
            end_str = relayoutData['xaxis.range[1]']
            # Plotly 返回的可能是字符串，需要转换
            start_date = pd.to_datetime(start_str).tz_localize(None) # 去除时区信息防止报错
            end_date = pd.to_datetime(end_str).tz_localize(None)
            trigger_mode = "自定义选区"
        
        # 情况B: 用户点击了 "Reset Axes" (重置)
        elif 'xaxis.autorange' in relayoutData:
            trigger_mode = "全量历史数据 (重置)"

    # --- 核心计算逻辑 ---
    # 在 DataFrame 中截取这段时间的数据
    # 使用 searchsorted 找到最近的交易日索引（防止选中的日期是非交易日）
    mask = (df.index >= start_date) & (df.index <= end_date)
    sub_df = df.loc[mask]

    if sub_df.empty:
        return "所选范围内无交易数据。"

    # 获取区间内的起止数据
    first_day = sub_df.iloc[0]
    last_day = sub_df.iloc[-1]
    
    p_start = first_day['close']
    p_end = last_day['close']
    
    # 计算收益率
    return_rate = (p_end - p_start) / p_start
    price_diff = p_end - p_start
    days = (sub_df.index[-1] - sub_df.index[0]).days

    # 样式化输出
    style_color = 'red' if return_rate >= 0 else 'green'
    
    return html.Div([
        html.Strong(f"【{trigger_mode}】 "),
        html.Span(f"{sub_df.index[0].strftime('%Y-%m-%d')} 至 {sub_df.index[-1].strftime('%Y-%m-%d')} ({days}天)"),
        html.Br(),
        "期初净值: ", html.Strong(f"{p_start:.3f}"), " 元",
        html.Span(" | ", style={'margin': '0 10px'}),
        "期末净值: ", html.Strong(f"{p_end:.3f}"), " 元",
        html.Br(),
        "区间盈亏: ", html.Strong(f"{price_diff:+.3f}", style={'color': style_color}), " 元",
        html.Span(" | ", style={'margin': '0 10px'}),
        "区间收益率: ", 
        html.Strong(f"{return_rate:+.2%}", style={'color': style_color, 'fontSize': '20px'})
    ])

# ==========================================
# 5. 启动服务器
# ==========================================
if __name__ == '__main__':
    print("正在启动服务...")
    print("请在浏览器中访问: http://127.0.0.1:8050/")
    app.run(debug=True)