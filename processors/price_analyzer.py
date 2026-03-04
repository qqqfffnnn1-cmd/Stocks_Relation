"""
价格相关性分析引擎
计算股票间的价格联动、同涨同跌、波动相似度等指标
"""
import pandas as pd
import numpy as np
from scipy import stats
from typing import Tuple, Dict
from datetime import datetime, timedelta


class PriceCorrelationAnalyzer:
    """价格相关性分析器"""

    def __init__(self):
        pass

    def calculate_correlation(self, df1: pd.DataFrame, df2: pd.DataFrame,
                            method: str = 'pearson') -> Dict:
        """
        计算两只股票的价格相关性

        Args:
            df1: 股票1的行情数据（需包含 date, close 列）
            df2: 股票2的行情数据
            method: 相关性计算方法 'pearson'/'spearman'

        Returns:
            dict: 包含相关系数、同涨同跌天数、波动相似度等指标
        """
        # 合并数据（按日期对齐）
        merged = pd.merge(
            df1[['date', 'close', 'pct_change']],
            df2[['date', 'close', 'pct_change']],
            on='date',
            suffixes=('_1', '_2')
        )

        if len(merged) < 10:
            return {
                'error': '数据不足，至少需要10个交易日',
                'data_points': len(merged)
            }

        # 1. 价格相关系数
        if method == 'pearson':
            corr_coef, p_value = stats.pearsonr(merged['close_1'], merged['close_2'])
        else:
            corr_coef, p_value = stats.spearmanr(merged['close_1'], merged['close_2'])

        # 2. 涨跌幅相关系数
        pct_corr, pct_p_value = stats.pearsonr(
            merged['pct_change_1'].fillna(0),
            merged['pct_change_2'].fillna(0)
        )

        # 3. 同涨同跌分析
        merged['both_up'] = (merged['pct_change_1'] > 0) & (merged['pct_change_2'] > 0)
        merged['both_down'] = (merged['pct_change_1'] < 0) & (merged['pct_change_2'] < 0)
        merged['sync'] = merged['both_up'] | merged['both_down']

        sync_days = merged['sync'].sum()
        sync_rate = sync_days / len(merged)

        # 4. 波动相似度（标准差比值）
        std1 = merged['pct_change_1'].std()
        std2 = merged['pct_change_2'].std()
        volatility_ratio = min(std1, std2) / max(std1, std2) if max(std1, std2) > 0 else 0

        # 5. 领先滞后关系（互相关分析）
        lead_lag = self._calculate_lead_lag(
            merged['pct_change_1'].fillna(0).values,
            merged['pct_change_2'].fillna(0).values
        )

        return {
            'correlation': round(corr_coef, 4),
            'p_value': round(p_value, 4),
            'pct_correlation': round(pct_corr, 4),
            'sync_days': int(sync_days),
            'total_days': len(merged),
            'sync_rate': round(sync_rate, 4),
            'both_up_days': int(merged['both_up'].sum()),
            'both_down_days': int(merged['both_down'].sum()),
            'volatility_ratio': round(volatility_ratio, 4),
            'lead_lag': lead_lag,
            'date_range': {
                'start': merged['date'].min().strftime('%Y-%m-%d'),
                'end': merged['date'].max().strftime('%Y-%m-%d')
            }
        }

    def _calculate_lead_lag(self, series1: np.ndarray, series2: np.ndarray,
                           max_lag: int = 5) -> Dict:
        """
        计算领先滞后关系

        Args:
            series1: 股票1的涨跌幅序列
            series2: 股票2的涨跌幅序列
            max_lag: 最大滞后期

        Returns:
            dict: 最佳滞后期和相关系数
        """
        correlations = []

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                # series1 领先
                corr = np.corrcoef(series1[:lag], series2[-lag:])[0, 1]
            elif lag > 0:
                # series2 领先
                corr = np.corrcoef(series1[lag:], series2[:-lag])[0, 1]
            else:
                # 同步
                corr = np.corrcoef(series1, series2)[0, 1]

            correlations.append((lag, corr))

        # 找到最大相关系数对应的滞后期
        best_lag, best_corr = max(correlations, key=lambda x: abs(x[1]))

        if best_lag < 0:
            lead_stock = 1
            lag_days = abs(best_lag)
        elif best_lag > 0:
            lead_stock = 2
            lag_days = best_lag
        else:
            lead_stock = 0  # 同步
            lag_days = 0

        return {
            'lead_stock': lead_stock,  # 0=同步, 1=股票1领先, 2=股票2领先
            'lag_days': lag_days,
            'correlation': round(best_corr, 4)
        }

    def calculate_beta(self, stock_df: pd.DataFrame, market_df: pd.DataFrame) -> float:
        """
        计算股票相对于市场的 Beta 值

        Args:
            stock_df: 个股行情
            market_df: 市场指数行情（如沪深300）

        Returns:
            float: Beta 值
        """
        merged = pd.merge(
            stock_df[['date', 'pct_change']],
            market_df[['date', 'pct_change']],
            on='date',
            suffixes=('_stock', '_market')
        )

        if len(merged) < 10:
            return 0.0

        # 线性回归: stock_return = alpha + beta * market_return
        market_returns = merged['pct_change_market'].fillna(0).values
        stock_returns = merged['pct_change_stock'].fillna(0).values

        slope, intercept, r_value, p_value, std_err = stats.linregress(
            market_returns, stock_returns
        )

        return round(slope, 4)

    def batch_correlation_matrix(self, stocks_data: Dict[str, pd.DataFrame],
                                 method: str = 'pearson') -> pd.DataFrame:
        """
        批量计算多只股票的相关性矩阵

        Args:
            stocks_data: {股票代码: 行情DataFrame} 字典
            method: 相关性方法

        Returns:
            DataFrame: 相关性矩阵
        """
        codes = list(stocks_data.keys())
        n = len(codes)
        corr_matrix = np.zeros((n, n))

        for i, code1 in enumerate(codes):
            for j, code2 in enumerate(codes):
                if i == j:
                    corr_matrix[i, j] = 1.0
                elif i < j:
                    result = self.calculate_correlation(
                        stocks_data[code1],
                        stocks_data[code2],
                        method=method
                    )
                    if 'correlation' in result:
                        corr_matrix[i, j] = result['correlation']
                        corr_matrix[j, i] = result['correlation']

        return pd.DataFrame(corr_matrix, index=codes, columns=codes)


