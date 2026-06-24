import akshare as ak
import pandas as pd

def get_data_via_akshare(fund_code):
    print(f"正在通过 AKShare 获取基金 {fund_code} 数据...")
    
    try:
        # fund_open_fund_info_em 是获取开放式基金历史数据的核心接口
        # indicator="单位净值走势" 会返回所有的历史净值数据
        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="累计净值走势")
        
        # AKShare 返回的列名通常已经是中文，例如：'净值日期', '单位净值', '日增长率' 等
        # 我们查看一下列名并进行标准化处理
        print("获取到的列名:", df.columns.tolist())
        
        # 重命名以匹配你之前的格式 (如果需要)
        # 通常 AKShare 返回的列是: ['净值日期', '单位净值', '累计净值', '日增长率', ...]
        # 确保日期格式正确
        df['净值日期'] = pd.to_datetime(df['净值日期'])
        df = df.sort_values('净值日期')
        
        # 保存文件
        file_name = f"data/fund_{fund_code}_akshare.csv"
        df.to_csv(file_name, index=False, encoding='utf-8-sig')
        file_path = f"data/fund_{fund_code}_history.json"
        df.to_json(file_path, orient='records', force_ascii=False, indent=4)
        print(f"成功！数据已保存至 {file_name}")
        print(f"数据区间: {df['净值日期'].iloc[0].date()} 至 {df['净值日期'].iloc[-1].date()}")
        print(df.tail())
        
    except Exception as e:
        print(f"获取失败: {e}")
        print("提示: 请确保 akshare 已更新到最新版 (pip install akshare --upgrade)")

if __name__ == "__main__":
    get_data_via_akshare("540010")