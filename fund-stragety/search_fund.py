import dash
from dash import dcc, html, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import akshare as ak
import numpy as np

# ==========================================
# 1. 全局数据准备 (应用启动时加载)
# ==========================================
print("正在初始化基金列表数据库 (fund_name_em)...")
try:
    # 获取所有公募基金列表 (包含 基金代码, 基金简称, 基金类型, 拼音缩写)
    ALL_FUNDS_DF = ak.fund_name_em()
    # 只需要保留关键列
    ALL_FUNDS_DF = ALL_FUNDS_DF[['基金代码', '基金简称', '基金类型']]
    print(f"成功加载 {len(ALL_FUNDS_DF)} 只基金信息。")
except Exception as e:
    print(f"初始化失败: {e}")
    #以此防崩溃
    ALL_FUNDS_DF = pd.DataFrame(columns=['基金代码', '基金简称', '基金类型'])

# 核心数据获取函数 (保持不变，增加了容错)
def fetch_fund_data(codes):
    data_dict = {}
    unique_codes = list(set(codes))
    
    for code in unique_codes:
        df = None
        try:
            # 优先尝试 东方财富 接口
            if hasattr(ak, 'fund_open_fund_hist_em'):
                df = ak.fund_open_fund_hist_em(symbol=code, period="after_adjustment", adjust="1")
                if df is not None and not df.empty:
                    col_map = {'净值日期':'date', '累计净值':'close', '单位净值':'close'}
                    df.rename(columns=col_map, inplace=True)
                    if 'date' in df.columns and 'close' in df.columns:
                        df = df[['date', 'close']]
                    else:
                        # 如果映射失败，尝试使用原始列名
                        print(f"警告: {code} 列名映射失败，尝试使用原始列名")
                        if df.columns.size >= 2:
                            # 使用第一列作为日期，第二列作为净值
                            df.columns = ['date', 'close'] + [f'col_{i}' for i in range(2, len(df.columns))]
                            df = df[['date', 'close']]
                        else:
                            df = None
            
            # 备用：新浪ETF
            if df is None and (code.startswith('5') or code.startswith('1')):
                prefix = 'sh' if code.startswith('5') else 'sz'
                try:
                    df = ak.fund_etf_hist_sina(symbol=f"{prefix}{code}")
                    # 检查新浪接口返回的列
                    if 'date' in df.columns and 'close' in df.columns:
                        df = df[['date', 'close']]
                    else:
                        print(f"新浪接口 {code} 返回列: {df.columns.tolist()}")
                        df = None
                except Exception as e2:
                    print(f"新浪接口获取 {code} 失败: {e2}")
                    df = None

            if df is not None and not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df['close'] = pd.to_numeric(df['close'], errors='coerce')
                # 删除无效数据
                df = df.dropna()
                if not df.empty:
                    data_dict[code] = df['close']
                    print(f"✓ 成功获取 {code} 数据 ({len(df)} 条)")
                else:
                    print(f"✗ {code} 有效数据为空")
            else:
                print(f"✗ 无法获取 {code} 的有效数据")
                
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
            continue

    if not data_dict: 
        print("没有成功获取任何基金数据")
        return None
    
    print(f"成功获取 {len(data_dict)} 个基金的数据，正在合并...")
    return pd.concat(data_dict.values(), axis=1, keys=data_dict.keys(), join='inner')

def calculate_max_drawdown(series):
    return ((series - series.cummax()) / series.cummax()).min()

# ==========================================
# 2. Dash 应用初始化
# ==========================================
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], title="智能基金投顾")
CACHE_DF = pd.DataFrame()

