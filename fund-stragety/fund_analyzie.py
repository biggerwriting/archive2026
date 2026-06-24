import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

class FundHoldingAnalysis:
    """基金持有1年年化收益率分析类"""
    
    def __init__(self, fund_data=None):
        """
        初始化分析器
        
        Parameters:
        -----------
        fund_data : DataFrame
            基金数据，应包含日期和净值列
            格式示例：
                date        nav
            2020-01-01  1.0000
            2020-01-02  1.0100
        """
        self.fund_data = fund_data
        self.annual_returns = None
        self.return_distribution = None
        
    def load_fund_data(self, file_path=None, date_col='date', nav_col='nav'):
        """
        加载基金数据
        
        参数:
        file_path: 数据文件路径（CSV或Excel）
        date_col: 日期列名
        nav_col: 净值列名
        """
        if file_path:
            if file_path.endswith('.csv'):
                self.fund_data = pd.read_csv(file_path)
            elif file_path.endswith('.xlsx'):
                self.fund_data = pd.read_excel(file_path)
            else:
                raise ValueError("不支持的文件格式，请使用CSV或Excel文件")
        
        # 确保日期格式正确
        self.fund_data[date_col] = pd.to_datetime(self.fund_data[date_col])
        self.fund_data = self.fund_data.sort_values(date_col).reset_index(drop=True)
        
        # 重命名列以便后续处理
        self.fund_data = self.fund_data.rename(columns={date_col: 'date', nav_col: 'nav'})
        
        print(f"数据加载完成，共{len(self.fund_data)}条记录")
        print(f"数据时间范围: {self.fund_data['date'].min()} 至 {self.fund_data['date'].max()}")
        
    def calculate_annual_returns(self, holding_days=252, trading_days_per_year=252):
        """
        计算从任意时间点买入持有1年后的年化收益率
        
        参数:
        holding_days: 持有天数（默认252个交易日）
        trading_days_per_year: 年交易天数
        """
        if self.fund_data is None:
            raise ValueError("请先加载基金数据")
        
        # 创建结果DataFrame
        results = []
        
        # 计算每个可能的买入点
        for i in range(len(self.fund_data) - holding_days):
            buy_date = self.fund_data.loc[i, 'date']
            buy_nav = self.fund_data.loc[i, 'nav']
            
            # 找到持有期结束时的日期和净值
            end_idx = i + holding_days
            end_date = self.fund_data.loc[end_idx, 'date']
            end_nav = self.fund_data.loc[end_idx, 'nav']
            
            # 计算持有期总收益率
            total_return = (end_nav - buy_nav) / buy_nav
            
            # 计算年化收益率
            # 方法1: 简单年化（假设线性增长）
            annual_return_simple = total_return * (trading_days_per_year / holding_days)
            
            # 方法2: 复合年化（更准确）
            # 年化收益率 = (1 + 总收益率)^(年交易天数/持有天数) - 1
            annual_return_compound = (1 + total_return) ** (trading_days_per_year / holding_days) - 1
            
            # 计算持有天数（实际日历天数）
            holding_calendar_days = (end_date - buy_date).days
            
            results.append({
                'buy_date': buy_date,
                'buy_nav': buy_nav,
                'end_date': end_date,
                'end_nav': end_nav,
                'holding_days': holding_days,
                'calendar_days': holding_calendar_days,
                'total_return': total_return,
                'annual_return_simple': annual_return_simple,
                'annual_return_compound': annual_return_compound
            })
        
        self.annual_returns = pd.DataFrame(results)
        
        print(f"年化收益率计算完成，共{len(self.annual_returns)}个有效持有期")
        print(f"年化收益率统计:")
        print(f"  均值: {self.annual_returns['annual_return_compound'].mean():.2%}")
        print(f"  中位数: {self.annual_returns['annual_return_compound'].median():.2%}")
        print(f"  标准差: {self.annual_returns['annual_return_compound'].std():.2%}")
        print(f"  最大值: {self.annual_returns['annual_return_compound'].max():.2%}")
        print(f"  最小值: {self.annual_returns['annual_return_compound'].min():.2%}")
        
        return self.annual_returns
    
    def analyze_return_distribution(self, bins=None):
        """
        统计年化收益率的概率分布
        
        参数:
        bins: 收益率区间划分，默认为自动划分
        """
        if self.annual_returns is None:
            raise ValueError("请先计算年化收益率")
        
        returns = self.annual_returns['annual_return_compound']
        
        # 如果没有指定bins，使用自定义区间
        if bins is None:
            # 定义收益率区间（可以根据实际数据调整）
            bins = [-np.inf, -0.5, -0.4, -0.3, -0.2, -0.1, -0.05, 0, 
                    0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, np.inf]
        
        # 创建区间标签
        labels = []
        for i in range(len(bins)-1):
            if bins[i] == -np.inf:
                labels.append(f'<-50%')
            elif bins[i+1] == np.inf:
                labels.append(f'>50%')
            else:
                labels.append(f'{bins[i]:.0%}~{bins[i+1]:.0%}')
        
        # 分箱并统计
        returns_binned = pd.cut(returns, bins=bins, labels=labels, right=False)
        
        # 计算概率分布
        distribution = pd.DataFrame({
            'return_range': labels,
            'count': returns_binned.value_counts().sort_index(),
            'probability': returns_binned.value_counts(normalize=True).sort_index()
        })
        
        self.return_distribution = distribution
        
        # 打印分布结果
        print("\n年化收益率概率分布:")
        print("=" * 50)
        for _, row in distribution.iterrows():
            print(f"{row['return_range']:15s}: {row['count']:4d}次 ({row['probability']:.2%})")
        
        # 计算关键统计数据
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        high_returns = returns[returns > 0.2]  # 年化收益>20%
        loss_returns = returns[returns < -0.1]  # 年化亏损>10%
        
        print("\n关键统计:")
        print(f"获得正收益的概率: {len(positive_returns)/len(returns):.2%}")
        print(f"获得负收益的概率: {len(negative_returns)/len(returns):.2%}")
        print(f"获得高收益(>20%)的概率: {len(high_returns)/len(returns):.2%}")
        print(f"发生较大亏损(<-10%)的概率: {len(loss_returns)/len(returns):.2%}")
        
        return self.return_distribution
    
    def visualize_distribution(self):
        """可视化年化收益率分布"""
        if self.return_distribution is None or self.annual_returns is None:
            raise ValueError("请先计算年化收益率和分布")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. 年化收益率概率分布柱状图
        ax1 = axes[0, 0]
        bars = ax1.bar(self.return_distribution['return_range'], 
                      self.return_distribution['probability'] * 100)
        ax1.set_xlabel('年化收益率区间')
        ax1.set_ylabel('概率 (%)')
        ax1.set_title('持有1年年化收益率概率分布')
        ax1.tick_params(axis='x', rotation=45)
        
        # 在柱子上添加百分比标签
        for bar in bars:
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
        
        # 2. 年化收益率直方图
        ax2 = axes[0, 1]
        ax2.hist(self.annual_returns['annual_return_compound'] * 100, 
                bins=30, alpha=0.7, color='skyblue', edgecolor='black')
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='零收益线')
        ax2.axvline(x=self.annual_returns['annual_return_compound'].mean() * 100, 
                   color='green', linestyle='-', alpha=0.7, label='均值')
        ax2.set_xlabel('年化收益率 (%)')
        ax2.set_ylabel('频数')
        ax2.set_title('年化收益率分布直方图')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. 年化收益率时间序列
        ax3 = axes[1, 0]
        ax3.plot(self.annual_returns['buy_date'], 
                self.annual_returns['annual_return_compound'] * 100, 
                alpha=0.6, linewidth=1)
        ax3.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        ax3.fill_between(self.annual_returns['buy_date'], 0, 
                        self.annual_returns['annual_return_compound'] * 100,
                        where=(self.annual_returns['annual_return_compound'] * 100 >= 0),
                        color='green', alpha=0.3, label='正收益')
        ax3.fill_between(self.annual_returns['buy_date'], 0, 
                        self.annual_returns['annual_return_compound'] * 100,
                        where=(self.annual_returns['annual_return_compound'] * 100 < 0),
                        color='red', alpha=0.3, label='负收益')
        ax3.set_xlabel('买入日期')
        ax3.set_ylabel('年化收益率 (%)')
        ax3.set_title('不同买入时点的年化收益率')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. 箱线图
        ax4 = axes[1, 1]
        box_data = [self.annual_returns['annual_return_compound'] * 100]
        ax4.boxplot(box_data, vert=True, patch_artist=True,
                   boxprops=dict(facecolor='lightblue'))
        ax4.set_ylabel('年化收益率 (%)')
        ax4.set_title('年化收益率箱线图')
        ax4.set_xticklabels(['持有1年'])
        ax4.grid(True, alpha=0.3)
        
        # 在箱线图上添加统计信息
        stats_text = f"中位数: {self.annual_returns['annual_return_compound'].median():.2%}\n"
        stats_text += f"均值: {self.annual_returns['annual_return_compound'].mean():.2%}\n"
        stats_text += f"标准差: {self.annual_returns['annual_return_compound'].std():.2%}"
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, 
                fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        plt.show()
        
        # 5. 累计分布函数图（额外单独显示）
        plt.figure(figsize=(10, 6))
        sorted_returns = np.sort(self.annual_returns['annual_return_compound'])
        cdf = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
        
        plt.plot(sorted_returns * 100, cdf * 100, linewidth=2)
        plt.axvline(x=0, color='red', linestyle='--', alpha=0.5, label='零收益')
        
        # 标记关键分位点
        for percentile in [10, 25, 50, 75, 90]:
            value = np.percentile(sorted_returns * 100, percentile)
            plt.axvline(x=value, color='gray', linestyle=':', alpha=0.5)
            plt.text(value, 5, f'{percentile}%', rotation=90, va='bottom', ha='center')
        
        plt.xlabel('年化收益率 (%)')
        plt.ylabel('累计概率 (%)')
        plt.title('持有1年年化收益率累计分布函数 (CDF)')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def get_summary_statistics(self):
        """获取详细的统计摘要"""
        if self.annual_returns is None:
            raise ValueError("请先计算年化收益率")
        
        returns = self.annual_returns['annual_return_compound']
        
        summary = {
            '样本数量': len(returns),
            '均值': returns.mean(),
            '中位数': returns.median(),
            '标准差': returns.std(),
            '最小值': returns.min(),
            '最大值': returns.max(),
            '偏度': returns.skew(),
            '峰度': returns.kurtosis(),
            '正收益比例': (returns > 0).mean(),
            '负收益比例': (returns < 0).mean(),
            '年化收益>10%比例': (returns > 0.1).mean(),
            '年化亏损>10%比例': (returns < -0.1).mean(),
            '年化收益>20%比例': (returns > 0.2).mean(),
            '夏普比率(假设无风险利率2%)': (returns.mean() - 0.02) / returns.std() if returns.std() > 0 else np.nan,
            '信息比率': returns.mean() / returns.std() if returns.std() > 0 else np.nan
        }
        
        # 分位数统计
        percentiles = [1, 5, 10, 25, 50, 75, 90, 95, 99]
        for p in percentiles:
            summary[f'{p}%分位数'] = np.percentile(returns, p)
        
        summary_df = pd.DataFrame.from_dict(summary, orient='index', columns=['数值'])
        summary_df['数值'] = summary_df['数值'].apply(lambda x: f'{x:.2%}' if isinstance(x, float) and abs(x) < 1 else f'{x:.4f}')
        
        return summary_df
    
    def simulate_random_investment(self, n_simulations=10000):
        """
        模拟随机投资：随机选择买入点，持有1年
        
        参数:
        n_simulations: 模拟次数
        """
        if self.annual_returns is None:
            raise ValueError("请先计算年化收益率")
        
        # 从实际计算结果中随机抽样
        simulated_returns = np.random.choice(
            self.annual_returns['annual_return_compound'], 
            size=n_simulations, 
            replace=True
        )
        
        # 计算模拟结果的统计
        sim_stats = {
            '模拟次数': n_simulations,
            '平均年化收益': simulated_returns.mean(),
            '收益中位数': np.median(simulated_returns),
            '正收益概率': (simulated_returns > 0).mean(),
            '亏损概率': (simulated_returns < 0).mean(),
            '获得>10%收益概率': (simulated_returns > 0.1).mean(),
            '获得>20%收益概率': (simulated_returns > 0.2).mean(),
            '亏损>10%概率': (simulated_returns < -0.1).mean()
        }
        
        print("随机投资模拟结果:")
        print("=" * 40)
        for key, value in sim_stats.items():
            if isinstance(value, float) and abs(value) < 1:
                print(f"{key}: {value:.2%}")
            else:
                print(f"{key}: {value}")
        
        return simulated_returns, sim_stats


