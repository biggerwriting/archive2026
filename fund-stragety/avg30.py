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
        # 1. 时间转换
        df['date'] = pd.to_datetime(df['date'], unit='ms')
        df = df.sort_values('date')
        df.set_index('date', inplace=True)

        # 2. 计算 30日均线 (MA30)
        # min_periods=1 表示初期数据不足30天时也计算平均值，避免空值
        df['ma30'] = df['close'].rolling(window=600, center=False, min_periods=1).mean()

        # 3. 生成中文星期字符串 (用于悬浮显示)
        # map: 0=周一, 6=周日
        week_map = {0:'星期一', 1:'星期二', 2:'星期三', 3:'星期四', 4:'星期五', 5:'星期六', 6:'星期日'}
        # 创建一列专门用于显示的日期格式： "2012-05-28 星期一"
        df['hover_date_str'] = df.index.strftime('%Y-%m-%d') + ' ' + df.index.dayofweek.map(week_map)

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
    
    # --- 第一条线：基金净值 (收盘价) ---
    fig.add_trace(go.Scatter(
        x=df.index, 
        y=df['close'],
        mode='lines',
        name='基金净值',
        # 将我们准备好的带星期的字符串传给 customdata
        customdata=df['hover_date_str'],
        line=dict(color='#1f77b4', width=1.5), # 蓝色
        # %{customdata} 代表取上面传入的数据
        hovertemplate='<b>%{customdata}</b><br>净值: %{y:.3f}<extra></extra>'
    ))

    # --- 第二条线：30日均线 (MA30) ---
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['ma30'],
        mode='lines',
        name='30日均线',
        customdata=df['hover_date_str'],
        line=dict(color='#ff7f0e', width=1.5, dash='solid'), # 橙色
        hovertemplate='<b>%{customdata}</b><br>MA30: %{y:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title='华泰柏瑞沪深300ETF (510300) 净值与均线分析',
        xaxis=dict(
            title='日期',
            rangeslider=dict(visible=True), 
            type='date'
        ),
        yaxis=dict(
            title='价格 (元)',
            fixedrange=False
        ),
        hovermode="x unified", # 开启统一悬浮提示（鼠标移动时同时显示两条线的数据）
        dragmode='zoom',
        template='plotly_white',
        height=600,
        legend=dict(
            orientation="h", # 图例水平放置
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    return fig

# ==========================================
# 3. 页面布局
# ==========================================
app.layout = html.Div([
    html.H1("基金净值回测分析看板", style={'textAlign': 'center', 'color': '#333'}),
    
    html.Div(id='stats-panel', style={
        'padding': '20px', 
        'backgroundColor': '#f9f9f9', 
        'border': '1px solid #ddd',
        'borderRadius': '5px',
        'margin': '10px 0',
        'fontSize': '16px',
        'lineHeight': '1.6'
    }, children="请在图表中框选或缩放以计算收益率..."),

    dcc.Graph(id='fund-graph', figure=create_figure())
])

# ==========================================
# 4. 交互逻辑 (回调函数)
# ==========================================
@callback(
    Output('stats-panel', 'children'),
    Input('fund-graph', 'relayoutData')
)
def update_stats(relayoutData):
    # 默认显示全量数据
    start_date = df.index[0]
    end_date = df.index[-1]
    trigger_mode = "全量历史数据"

    if relayoutData:
        if 'xaxis.range[0]' in relayoutData:
            start_str = relayoutData['xaxis.range[0]']
            end_str = relayoutData['xaxis.range[1]']
            start_date = pd.to_datetime(start_str).tz_localize(None)
            end_date = pd.to_datetime(end_str).tz_localize(None)
            trigger_mode = "自定义选区"
        elif 'xaxis.autorange' in relayoutData:
            trigger_mode = "全量历史数据 (重置)"

    # 截取数据
    mask = (df.index >= start_date) & (df.index <= end_date)
    sub_df = df.loc[mask]

    if sub_df.empty:
        return "所选范围内无交易数据。"

    first_day = sub_df.iloc[0]
    last_day = sub_df.iloc[-1]
    
    p_start = first_day['close']
    p_end = last_day['close']
    
    return_rate = (p_end - p_start) / p_start
    price_diff = p_end - p_start
    days = (sub_df.index[-1] - sub_df.index[0]).days

    style_color = 'red' if return_rate >= 0 else 'green'
    
    # 这里的 html.Span 已经修正为大写
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