# ==========================================
# 3. 页面布局
# ==========================================
app.layout = dbc.Container([
    dbc.Row(html.H2("智能基金组合构建工具", className="text-center my-4")),
    
    dcc.Store(id='local-store-strategies', storage_type='local'),

    dbc.Row([
        # --- 左侧：基金查询与策略配置 ---
        dbc.Col([
            # 模块 1: 基金搜索器
            dbc.Card([
                dbc.CardHeader("1. 基金搜索 (添加到池子)"),
                dbc.CardBody([
                    dbc.InputGroup([
                        dbc.Input(id='search-keyword', placeholder="输入代码(如510300) 或 名称(如半导体)"),
                        dbc.Button("搜索", id='btn-search', color="info")
                    ], className="mb-2"),
                    
                    # 搜索结果表格
                    dash_table.DataTable(
                        id='search-results-table',
                        columns=[{"name": i, "id": i} for i in ['基金代码', '基金简称', '基金类型']],
                        data=[],
                        row_selectable='multi', # 支持多选
                        selected_rows=[],
                        page_size=5, # 每页显示5条
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left', 'fontSize': '12px'},
                        style_header={'fontWeight': 'bold'}
                    ),
                    
                    dbc.Button("⬇️ 将选中基金添加到下方策略", id='btn-add-to-pool', color="warning", size="sm", className="w-100 mt-2")
                ])
            ], className="mb-3"),

            # 模块 2: 策略配置
            dbc.Card([
                dbc.CardHeader("2. 策略配置与保存"),
                dbc.CardBody([
                    html.Label("策略名称:"),
                    dbc.Input(id='input-strat-name', placeholder="我的自定义策略", className="mb-2"),
                    
                    html.Label("基金代码池 (自动填充):"),
                    dbc.Textarea(id='input-codes', placeholder="点击上方搜索添加，或手动输入", style={'height': '60px'}, className="mb-2"),
                    
                    html.Label("持仓权重 (逗号分隔, 自动填充默认值):"),
                    dbc.Textarea(id='input-weights', placeholder="例如: 0.5, 0.5", style={'height': '60px'}, className="mb-3"),
                    
                    dbc.Button("保存当前策略", id='btn-save', color="success", className="w-100"),
                    html.Div(id='save-msg', className="text-success mt-2 small")
                ])
            ])
        ], width=4),

        # --- 右侧：策略对比与回测 ---
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("3. 策略回测看板"),
                dbc.CardBody([
                    html.Label("已保存策略 (多选对比):"),
                    dcc.Checklist(id='checklist-strategies', options=[], value=[], labelStyle={'display': 'inline-block', 'marginRight': '15px'}),
                    dbc.Button("开始回测对比", id='btn-run', color="primary", size="lg", className="w-100 mt-3"),
                    html.Div(id='run-msg', className="text-danger mt-2 small")
                ])
            ], className="mb-3"),
            
            dcc.Loading(dcc.Graph(id='main-chart', style={'height': '500px'})),
            html.Div(id='stats-table-container', className="mt-3")
        ], width=8)
    ])
], fluid=True)

# ==========================================
# 4. 回调逻辑
# ==========================================

# --- 回调 A: 搜索基金 ---
@app.callback(
    Output('search-results-table', 'data'),
    Input('btn-search', 'n_clicks'),
    State('search-keyword', 'value')
)
def search_funds(n_clicks, keyword):
    if not keyword:
        return []
    
    # 模糊搜索：代码包含 OR 名称包含
    #astype(str) 防止代码列被当成数字
    mask = ALL_FUNDS_DF['基金代码'].astype(str).str.contains(keyword) | \
           ALL_FUNDS_DF['基金简称'].str.contains(keyword)
    
    results = ALL_FUNDS_DF[mask].head(20) # 只显示前20条，防止卡顿
    return results.to_dict('records')

# --- 回调 B: 将搜索结果添加到策略池 (核心交互) ---
@app.callback(
    [Output('input-codes', 'value'),
     Output('input-weights', 'value'),
     Output('search-results-table', 'selected_rows')], # 添加后清空勾选
    Input('btn-add-to-pool', 'n_clicks'),
    [State('search-results-table', 'selected_rows'),
     State('search-results-table', 'data'),
     State('input-codes', 'value'),
     State('input-weights', 'value')]
)
def add_funds_to_pool(n_clicks, selected_indices, table_data, current_codes, current_weights):
    if not n_clicks or not selected_indices:
        return dash.no_update, dash.no_update, dash.no_update
    
    # 1. 获取当前已有的代码列表
    if current_codes:
        code_list = [c.strip() for c in current_codes.replace('，', ',').split(',') if c.strip()]
        weight_list = [w.strip() for w in str(current_weights).replace('，', ',').split(',') if w.strip()]
    else:
        code_list = []
        weight_list = []

    # 2. 遍历选中的行，添加新代码
    new_codes_added = []
    for idx in selected_indices:
        row = table_data[idx]
        new_code = row['基金代码']
        
        # 避免重复添加
        if new_code not in code_list:
            code_list.append(new_code)
            new_codes_added.append(new_code)
            # 默认添加一个权重占位符，比如 '0.1'，提示用户修改
            weight_list.append("0.1") 

    # 3. 重新组合字符串
    new_codes_str = ", ".join(code_list)
    new_weights_str = ", ".join(weight_list)
    
    return new_codes_str, new_weights_str, [] # 清空勾选

