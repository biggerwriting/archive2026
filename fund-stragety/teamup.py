import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc  # 可选，用于美化布局
import plotly.graph_objs as go
import pandas as pd
import akshare as ak
import numpy as np

# ==========================================
# 1. 核心计算函数
# ==========================================

def detect_fund_type(code):
    """
    根据基金代码检测基金类型
    """
    # 移除可能的前缀
    clean_code = code.lower().replace('sh', '').replace('sz', '').replace('fund', '')
    
    # 股票ETF (51xxx, 15xxx)
    if clean_code.startswith(('51', '15')):
        return 'etf'
    
    # 债券ETF (511xxx, 159xxx等)
    if clean_code.startswith(('511', '159')) and len(clean_code) >= 6:
        return 'bond_etf'
    
    # 开放式基金 (通常为6位数字)
    if clean_code.isdigit() and len(clean_code) == 6:
        return 'open_fund'
    
    # 默认尝试ETF
    return 'etf'

def fetch_single_fund_data(code):
    """
    获取单个基金的数据，支持自动检测类型
    """
    fund_type = detect_fund_type(code)
    
    # 标准化代码格式
    original_code = code
    code = code.lower()
    
    # 尝试不同的数据获取方法
    methods_to_try = []
    
    if fund_type == 'etf' or fund_type == 'bond_etf':
        # ETF/Bond ETF 尝试新浪接口
        if not code.startswith(('sh', 'sz')):
            # 尝试添加前缀
            methods_to_try.extend([
                ('sina_etf', f"sh{code}"),
                ('sina_etf', f"sz{code}")
            ])
        else:
            methods_to_try.append(('sina_etf', code))
    
    # 开放式基金尝试其他接口
    if fund_type == 'open_fund':
        methods_to_try.extend([
            ('em_open_fund', original_code),
            ('em_fund_info', original_code)
        ])
    
    # 通用回退方法
    methods_to_try.extend([
        ('sina_etf', f"sh{code}"),
        ('sina_etf', f"sz{code}")
    ])
    
    for method, code_to_try in methods_to_try:
        try:
            if method == 'sina_etf':
                df = ak.fund_etf_hist_sina(symbol=code_to_try)
            elif method == 'em_open_fund':
                df = ak.fund_em_open_fund_info(fund=code_to_try, indicator="累计净值")
                df = df.rename(columns={'净值日期': 'date', '累计净值': 'close'})
            elif method == 'em_fund_info':
                df = ak.fund_em_open_fund_info(fund=code_to_try, indicator="单位净值")
                df = df.rename(columns={'净值日期': 'date', '单位净值': 'close'})
            
            if not df.empty and 'close' in df.columns and 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df.sort_index(inplace=True)
                print(f"✓ {original_code} 使用 {method} ({code_to_try}) 获取成功")
                return df['close']
                
        except Exception as e:
            continue
    
    return None

def fetch_data(codes):
    """
    批量获取基金数据并对齐日期，支持多种基金类型
    """
    data_dict = {}
    print(f"正在获取数据: {codes} ...")
    
    for code in codes:
        try:
            series = fetch_single_fund_data(code)
            if series is not None and not series.empty:
                data_dict[code] = series
            else:
                print(f"✗ 获取 {code} 失败: 无法获取有效数据")
                return None
        except Exception as e:
            print(f"✗ 获取 {code} 失败: {e}")
            return None

    if not data_dict:
        print("没有成功获取任何基金数据")
        return None

    # 合并数据 (inner join，只保留大家都有的日期)
    df_merged = pd.concat(data_dict.values(), axis=1, keys=data_dict.keys(), join='inner')
    df_merged.sort_index(inplace=True)
    print(f"✓ 成功获取 {len(data_dict)} 个基金的数据")
    return df_merged

def calculate_metrics(series):
    """
    计算序列的累计收益率和最大回撤
    """
    if series.empty:
        return 0.0, 0.0
    
    # 1. 累计收益率
    start_price = series.iloc[0]
    end_price = series.iloc[-1]
    total_return = (end_price - start_price) / start_price

    # 2. 最大回撤
    # 累计最大值
    roll_max = series.cummax()
    # 当前回撤
    drawdown = (series - roll_max) / roll_max
    # 最大回撤 (最小值)
    max_dd = drawdown.min()

    return total_return, max_dd