if __name__ == "__main__":
    # 测试代码
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from data_sources.akshare_api import AKShareAPI

    api = AKShareAPI()
    analyzer = PriceCorrelationAnalyzer()

    # 获取两只股票的行情
    print("=== 获取天孚通信(300394) 和 中际旭创(300308) 最近90天行情 ===")
    start_date = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

    df1 = api.get_stock_hist("300394", start_date=start_date)
    df2 = api.get_stock_hist("300308", start_date=start_date)

    print(f"天孚通信: {len(df1)} 条数据")
    print(f"中际旭创: {len(df2)} 条数据\n")

    # 计算相关性
    print("=== 计算价格相关性 ===")
    result = analyzer.calculate_correlation(df1, df2)

    for key, value in result.items():
        print(f"{key}: {value}")

    print("\n=== 解读 ===")
    if result['correlation'] > 0.7:
        print("✅ 强正相关，两只股票走势高度一致")
    elif result['correlation'] > 0.4:
        print("⚠️ 中等正相关，有一定联动性")
    else:
        print("❌ 弱相关或负相关")

    print(f"同涨同跌率: {result['sync_rate']*100:.1f}%")

    if result['lead_lag']['lead_stock'] == 1:
        print(f"天孚通信领先 {result['lead_lag']['lag_days']} 天")
    elif result['lead_lag']['lead_stock'] == 2:
        print(f"中际旭创领先 {result['lead_lag']['lag_days']} 天")
    else:
        print("两股基本同步")
