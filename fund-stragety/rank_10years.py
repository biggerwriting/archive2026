import akshare as ak
import pandas as pd
import datetime
from tqdm import tqdm # 进度条库，如果没有请 pip install tqdm

# ==========================================
# 1. 配置参数
# ==========================================
pd.set_option('display.max_rows', 20)
pd.set_option('display.unicode.east_asian_width', True)

# 设定考察的时间跨度 (10年)
YEARS_BACK = 10
TARGET_DATE = datetime.datetime.now() - datetime.timedelta(days=365*YEARS_BACK)
print(f"正在寻找成立于 {TARGET_DATE.strftime('%Y-%m-%d')} 之前的债券基金...")

# ==========================================
# 2. 获取基金排名概览 (初筛)
# ==========================================
def get_bond_fund_candidates():
    print("正在获取东方财富债券型基金实时排名...")
    # symbol="债券型" 获取所有债基
    # 这一步主要为了拿到基金代码列表
    try:
        df_rank = ak.fund_open_fund_rank_em(symbol="债券型")
        
        # 筛选逻辑：
        # 1. 必须有“近5年”的数据 (说明至少成立5年以上，作为初步过滤)
        # 2. 我们可以先按“近5年”收益降序取前 50 名，作为“优等生”候选池
        #    (因为计算几千只基金的历史数据太慢了，我们假设近5年好的，近10年大概率也不差)
        
        # 转换数字列
        df_rank['近5年'] = pd.to_numeric(df_rank['近5年'], errors='coerce')
        
        # 过滤掉没有5年数据的
        df_candidates = df_rank.dropna(subset=['近5年'])
        
        # 取近5年排名前 30 的基金进行深度回测
        # (你可以把这个数字改大，比如 100，但运行时间会变长)
        top_candidates = df_candidates.sort_values('近5年', ascending=False).head(30)
        
        print(f"初筛完成，选取近5年表现最好的 {len(top_candidates)} 只基金进行10年期回测。")
        return top_candidates[['基金代码', '基金简称', '近5年']]
        
    except Exception as e:
        print(f"获取排名列表失败: {e}")
        return pd.DataFrame()

# ==========================================
# 3. 精确计算单只基金的 N 年收益
# ==========================================
def calculate_10y_return(fund_code):
    try:
        # 获取历史净值
        df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        
        # 优先使用累计净值计算（包含分红），如果没有则用单位净值
        # 注意：akshare返回的列名可能是 '累计净值' 或 '单位净值'
        col_name = '累计净值' if '累计净值' in df.columns else '单位净值'
        
        # 检查基金成立时间是否足够
        first_date = df['净值日期'].iloc[0]
        if first_date > TARGET_DATE:
            return None # 成立不满10年
            
        # 获取最新净值
        end_val = df[col_name].iloc[-1]
        
        # 获取10年前那天的净值 (找离目标日期最近的一天)
        # 使用 searchsorted 或 简单的距离比较
        # 这里用一种简单直观的方法：找 target_date 之后最近的一个交易日
        start_row = df[df['净值日期'] >= TARGET_DATE].iloc[0]
        start_val = start_row[col_name]
        
        # 计算收益率
        total_return = (end_val - start_val) / start_val
        
        return total_return
        
    except Exception:
        return None

# ==========================================
# 4. 主程序
# ==========================================
if __name__ == "__main__":
    # 1. 获取候选名单
    candidates = get_bond_fund_candidates()
    
    if not candidates.empty:
        results = []
        
        print("开始逐个计算近10年收益率 (请耐心等待)...")
        # 使用 tqdm 显示进度条
        for index, row in tqdm(candidates.iterrows(), total=candidates.shape[0]):
            code = row['基金代码']
            name = row['基金简称']
            
            ret_10y = calculate_10y_return(code)
            
            if ret_10y is not None:
                results.append({
                    '基金代码': code,
                    '基金简称': name,
                    '近10年收益率': ret_10y,
                    '近5年收益率(参考)': float(row['近5年']) / 100 # 原数据是百分数
                })
        
        # 2. 生成最终排名
        final_df = pd.DataFrame(results)
        if not final_df.empty:
            final_df = final_df.sort_values('近10年收益率', ascending=False).reset_index(drop=True)
            
            # 格式化输出
            final_df['近10年收益率'] = final_df['近10年收益率'].apply(lambda x: f"{x:.2%}")
            final_df['近5年收益率(参考)'] = final_df['近5年收益率(参考)'].apply(lambda x: f"{x:.2%}")
            
            print("\n" + "="*50)
            print("近10年债券型基金精选排名 (基于近5年Top30回测)")
            print("="*50)
            print(final_df[['基金代码', '基金简称', '近10年收益率', '近5年收益率(参考)']])
            
            # 保存
            final_df.to_csv("top_bond_funds_10years.csv", index=False, encoding='utf-8-sig')
            print("\n结果已保存至 top_bond_funds_10years.csv")
        else:
            print("没有找到符合条件的基金 (可能候选池中的基金都成立不满10年)。")