# ==========================================
# 2. Dash 应用初始化
# ==========================================
app = dash.Dash(__name__, title="基金组合回测工具")

# 全局变量缓存数据 (简单起见，生产环境应用 dcc.Store)
global_df = pd.DataFrame()

# ==========================================
# 3. 页面布局
# ==========================================
app.layout = html.Div([
    html.H1("基金组合策略回测看板", style={'textAlign': 'center', 'padding': '20px'}),

    # --- 控制面板 ---
    html.Div([
        html.Div([
            html.Label("基金代码 (逗号分隔, 支持多种格式):"),
            dcc.Input(id='input-codes', type='text', value='sh510300,sz159915', style={'width': '100%'}),
            html.Small("示例: ETF(sh510300/sz159915), 债基(040026), 支持自动识别")
        ], style={'width': '40%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            html.Label("持仓比例 (逗号分隔, 需对应):"),
            dcc.Input(id='input-weights', type='text', value='0.5,0.5', style={'width': '100%'}),
            html.Small("示例: 0.5,0.5 表示各买一半")
        ], style={'width': '40%', 'display': 'inline-block', 'padding': '10px'}),

        html.Button('开始回测', id='btn-run', n_clicks=0, style={'height': '50px', 'verticalAlign': 'top', 'marginTop': '25px'}),
    ], style={'backgroundColor': '#f0f0f0', 'padding': '20px', 'borderRadius': '10px', 'margin': '20px'}),

    # --- 状态提示 ---
    html.Div(id='status-msg', style={'textAlign': 'center', 'color': 'red'}),

    # --- 图表区域 ---
    dcc.Graph(id='main-chart'),

    # --- 统计表格区域 ---
    html.Div([
        html.H3("区间绩效统计 (请在图表上框选时间范围)", style={'textAlign': 'center'}),
        html.Div(id='stats-table-container')
    ], style={'padding': '20px'})
])

# ==========================================
# 4. 回调逻辑
# ==========================================

