import dash
from dash import dcc, html, Input, Output, State, ALL, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import akshare as ak
import numpy as np
import json

# ==========================================
# 1. 核心数据获取 (支持全类型基金)
# ==========================================
def fetch_fund_data(codes):
    """
    获取基金历史净值 (支持股票、债券、ETF等所有开放式基金)
    使用东方财富接口: fund_open_fund_hist_em
    """
    data_dict = {}
    unique_codes = list(set(codes)) # 去重
    
    print(f"正在获取基金数据: {unique_codes} ...")
    
    for code in unique_codes:
        try:
            # period='after_adjustment' 表示复权净值(包含分红)，计算收益更准
            # 东方财富接口通常只需要6位数字代码，如 '110011', '510300'
            df = ak.fund_open_fund_hist_em(symbol=code, period="after_adjustment", adjust="1")
            
            # 数据清洗
            df['净值日期'] = pd.to_datetime(df['净值日期'])
            df.set_index('净值日期', inplace=True)
            df.sort_index(inplace=True)
            
            # 只取 '单位净值' 或 '累计净值'，这里复权后通常看累计
            # 接口返回列名: 净值日期, 单位净值, 累计净值, 日增长率...
            # 注意：akshare不同版本列名可能微调，这里取 '累计净值' 或 '单位净值'
            # 为了回测准确，我们优先用复权后的数据。如果接口返回的是复权数据，直接用单位净值即可
            col_name = '单位净值' if '单位净值' in df.columns else df.columns[0]
            data_dict[code] = df[col_name]
            
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
            continue

    if not data_dict:
        return None

    # 合并数据 (inner join 保证日期对齐)
    df_merged = pd.concat(data_dict.values(), axis=1, keys=data_dict.keys(), join='inner')
    return df_merged

def calculate_max_drawdown(series):
    roll_max = series.cummax()
    drawdown = (series - roll_max) / roll_max
    return drawdown.min()

# ==========================================
# 2. Dash 应用初始化
# ==========================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="全能基金策略回测")

# 全局缓存 (生产环境建议用 Redis 或 文件缓存)
CACHE_DF = pd.DataFrame()

# ==========================================
# 3. 页面布局
# ==========================================
app.layout = dbc.Container([
    # --- 标题 ---
    dbc.Row(html.H2("全能基金组合策略回测 (股票/债券/ETF)", className="text-center my-4")),

    # --- 存储组件 (Local Storage) ---
    dcc.Store(id='local-store-strategies', storage_type='local'), # 保存策略配置
    dcc.Store(id='session-data-status', storage_type='memory'),   # 触发数据更新

    dbc.Row([
        # --- 左侧：策略配置与保存 ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("1. 新建/保存策略"),
                dbc.CardBody([
                    html.Label("策略名称:"),
                    dbc.Input(id='input-strat-name', placeholder="例如: 股债平衡策略", className="mb-2"),
                    
                    html.Label("基金代码 (6位数字, 逗号分隔):"),
                    dbc.Input(id='input-codes', placeholder="例如: 110011, 510300", value="110011, 510300", className="mb-2"),
                    html.Small("支持: 易方达中小盘(110011), 沪深300ETF(510300), 债券基金等", className="text-muted"),
                    
                    html.Label("持仓比例 (逗号分隔):", className="mt-2"),
                    dbc.Input(id='input-weights', placeholder="例如: 0.5, 0.5", value="0.5, 0.5", className="mb-3"),
                    
                    dbc.Button("保存策略", id='btn-save', color="success", className="w-100"),
                    html.Div(id='save-msg', className="text-success mt-2 small")
                ])
            ], className="h-100")
        ], width=4),

        # --- 右侧：策略选择与对比 ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("2. 策略对比分析"),
                dbc.CardBody([
                    html.Label("选择要对比的策略 (多选):"),
                    dcc.Checklist(id='checklist-strategies', options=[], value=[], labelStyle={'display': 'block', 'margin': '5px'}),
                    
                    html.Hr(),
                    dbc.Button("开始回测对比", id='btn-run', color="primary", size="lg", className="w-100"),
                    html.Div(id='run-msg', className="text-danger mt-2 small")
                ])
            ], className="h-100")
        ], width=8)
    ]),

    # --- 图表区域 ---
    dbc.Row([
        dbc.Col([
            dcc.Loading(dcc.Graph(id='main-chart', style={'height': '600px'}))
        ])
    ], className="mt-4"),

    # --- 统计表格 ---
    dbc.Row([
        dbc.Col([
            html.H4("区间绩效统计 (框选图表以更新)", className="text-center mt-4"),
            html.Div(id='stats-table-container')
        ])
    ], className="mb-5")

], fluid=True)

# ==========================================
# 4. 回调逻辑
# ==========================================

