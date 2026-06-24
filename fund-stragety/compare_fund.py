import akshare as ak
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ==========================================
# 1. 配置部分
# ==========================================
# 基金代码列表
fund_codes = ['040026', '008928', '008701', '007361']

# 设置绘图风格和中文字体
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'sans-serif'] # 适配 Mac 和 Windows
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 2. 数据获取与清洗函数
# ==========================================
def get_fund_data(codes):
    data_dict = {}
    name_dict = {}
    
    print("正在获取基金数据...")
    
    # 获取所有基金的名称映射（为了图例显示名字而不是代码）
    try:
        fund_info = ak.fund_name_em()
        for code in codes:
            # 在总表中找到对应的名字
            name = fund_info[fund_info['基金代码'] == code]['基金简称'].values
            name_dict[code] = name[0] if len(name) > 0 else code
            print(f"找到基金: {code} - {name_dict[code]}")
    except:
        print("基金名称获取失败，将只显示代码")
        name_dict = {c: c for c in codes}

    # 获取历史净值
    for code in codes:
        try:
            # period="after_adjustment" 表示复权净值（包含分红再投资），对比收益必须用这个
            df = ak.fund_open_fund_hist_em(symbol=code, period="after_adjustment", adjust="1")
        except AttributeError:
            # 如果接口不存在，尝试替代方案
            try:
                print(f"尝试使用 fund_em_open_fund_info 获取 {code}...")
                df = ak.fund_em_open_fund_info(fund=code, indicator="累计净值")
            except AttributeError:
                print(f"akshare接口不可用，跳过基金 {code}")
                return pd.DataFrame()  # 返回空DataFrame
        except Exception as e:
            print(f"获取 {code} 失败: {e}")
            continue
            
            # 清洗数据
            if '净值日期' in df.columns:
                df['date'] = pd.to_datetime(df['净值日期'])
            elif 'date' in df.columns:
                # 有些接口返回date列
                pass
            else:
                print(f"未知的数据格式，跳过 {code}")
                continue
                
            if 'date' in df.columns:
                df.set_index('date', inplace=True)
            else:
                print(f"缺少日期列，跳过 {code}")
                continue
            
            # 我们使用 '累计净值' 或 '单位净值'(复权后)
            # 接口返回的列名可能变化，这里做个容错
            col_name = None
            for col in ['累计净值', '单位净值', 'close']:
                if col in df.columns:
                    col_name = col
                    break
            
            if col_name is None:
                print(f"未找到净值列，跳过 {code}。可用列: {df.columns.tolist()}")
                continue
            
            # 存入字典
            data_dict[name_dict[code]] = df[col_name]
            
        except Exception as e:
            print(f"获取 {code} 数据失败: {e}")

    # 合并为一个 DataFrame (自动对齐日期)
    # join='inner' 表示只保留大家都有数据的日期区间（取交集）
    if not data_dict:
        print("警告: 没有成功获取任何基金数据")
        return pd.DataFrame()
    
    try:
        df_merged = pd.concat(data_dict.values(), axis=1, keys=data_dict.keys(), join='inner')
        df_merged.sort_index(inplace=True)
        print(f"成功获取 {len(data_dict)} 个基金的数据")
        return df_merged
    except Exception as e:
        print(f"合并数据失败: {e}")
        return pd.DataFrame()

# ==========================================
# 3. 主逻辑
# ==========================================
# A. 获取数据
df = get_fund_data(fund_codes)

if df is None or df.empty:
    print("没有获取到有效数据")
    exit()

# B. 归一化处理 (关键步骤)
# 每一列都除以该列的第一行数据
# 这样所有基金在起始点的净值都变成了 1.0，方便对比涨幅
df_normalized = df / df.iloc[0]

# 计算累计收益率用于图例展示
total_returns = (df_normalized.iloc[-1] - 1) * 100

# ==========================================
# 4. 绘图
# ==========================================
fig, ax = plt.subplots(figsize=(12, 7))

# 绘制曲线
for column in df_normalized.columns:
    # 获取该基金的总收益率，显示在图例中
    ret = total_returns[column]
    ax.plot(df_normalized.index, df_normalized[column], linewidth=2, label=f"{column} (+{ret:.2f}%)")

# 设置图表细节
ax.set_title('多基金累计收益走势对比 (归一化)', fontsize=16, fontweight='bold')
ax.set_ylabel('累计净值 (起始=1.0)', fontsize=12)
ax.set_xlabel('日期', fontsize=12)

# Y轴显示百分比格式 (可选，或者直接显示 1.0, 1.2)
# ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0)) 

# 添加基准线 (y=1)
ax.axhline(y=1, color='black', linestyle='--', linewidth=1, alpha=0.5)

# 图例放在左上角
ax.legend(loc='upper left', frameon=True, shadow=True, fontsize=11)

# 自动调整布局
plt.grid(True, alpha=0.3)
plt.tight_layout()

# 保存或显示
plt.show()