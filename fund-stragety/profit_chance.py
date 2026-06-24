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
        
        return self.prob_matrix
    
    def plot_profit_heatmap(self):
        """绘制收益概率分布热力图（参考上传图片样式）"""
        if self.prob_matrix is None:
            print("请先计算概率分布")
            return
        
        # 准备数据
        heatmap_data = self.prob_matrix.copy()
        
        # 如果数据太多，可以只显示部分区间
        if len(heatmap_data) > 30:
            # 选择概率较高的区间显示
            max_probs = heatmap_data.max(axis=1)
            top_indices = max_probs.nlargest(30).index
            heatmap_data = heatmap_data.loc[top_indices]
        
        # 确保顺序：亏损在下方，盈利在上方
        def sort_key(label):
            if '亏损' in label:
                # 提取亏损数值（负的越小表示亏损越大）
                try:
                    nums = label.replace('亏损', '').split('~')
                    return -float(nums[0].replace('元', ''))
                except:
                    return 0
            elif '盈利' in label:
                try:
                    nums = label.replace('盈利', '').split('~')
                    return 10000 + float(nums[0].replace('元', ''))
                except:
                    return 10000
            else:
                try:
                    nums = label.split('~')
                    return 5000 + float(nums[0])
                except:
                    return 5000
        
        heatmap_data = heatmap_data.iloc[np.argsort([sort_key(idx) for idx in heatmap_data.index])]
        
        # 创建热力图
        fig, ax = plt.subplots(figsize=(12, 14))
        
        # 使用seaborn绘制热力图
        sns.heatmap(heatmap_data, 
                   annot=True, 
                   fmt='.2%', 
                   cmap='RdYlGn',  # 红黄绿配色，红色表示亏损概率高，绿色表示盈利概率高
                   center=0,
                   linewidths=0.5,
                   linecolor='gray',
                   cbar_kws={'label': '概率', 'orientation': 'horizontal'},
                   ax=ax)
        
        # 设置标题和标签
        ax.set_title('任意一天买入1万元基金，不同持有期的收益概率分布热力图', 
                    fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('持有时间', fontsize=12)
        ax.set_ylabel('收益区间（元）', fontsize=12)
        
        # 调整刻度标签
        ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=9)
        
        # 添加网格线
        ax.grid(False)
        
        # 添加统计数据
        total_samples = len(self.returns_matrix)
        stats_text = f"数据来源: 沪深300ETF(510300)\n"
        stats_text += f"分析样本: {total_samples}个买入点\n"
        stats_text += f"初始投资: 10,000元\n"
        stats_text += f"时间范围: {self.fund_data['date'].min().date()} 至 {self.fund_data['date'].max().date()}"
        
        plt.figtext(0.02, 0.02, stats_text, fontsize=10,
                   bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
        
        plt.tight_layout()
        plt.show()
        
        # 额外绘制一个简化的汇总热力图
        self.plot_simplified_heatmap()
    
    def plot_simplified_heatmap(self):
        """绘制简化的收益热力图（类似上传图片的样式）"""
        if self.returns_matrix is None:
            return
        
        # 计算每个持有期的关键统计指标
        summary_stats = {}
        
        for period_name in self.returns_matrix.columns:
            returns = self.returns_matrix[period_name].dropna()
            
            # 定义收益区间
            profit_ranges = [
                ('大幅亏损', (returns <= -1000).mean()),
                ('中等亏损', ((returns > -1000) & (returns <= -500)).mean()),
                ('小幅亏损', ((returns > -500) & (returns < 0)).mean()),
                ('小幅盈利', ((returns >= 0) & (returns < 500)).mean()),
                ('中等盈利', ((returns >= 500) & (returns < 1000)).mean()),
                ('大幅盈利', (returns >= 1000).mean())
            ]
            
            summary_stats[period_name] = {k: v for k, v in profit_ranges}
        
        # 转换为DataFrame
        summary_df = pd.DataFrame(summary_stats)
        
        # 重新排序行
        row_order = ['大幅亏损', '中等亏损', '小幅亏损', '小幅盈利', '中等盈利', '大幅盈利']
        summary_df = summary_df.loc[row_order]
        
        # 创建热力图
        fig, ax = plt.subplots(figsize=(10, 6))
        
        sns.heatmap(summary_df, 
                   annot=True, 
                   fmt='.2%',
                   cmap='RdYlGn',
                   linewidths=0.5,
                   linecolor='gray',
                   cbar_kws={'label': '概率'},
                   ax=ax)
        
        ax.set_title('任意一天买入1万元基金，不同持有期的收益概览', 
                    fontsize=14, fontweight='bold', pad=15)
        ax.set_xlabel('持有时间')
        ax.set_ylabel('收益类别')
        
        plt.tight_layout()
        plt.show()
        
        # 打印具体数字
        print("\n收益概率分布详情:")
        print("=" * 60)
        print(f"{'持有期':<10} {'大幅亏损':<10} {'中等亏损':<10} {'小幅亏损':<10} {'小幅盈利':<10} {'中等盈利':<10} {'大幅盈利':<10}")
        print("-" * 80)
        
        for col in summary_df.columns:
            probs = summary_df[col]
            print(f"{col:<10} ", end="")
            for row in row_order:
                print(f"{probs[row]:<10.2%}", end="")
            print()
    
    def plot_cumulative_profit_curve(self):
        """绘制不同持有期的累计收益曲线"""
        if self.returns_matrix is None:
            print("请先计算收益矩阵")
            return
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        axes = axes.flatten()
        
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        for idx, (period_name, color) in enumerate(zip(self.returns_matrix.columns, colors)):
            if idx >= len(axes):
                break
                
            returns = self.returns_matrix[period_name].dropna().values
            
            # 计算累计收益（按买入时间顺序）
            cumulative_returns = np.cumsum(returns)
            
            ax = axes[idx]
            ax.plot(cumulative_returns, color=color, linewidth=1.5, alpha=0.8)
            ax.fill_between(range(len(cumulative_returns)), 0, cumulative_returns, 
                          alpha=0.2, color=color)
            
            # 添加零线
            ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, linewidth=1)
            
            # 添加统计信息
            total_return = cumulative_returns[-1] if len(cumulative_returns) > 0 else 0
            avg_return = returns.mean() if len(returns) > 0 else 0
            win_rate = (returns > 0).mean() if len(returns) > 0 else 0
            
            stats_text = f"总收益: {total_return:.0f}元\n"
            stats_text += f"平均收益: {avg_return:.0f}元\n"
            stats_text += f"胜率: {win_rate:.1%}"
            
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                   fontsize=9, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.7))
            
            ax.set_title(f'持有{period_name}的累计收益曲线', fontsize=12, fontweight='bold')
            ax.set_xlabel('买入次序')
            ax.set_ylabel('累计收益（元）')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_3d_surface(self):
        """绘制3D收益曲面图"""
        if self.returns_matrix is None:
            print("请先计算收益矩阵")
            return
        
        try:
            from mpl_toolkits.mplot3d import Axes3D
            
            # 准备数据
            periods = list(self.holding_periods.values())
            period_names = list(self.holding_periods.keys())
            
            # 计算每个持有期的收益分布
            X, Y = np.meshgrid(range(len(periods)), range(100))
            Z = np.zeros_like(X, dtype=float)
            
            for i, period_days in enumerate(periods):
                returns = self.returns_matrix[period_names[i]].dropna()
                
                # 计算分位数
                if len(returns) > 0:
                    quantiles = np.percentile(returns, np.linspace(0, 100, 100))
                    Z[:, i] = quantiles
            
            # 创建3D图
            fig = plt.figure(figsize=(14, 10))
            ax = fig.add_subplot(111, projection='3d')
            
            # 绘制曲面
            surf = ax.plot_surface(X, Y, Z, cmap='viridis', 
                                 alpha=0.8, linewidth=0, antialiased=True)
            
            # 设置标签
            ax.set_xlabel('持有期（天）')
            ax.set_ylabel('分位数 (%)')
            ax.set_zlabel('收益（元）')
            ax.set_title('不同持有期下的收益分布曲面', fontsize=14, fontweight='bold')
            
            # 设置x轴刻度
            ax.set_xticks(range(len(periods)))
            ax.set_xticklabels([str(d) for d in periods])
            
            # 设置y轴刻度
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.set_yticklabels(['0%', '25%', '50%', '75%', '100%'])
            
            # 添加颜色条
            fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5, label='收益（元）')
            
            plt.tight_layout()
            plt.show()
            
        except ImportError:
            print("3D绘图需要mpl_toolkits.mplot3d，请确保已正确安装matplotlib")
    
    def full_analysis(self, initial_investment=10000):
        """执行完整分析流程"""
        print("开始基金收益分析")
        print("=" * 60)
        
        # 1. 加载数据
        self.load_data()
        
        # 2. 绘制净值曲线
        self.plot_nav_curve()
        
        # 3. 计算收益矩阵
        self.calculate_returns_matrix(initial_investment)
        
        # 4. 计算概率分布
        self.calculate_probability_distribution()
        
        # 5. 绘制热力图
        self.plot_profit_heatmap()
        
        # 6. 绘制累计收益曲线
        self.plot_cumulative_profit_curve()
        
        print("\n分析完成！")
        
        return self


# 主程序
def main():
    # 创建分析器
    analyzer = FundProfitAnalysis('sh510300.json')
    
    # 执行完整分析
    analyzer.full_analysis(initial_investment=10000)
    
    # 尝试绘制3D图（可选）
    try:
        analyzer.plot_3d_surface()
    except Exception as e:
        print(f"3D绘图失败: {e}")


if __name__ == "__main__":
    main()