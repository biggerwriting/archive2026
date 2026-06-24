import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class FundProfitAnalysis:
    """基金收益分析类 - 支持不同持有期的收益分布热力图"""
    
    def __init__(self, data_path='sh510300.json'):
        """初始化分析器"""
        self.data_path = data_path
        self.fund_data = None
        self.returns_matrix = None
        self.prob_matrix = None
        self.holding_periods = None
        
    def load_data(self):
        """加载基金数据"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            
            # 转换时间戳（毫秒转日期）
            df['date'] = pd.to_datetime(df['date'], unit='ms')
            
            # 使用收盘价作为净值
            df['nav'] = df['close']
            
            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算日收益率
            df['daily_return'] = df['nav'].pct_change()
            
            self.fund_data = df
            
            print(f"数据加载完成，共{len(df)}条记录")
            print(f"时间范围: {df['date'].min()} 至 {df['date'].max()}")
            print(f"初始净值: {df['nav'].iloc[0]:.4f}, 最终净值: {df['nav'].iloc[-1]:.4f}")
            print(f"总收益率: {(df['nav'].iloc[-1] - df['nav'].iloc[0]) / df['nav'].iloc[0]:.2%}")
            
            return df
            
        except Exception as e:
            print(f"数据加载失败: {e}")
            return None

    def plot_nav_curve(self):
        """绘制基金净值曲线图"""
        if self.fund_data is None:
            print("请先加载数据")
            return
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10), height_ratios=[2, 1])
        
        # 1. 净值曲线
        ax1.plot(self.fund_data['date'], self.fund_data['nav'], 
                linewidth=1.5, color='#1f77b4', label='净值')
        
        # 计算移动平均线
        ma20 = self.fund_data['nav'].rolling(window=20).mean()
        ma60 = self.fund_data['nav'].rolling(window=60).mean()
        
        ax1.plot(self.fund_data['date'], ma20, 'orange', linewidth=1, alpha=0.7, label='20日均线')
        ax1.plot(self.fund_data['date'], ma60, 'red', linewidth=1, alpha=0.7, label='60日均线')
        
        # 填充净值曲线
        ax1.fill_between(self.fund_data['date'], self.fund_data['nav'], 
                        alpha=0.2, color='#1f77b4')
        
        ax1.set_title('沪深300ETF(510300)净值变化曲线', fontsize=16, fontweight='bold')
        ax1.set_xlabel('日期')
        ax1.set_ylabel('单位净值')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='upper left')
        
        # 添加净值统计信息
        stats_text = f"初始净值: {self.fund_data['nav'].iloc[0]:.4f}\n"
        stats_text += f"最终净值: {self.fund_data['nav'].iloc[-1]:.4f}\n"
        stats_text += f"累计涨幅: {((self.fund_data['nav'].iloc[-1] - self.fund_data['nav'].iloc[0]) / self.fund_data['nav'].iloc[0]):.2%}\n"
        stats_text += f"年化收益率: {((self.fund_data['nav'].iloc[-1] / self.fund_data['nav'].iloc[0]) ** (252/len(self.fund_data)) - 1):.2%}"
        
        print("=" * 60)
        print(stats_text)

        ax1.text(0.02, 0.98, stats_text, transform=ax1.transAxes,
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
        
        # 2. 日收益率分布
        daily_returns = self.fund_data['daily_return'].dropna() * 100
        
        ax2.hist(daily_returns, bins=100, alpha=0.7, color='#2ca02c', edgecolor='black')
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='零收益线')
        ax2.axvline(x=daily_returns.mean(), color='blue', linestyle='-', alpha=0.7, label='均值')
        
        ax2.set_xlabel('日收益率 (%)')
        ax2.set_ylabel('频数')
        ax2.set_title('日收益率分布直方图', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 添加收益率统计信息
        return_stats = f"日收益率均值: {daily_returns.mean():.4f}%\n"
        return_stats += f"日收益率标准差: {daily_returns.std():.4f}%\n"
        return_stats += f"正收益天数比例: {(daily_returns > 0).sum() / len(daily_returns):.2%}\n"
        return_stats += f"最大单日涨幅: {daily_returns.max():.2f}%\n"
        return_stats += f"最大单日跌幅: {daily_returns.min():.2f}%"
        
        ax2.text(0.02, 0.98, return_stats, transform=ax2.transAxes,
                fontsize=9, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        print("=" * 60)
        print(return_stats)
        
        plt.tight_layout()
        plt.show()

    def calculate_returns_matrix(self, initial_investment=10000):
        """
        计算不同持有期的收益矩阵
        
        参数:
        initial_investment: 初始投资金额（元）
        """
        if self.fund_data is None:
            print("请先加载数据")
            return
        
        # 定义持有期（交易日）
        holding_periods = {
            '1天': 1,
            '1周': 5,
            '1月': 21,
            '3月': 63,
            '6月': 126,
            '1年': 252
        }
        
        self.holding_periods = holding_periods
        
        # 初始化结果矩阵
        returns_dict = {}
        
        # 对每个持有期计算收益
        for period_name, days in holding_periods.items():
            print(f"正在计算持有{period_name}的收益...")
            
            period_returns = []
            
            # 对每个可能的买入日
            for i in range(len(self.fund_data) - days):
                buy_nav = self.fund_data.loc[i, 'nav']
                end_nav = self.fund_data.loc[i + days, 'nav']
                
                # 计算收益率
                return_rate = (end_nav - buy_nav) / buy_nav
                
                # 计算收益金额
                profit = initial_investment * return_rate
                
                period_returns.append(profit)
            
            returns_dict[period_name] = period_returns
        
        # 转换为DataFrame
        max_len = max(len(r) for r in returns_dict.values())
        for key in returns_dict:
            if len(returns_dict[key]) < max_len:
                # 填充NaN
                returns_dict[key] = returns_dict[key] + [np.nan] * (max_len - len(returns_dict[key]))
        
        self.returns_matrix = pd.DataFrame(returns_dict)
        
        print("\n收益矩阵计算完成！")
        print(f"每种持有期样本数: {len(self.returns_matrix)}")
        
        # 打印各持有期的收益统计
        for period_name in holding_periods.keys():
            returns = self.returns_matrix[period_name].dropna()
            if len(returns) > 0:
                print(f"\n持有{period_name}:")
                print(f"  平均收益: {returns.mean():.2f}元")
                print(f"  收益中位数: {returns.median():.2f}元")
                print(f"  正收益概率: {(returns > 0).mean():.2%}")
                print(f"  最大收益: {returns.max():.2f}元")
                print(f"  最大亏损: {returns.min():.2f}元")
        
        return self.returns_matrix

    def calculate_percentiles(self, bins=None):

        if self.returns_matrix is None:
            print("请先计算收益矩阵")
            return
        
        # 计算每个持有期的概率分布
        for period_name in self.returns_matrix.columns:
            daily_returns = self.returns_matrix[period_name].dropna()
            

            # 计算10%分位点
            percentiles = [np.percentile(daily_returns, i*10) for i in range(1, 11)]

            # 输出每个概率区间的收益范围
            print(f"{period_name}收益概率分布：")
            for i in range(10):
                if i == 0:
                    lower_bound = min(daily_returns)
                else:
                    lower_bound = percentiles[i-1]
                
                upper_bound = percentiles[i]
                
                print(f"{i+1}0% 概率: 收益在 {lower_bound:.2f} 到 {upper_bound:.2f} 之间")
                    
     

    def calculate_probability_distribution(self, bins=None):
        """
        计算不同持有期的收益概率分布
        
        参数:
        bins: 收益区间划分，默认为自动划分
        """
        if self.returns_matrix is None:
            print("请先计算收益矩阵")
            return
        
        if bins is None:
            # 基于所有收益数据动态确定区间
            all_returns = self.returns_matrix.values.flatten()
            all_returns = all_returns[~np.isnan(all_returns)]
            
            # 确定区间范围（从最小到最大）
            min_val = np.floor(all_returns.min() / 100) * 100
            max_val = np.ceil(all_returns.max() / 100) * 100
            
            # 如果范围太大，使用更粗的划分
            if max_val - min_val > 5000:
                step = 500
            elif max_val - min_val > 2000:
                step = 200
            elif max_val - min_val > 1000:
                step = 100
            else:
                step = 50
            
            bins = np.arange(min_val, max_val + step, step)
        
        # 初始化概率矩阵
        prob_matrix = []
        bin_labels = []
        
        # 创建区间标签
        for i in range(len(bins) - 1):
            if bins[i] < 0 and bins[i+1] <= 0:
                label = f'亏损{bins[i+1]:.0f}~{bins[i]:.0f}'
            elif bins[i] < 0 and bins[i+1] > 0:
                label = f'{bins[i]:.0f}~{bins[i+1]:.0f}'
            else:
                label = f'盈利{bins[i]:.0f}~{bins[i+1]:.0f}'
            bin_labels.append(label)
        
        # 计算每个持有期的概率分布
        for period_name in self.returns_matrix.columns:
            returns = self.returns_matrix[period_name].dropna()
            
            # 计算落在每个区间的概率
            hist, _ = np.histogram(returns, bins=bins, density=True)
            prob = hist / hist.sum() if hist.sum() > 0 else hist
            
            prob_matrix.append(prob)
        
        self.prob_matrix = pd.DataFrame(
            prob_matrix, 
            index=self.returns_matrix.columns,
            columns=bin_labels
        ).T  # 转置，使持有期为列，收益区间为行
        
        print("概率分布矩阵计算完成！")
        print( self.prob_matrix)
        
        return self.prob_matrix
    

    def full_analysis(self, initial_investment=10000):
        """执行完整分析流程"""
        print("开始基金收益分析")
        print("=" * 60)
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 绘制净值曲线
        # self.plot_nav_curve()

        # 3. 计算收益矩阵
        self.calculate_returns_matrix(initial_investment)

        # 4. 计算概率分布
        self.calculate_probability_distribution()

        self.calculate_percentiles()

# 主程序
def main():
    # 创建分析器
    analyzer = FundProfitAnalysis('sh510300.json')
    
    # 执行完整分析
    analyzer.full_analysis(initial_investment=10000)
    


if __name__ == "__main__":
    main()