# 回调1: 点击按钮 -> 获取数据 -> 绘制全量图表
@app.callback(
    [Output('main-chart', 'figure'),
     Output('status-msg', 'children'),
     Output('stats-table-container', 'children')], # 初始加载也更新表格
    [Input('btn-run', 'n_clicks'),
     Input('main-chart', 'relayoutData')], # 监听图表缩放
    [State('input-codes', 'value'),
     State('input-weights', 'value')]
)
def update_dashboard(n_clicks, relayoutData, codes_str, weights_str):
    global global_df
    
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # --- 情况A: 点击了“开始回测”按钮 (重新获取数据) ---
    if trigger_id == 'btn-run' or (trigger_id == '' and n_clicks == 0):
        # 1. 解析输入
        codes = [c.strip() for c in codes_str.split(',')]
        try:
            weights = [float(w.strip()) for w in weights_str.split(',')]
        except:
            return dash.no_update, "权重格式错误", dash.no_update
        
        if len(codes) != len(weights):
            return dash.no_update, "基金数量与权重数量不一致", dash.no_update

        # 归一化权重 (确保和为1)
        weights = np.array(weights)
        weights = weights / weights.sum()

        # 2. 获取数据
        df = fetch_data(codes)
        if df is None or df.empty:
            return dash.no_update, "数据获取失败，请检查代码是否正确 (如 sh510300)", dash.no_update
        
        # 3. 计算组合净值 (归一化起步价为1)
        # 每一列除以第一行，变成净值走势 (1.0, 1.01, ...)
        df_norm = df / df.iloc[0]
        # 组合净值 = 各基金净值 * 权重 的和
        df['Strategy_Portfolio'] = (df_norm * weights).sum(axis=1) * df.iloc[0,0] # 乘回价格量级以便展示，或者直接用净值1.0开始
        # 为了直观，我们让策略曲线也从 1.0 开始展示
        df['Strategy_Portfolio'] = (df_norm * weights).sum(axis=1)

        # 同时也把单只基金转为净值 1.0 起步，方便在同一张图比较
        for col in codes:
            df[f"{col}_norm"] = df[col] / df[col].iloc[0]

        global_df = df # 更新全局缓存
        
        # 重置视图范围
        start_date = df.index[0]
        end_date = df.index[-1]
        
    # --- 情况B: 只是在图上缩放/框选 (使用现有数据) ---
    else:
        if global_df.empty:
            return dash.no_update, "请先点击开始回测", dash.no_update
        
        # 获取当前视图的时间范围
        start_date = global_df.index[0]
        end_date = global_df.index[-1]
        
        if relayoutData:
            if 'xaxis.range[0]' in relayoutData:
                start_date = pd.to_datetime(relayoutData['xaxis.range[0]'])
                end_date = pd.to_datetime(relayoutData['xaxis.range[1]'])
            elif 'xaxis.autorange' in relayoutData:
                pass # 重置

    # ==================================
    # 通用逻辑: 根据 start_date/end_date 计算指标并绘图
    # ==================================
    
    # 1. 截取数据
    mask = (global_df.index >= start_date) & (global_df.index <= end_date)
    sub_df = global_df.loc[mask]
    
    if sub_df.empty:
        return dash.no_update, "所选区间无数据", dash.no_update

    # 2. 计算指标表格
    stats_data = []
    
    # A. 策略组合
    ret, mdd = calculate_metrics(sub_df['Strategy_Portfolio'])
    stats_data.append({'名称': '★ 投资组合策略', '累计收益': f"{ret:.2%}", '最大回撤': f"{mdd:.2%}"})
    
    # B. 单只基金 (使用归一化后的列计算收益，回撤是一样的)
    # 原始代码列名在 global_df.columns[:len(codes)] 
    # 但我们用 _norm 列来画图，计算指标也可以用 _norm 列
    original_codes = [c.strip() for c in codes_str.split(',')]
    for code in original_codes:
        ret, mdd = calculate_metrics(sub_df[f"{code}_norm"])
        stats_data.append({'名称': code, '累计收益': f"{ret:.2%}", '最大回撤': f"{mdd:.2%}"})

    # 生成 HTML 表格
    table_header = [
        html.Thead(html.Tr([html.Th("名称"), html.Th("区间累计收益"), html.Th("区间最大回撤")]))
    ]
    table_body = [
        html.Tbody([
            html.Tr([
                html.Td(row['名称'], style={'fontWeight': 'bold' if '策略' in row['名称'] else 'normal'}),
                html.Td(row['累计收益'], style={'color': 'red' if '-' not in row['累计收益'] else 'green'}),
                html.Td(row['最大回撤'], style={'color': 'green'})
            ]) for row in stats_data
        ])
    ]
    stats_table = dbc.Table(table_header + table_body, bordered=True, hover=True, striped=True) if 'dbc' in globals() else html.Table(table_header + table_body, style={'width': '100%', 'textAlign': 'center', 'border': '1px solid #ddd'})

    # 3. 绘制图表 (只重绘一次，如果只是缩放，其实不需要重绘figure，只需要layout update，但为了简单这里重绘)
    # 注意：为了让用户在缩放时图表不重置，我们需要保持 layout 的 range
    fig = go.Figure()

    # 画策略线 (加粗)
    fig.add_trace(go.Scatter(
        x=global_df.index, y=global_df['Strategy_Portfolio'],
        mode='lines', name='★ 投资组合',
        line=dict(width=3, color='red')
    ))

    # 画单只基金线 (细线)
    for code in original_codes:
        fig.add_trace(go.Scatter(
            x=global_df.index, y=global_df[f"{code}_norm"],
            mode='lines', name=code,
            line=dict(width=1),
            opacity=0.6
        ))

    fig.update_layout(
        title=f"净值走势对比 (基准=1.0) | 当前区间: {start_date.date()} 至 {end_date.date()}",
        xaxis=dict(
            range=[start_date, end_date], # 关键：锁定视图范围
            rangeslider=dict(visible=True),
            type='date'
        ),
        yaxis=dict(title='累计净值', fixedrange=False),
        hovermode="x unified",
        template="plotly_white",
        height=500,
        dragmode='zoom' # 默认鼠标模式为框选
    )

    return fig, "计算完成", stats_table

# ==========================================
# 5. 启动服务
# ==========================================
if __name__ == '__main__':
    print("应用已启动，请访问: http://127.0.0.1:8050/")
    app.run(debug=True)