# 示例使用方式
def main():
    # 示例1: 使用模拟数据
    print("示例1: 使用模拟数据")
    print("=" * 60)
    
    # 生成模拟基金数据
    np.random.seed(42)
    dates = pd.date_range('2010-01-01', '2023-12-31', freq='B')  # 交易日
    n = len(dates)
    
    # 生成随机游走的净值序列（更符合实际）
    returns = np.random.normal(0.0003, 0.015, n)  # 日收益率均值为0.03%，标准差为1.5%
    nav = 1.0 * np.exp(np.cumsum(returns))  # 净值
    
    fund_data = pd.DataFrame({
        'date': dates,
        'nav': nav
    })
    
    # 创建分析器
    analyzer = FundHoldingAnalysis(fund_data)
    
    # 计算年化收益率
    annual_returns = analyzer.calculate_annual_returns(holding_days=252)
    
    # 分析收益率分布
    distribution = analyzer.analyze_return_distribution()
    
    # 获取统计摘要
    summary = analyzer.get_summary_statistics()
    print("\n详细统计摘要:")
    print(summary)
    
    # 可视化
    analyzer.visualize_distribution()
    
    # 模拟随机投资
    simulated_returns, sim_stats = analyzer.simulate_random_investment(n_simulations=10000)
    
    # 示例2: 实际使用（需要提供数据文件）
    print("\n" + "=" * 60)
    print("示例2: 使用实际数据文件")
    print("提示: 请准备包含'date'和'nav'列的CSV文件")
    
    """
    # 实际使用代码示例
    analyzer2 = FundHoldingAnalysis()
    
    # 加载实际数据
    analyzer2.load_fund_data('your_fund_data.csv')
    
    # 计算年化收益率
    annual_returns2 = analyzer2.calculate_annual_returns()
    
    # 分析分布
    distribution2 = analyzer2.analyze_return_distribution()
    
    # 可视化
    analyzer2.visualize_distribution()
    """

if __name__ == "__main__":
    main()