# --- 回调1: 保存策略到 LocalStorage 并更新 Checklist ---
@app.callback(
    [Output('local-store-strategies', 'data'),
     Output('save-msg', 'children'),
     Output('checklist-strategies', 'options'),
     Output('checklist-strategies', 'value')],
    [Input('btn-save', 'n_clicks'),
     Input('local-store-strategies', 'data')], # 监听已有数据，用于初始化
    [State('input-strat-name', 'value'),
     State('input-codes', 'value'),
     State('input-weights', 'value')]
)
def manage_strategies(n_clicks, stored_data, name, codes_str, weights_str):
    # 初始化
    strategies = stored_data if stored_data else {}
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 如果是页面加载，仅刷新列表
    if trigger_id == 'local-store-strategies' or not ctx.triggered:
        options = [{'label': k, 'value': k} for k in strategies.keys()]
        return dash.no_update, "", options, dash.no_update

    # 如果是点击保存
    if not name or not codes_str or not weights_str:
        return dash.no_update, "请填写完整信息", dash.no_update, dash.no_update

    # 简单校验
    try:
        codes = [c.strip() for c in codes_str.replace('，', ',').split(',')]
        weights = [float(w) for w in weights_str.replace('，', ',').split(',')]
        if len(codes) != len(weights):
            return dash.no_update, "代码数量与权重数量不一致", dash.no_update, dash.no_update
    except:
        return dash.no_update, "格式错误", dash.no_update, dash.no_update

    # 保存
    strategies[name] = {'codes': codes, 'weights': weights}
    options = [{'label': k, 'value': k} for k in strategies.keys()]
    
    # 默认选中刚保存的
    return strategies, f"策略 '{name}' 已保存!", options, [name]

# --- 回调2: 点击运行 -> 获取所有相关数据 -> 绘图 ---
@app.callback(
    [Output('main-chart', 'figure'),
     Output('stats-table-container', 'children'),
     Output('run-msg', 'children')],
    [Input('btn-run', 'n_clicks'),
     Input('main-chart', 'relayoutData')],
    [State('checklist-strategies', 'value'),
     State('local-store-strategies', 'data')]
)
def update_chart(n_clicks, relayoutData, selected_strat_names, stored_strategies):
    global CACHE_DF
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    # 没有选择策略
    if not selected_strat_names:
        return go.Figure(), "请先选择策略", ""

    # --- 阶段A: 数据获取与计算 (点击按钮时触发) ---
    if trigger_id == 'btn-run':
        # 1. 收集所有需要用到的基金代码
        all_codes = set()
        for name in selected_strat_names:
            all_codes.update(stored_strategies[name]['codes'])
        
        # 2. 批量获取数据
        raw_df = fetch_fund_data(list(all_codes))
        if raw_df is None or raw_df.empty:
            return go.Figure(), "", "数据获取失败，请检查代码"

        # 3. 归一化处理 (所有基金从 1.0 开始)
        df_norm = raw_df / raw_df.iloc[0]

        # 4. 计算每个策略的净值曲线
        strategy_curves = pd.DataFrame(index=df_norm.index)
        
        for name in selected_strat_names:
            strat = stored_strategies[name]
            codes = strat['codes']
            weights = np.array(strat['weights'])
            # 归一化权重
            weights = weights / weights.sum()
            
            # 提取该策略涉及的基金列
            sub_df = df_norm[codes]
            # 计算组合净值
            strategy_curves[name] = (sub_df * weights).sum(axis=1)

        CACHE_DF = strategy_curves # 更新缓存
        start_date = CACHE_DF.index[0]
        end_date = CACHE_DF.index[-1]

    # --- 阶段B: 视图更新 (点击按钮 或 缩放图表时触发) ---
    else:
        if CACHE_DF.empty:
            return dash.no_update, dash.no_update, dash.no_update
        
        start_date = CACHE_DF.index[0]
        end_date = CACHE_DF.index[-1]
        
        # 处理框选时间
        if relayoutData:
            if 'xaxis.range[0]' in relayoutData:
                start_date = pd.to_datetime(relayoutData['xaxis.range[0]'])
                end_date = pd.to_datetime(relayoutData['xaxis.range[1]'])
            elif 'xaxis.autorange' in relayoutData:
                pass

    # --- 绘图与统计 ---
    
    # 1. 截取时间段
    mask = (CACHE_DF.index >= start_date) & (CACHE_DF.index <= end_date)
    sub_df = CACHE_DF.loc[mask]
    
    if sub_df.empty:
        return dash.no_update, "所选区间无数据", dash.no_update

    # 2. 归一化展示 (让所有策略在选定区间的起点都对齐到 1.0，方便对比区间涨幅)
    #    如果不希望每次缩放都对齐，可以注释掉下面这行，直接用 sub_df
    display_df = sub_df / sub_df.iloc[0]

    # 3. 计算统计指标
    stats = []
    for col in display_df.columns:
        total_ret = display_df[col].iloc[-1] - 1
        mdd = calculate_max_drawdown(display_df[col])
        stats.append({
            '策略名称': col,
            '区间收益': f"{total_ret:+.2%}",
            '区间最大回撤': f"{mdd:.2%}"
        })

    # 4. 生成表格
    table = dbc.Table.from_dataframe(pd.DataFrame(stats), striped=True, bordered=True, hover=True)

    # 5. 生成图表
    fig = go.Figure()
    for col in display_df.columns:
        fig.add_trace(go.Scatter(
            x=display_df.index, y=display_df[col],
            mode='lines', name=col,
            hovertemplate='%{y:.3f}'
        ))

    fig.update_layout(
        title=f"策略对比 (区间起点归一化) | {start_date.date()} 至 {end_date.date()}",
        xaxis=dict(range=[start_date, end_date], type='date'),
        yaxis=dict(title='相对净值', fixedrange=False),
        hovermode="x unified",
        template="plotly_white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig, table, ""

# ==========================================
# 5. 启动
# ==========================================
if __name__ == '__main__':
    print("应用已启动: http://127.0.0.1:8050/")
    app.run(debug=True)