# --- 回调 C: 保存策略 (同前) ---
@app.callback(
    [Output('local-store-strategies', 'data'),
     Output('save-msg', 'children'),
     Output('checklist-strategies', 'options')],
    [Input('btn-save', 'n_clicks'),
     Input('local-store-strategies', 'data')],
    [State('input-strat-name', 'value'),
     State('input-codes', 'value'),
     State('input-weights', 'value')]
)
def save_strategy(n_clicks, stored_data, name, codes, weights):
    strategies = stored_data if stored_data else {}
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'local-store-strategies' or not ctx.triggered:
        options = [{'label': k, 'value': k} for k in strategies.keys()]
        return dash.no_update, "", options

    if not name or not codes:
        return dash.no_update, "请填写完整", dash.no_update

    try:
        c_list = [c.strip() for c in codes.replace('，', ',').split(',')]
        w_list = [float(w) for w in weights.replace('，', ',').split(',')]
        # 简单归一化权重
        w_sum = sum(w_list)
        w_list = [w/w_sum for w in w_list]
        
        strategies[name] = {'codes': c_list, 'weights': w_list}
        options = [{'label': k, 'value': k} for k in strategies.keys()]
        return strategies, f"策略 '{name}' 已保存!", options
    except Exception as e:
        return dash.no_update, f"格式错误: {e}", dash.no_update

# --- 回调 D: 运行回测 (同前，略微精简) ---
@app.callback(
    [Output('main-chart', 'figure'),
     Output('stats-table-container', 'children'),
     Output('run-msg', 'children')],
    [Input('btn-run', 'n_clicks'),
     Input('main-chart', 'relayoutData')],
    [State('checklist-strategies', 'value'),
     State('local-store-strategies', 'data')]
)
def run_backtest(n_clicks, relayoutData, selected_names, stored_data):
    global CACHE_DF
    ctx = callback_context
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not selected_names:
        return go.Figure(), "", "请选择策略"

    # 点击运行：重新获取数据
    if trigger_id == 'btn-run':
        all_codes = set()
        for name in selected_names:
            all_codes.update(stored_data[name]['codes'])
        
        raw_df = fetch_fund_data(list(all_codes))
        if raw_df is None or raw_df.empty:
            return go.Figure(), "", "数据获取失败"

        df_norm = raw_df / raw_df.iloc[0]
        strategy_curves = pd.DataFrame(index=df_norm.index)
        
        for name in selected_names:
            strat = stored_data[name]
            # 这里的权重已经是保存时归一化过的
            # 重新对齐数据列 - 确保代码与数据框列名匹配
            available_codes = []
            available_weights = []
            
            for i, code in enumerate(strat['codes']):
                # 检查代码是否在数据框中可用
                if code in df_norm.columns:
                    available_codes.append(code)
                    available_weights.append(strat['weights'][i])
                else:
                    # 如果代码不匹配，尝试不同的格式
                    clean_code = code.replace('sh', '').replace('sz', '')
                    if clean_code in df_norm.columns:
                        available_codes.append(clean_code)
                        available_weights.append(strat['weights'][i])
                    else:
                        print(f"警告: 基金代码 {code} 在获取的数据中未找到，已跳过")
            
            if not available_codes:
                print(f"错误: 策略 '{name}' 中没有可用的基金代码")
                continue
                
            # 重新归一化权重
            available_weights = np.array(available_weights)
            available_weights = available_weights / available_weights.sum()
            
            sub_df = df_norm[available_codes]
            strategy_curves[name] = (sub_df * available_weights).sum(axis=1)

        CACHE_DF = strategy_curves
        start_date = CACHE_DF.index[0]
        end_date = CACHE_DF.index[-1]
    
    # 缩放图表
    else:
        if CACHE_DF.empty: return dash.no_update, dash.no_update, dash.no_update
        start_date = CACHE_DF.index[0]
        end_date = CACHE_DF.index[-1]
        if relayoutData and 'xaxis.range[0]' in relayoutData:
            start_date = pd.to_datetime(relayoutData['xaxis.range[0]'])
            end_date = pd.to_datetime(relayoutData['xaxis.range[1]'])

    # 绘图
    mask = (CACHE_DF.index >= start_date) & (CACHE_DF.index <= end_date)
    sub_df = CACHE_DF.loc[mask]
    if sub_df.empty: return dash.no_update, "无数据", dash.no_update
    
    # 重新归一化展示
    display_df = sub_df / sub_df.iloc[0]
    
    # 统计
    stats = []
    for col in display_df.columns:
        ret = display_df[col].iloc[-1] - 1
        mdd = calculate_max_drawdown(display_df[col])
        stats.append({'策略': col, '收益': f"{ret:+.2%}", '回撤': f"{mdd:.2%}"})
    
    table = dbc.Table.from_dataframe(pd.DataFrame(stats), striped=True, bordered=True)
    
    fig = go.Figure()
    for col in display_df.columns:
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df[col], name=col))
    
    fig.update_layout(
        title=f"策略收益对比 | {start_date.date()} 至 {end_date.date()}",
        xaxis=dict(range=[start_date, end_date]),
        hovermode="x unified", template="plotly_white"
    )
    
    return fig, table, ""

if __name__ == '__main__':
    app.run(debug=True)