"""
AKShare 数据接口封装
提供股票行情、龙虎榜、资金流向等数据
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List
import time
import os


class AKShareAPI:
    """AKShare 数据接口"""

    def __init__(self):
        self.cache = {}
        # 关键：绕过 Clash 系统代理
        self._bypass_proxy()

    def _bypass_proxy(self):
        """绕过系统代理（参考 TK_MLAnalysis 的做法）"""
        # 清除环境变量中的代理设置
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
            if key in os.environ:
                del os.environ[key]

        # 配置 requests 不使用系统代理
        try:
            import requests
            # 创建一个不使用代理的 session
            session = requests.Session()
            session.trust_env = False  # 关键：不读取环境变量的代理设置

            # 尝试让 akshare 使用这个 session（如果可能）
            # 注意：akshare 内部可能不支持自定义 session，但清除环境变量应该足够了
        except:
            pass

    def get_stock_hist(self, symbol: str, period: str = "daily",
                       start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票历史行情

        Args:
            symbol: 股票代码，如 '000001' 或 '600000'
            period: 周期 'daily'/'weekly'/'monthly'
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'

        Returns:
            DataFrame: 包含日期、开盘、收盘、最高、最低、成交量等
        """
        try:
            # 判断市场
            if symbol.startswith('6'):
                adjust = "qfq"  # 前复权
            else:
                adjust = "qfq"

            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=period,
                start_date=start_date or (datetime.now() - timedelta(days=365)).strftime("%Y%m%d"),
                end_date=end_date or datetime.now().strftime("%Y%m%d"),
                adjust=adjust
            )

            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '涨跌幅': 'pct_change'
            })

            df['date'] = pd.to_datetime(df['date'])
            return df

        except Exception as e:
            print(f"获取 {symbol} 行情失败: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票基本信息

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票名称、行业、概念等信息
        """
        try:
            # 方法1: 尝试获取个股实时行情（更快）
            try:
                df = ak.stock_zh_a_hist(
                    symbol=symbol,
                    period="daily",
                    adjust="qfq"
                )

                if not df.empty:
                    latest = df.iloc[-1]
                    return {
                        'code': symbol,
                        'name': f'股票{symbol}',  # 默认名称
                        'industry': '',
                        'latest_price': float(latest['收盘']),
                        'pct_change': float(latest['涨跌幅'])
                    }
            except:
                pass

            # 方法2: 获取全市场行情（较慢，作为备选）
            df = ak.stock_zh_a_spot_em()
            stock_info = df[df['代码'] == symbol]

            if not stock_info.empty:
                return {
                    'code': symbol,
                    'name': stock_info.iloc[0]['名称'],
                    'industry': stock_info.iloc[0].get('行业', ''),
                    'latest_price': float(stock_info.iloc[0]['最新价']),
                    'pct_change': float(stock_info.iloc[0]['涨跌幅'])
                }

            # 如果都失败，返回基本信息
            return {
                'code': symbol,
                'name': f'股票{symbol}',
                'industry': '',
                'latest_price': 0.0,
                'pct_change': 0.0
            }

        except Exception as e:
            print(f"获取 {symbol} 信息失败: {e}")
            # 返回基本信息而不是空字典
            return {
                'code': symbol,
                'name': f'股票{symbol}',
                'industry': '',
                'latest_price': 0.0,
                'pct_change': 0.0
            }

    def get_lhb_detail(self, start_date: str, end_date: str) -> pd.DataFrame:
        """
        获取龙虎榜数据

        Args:
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'

        Returns:
            DataFrame: 龙虎榜明细
        """
        try:
            df = ak.stock_lhb_detail_em(
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"获取龙虎榜失败: {e}")
            return pd.DataFrame()

    def get_capital_flow(self, symbol: str) -> pd.DataFrame:
        """
        获取个股资金流向

        Args:
            symbol: 股票代码

        Returns:
            DataFrame: 主力资金、超大单、大单、中单、小单流向
        """
        try:
            df = ak.stock_individual_fund_flow(stock=symbol, market="沪深A股")
            return df
        except Exception as e:
            print(f"获取 {symbol} 资金流向失败: {e}")
            return pd.DataFrame()

    def get_concept_stocks(self, concept: str) -> List[str]:
        """
        获取概念板块成分股

        Args:
            concept: 概念名称，如 'AI'、'光模块'

        Returns:
            List[str]: 股票代码列表
        """
        try:
            # 获取概念板块列表
            concept_df = ak.stock_board_concept_name_em()

            # 模糊匹配概念名称
            matched = concept_df[concept_df['板块名称'].str.contains(concept, na=False)]

            if matched.empty:
                return []

            # 获取第一个匹配的概念成分股
            concept_code = matched.iloc[0]['板块代码']
            stocks_df = ak.stock_board_concept_cons_em(symbol=matched.iloc[0]['板块名称'])

            return stocks_df['代码'].tolist()

        except Exception as e:
            print(f"获取概念 {concept} 成分股失败: {e}")
            return []

    def get_industry_stocks(self, industry: str) -> List[str]:
        """
        获取行业板块成分股

        Args:
            industry: 行业名称，如 '通信设备'、'半导体'

        Returns:
            List[str]: 股票代码列表
        """
        try:
            # 获取行业板块列表
            industry_df = ak.stock_board_industry_name_em()

            # 模糊匹配行业名称
            matched = industry_df[industry_df['板块名称'].str.contains(industry, na=False)]

            if matched.empty:
                return []

            # 获取成分股
            stocks_df = ak.stock_board_industry_cons_em(symbol=matched.iloc[0]['板块名称'])

            return stocks_df['代码'].tolist()

        except Exception as e:
            print(f"获取行业 {industry} 成分股失败: {e}")
            return []


if __name__ == "__main__":
    # 测试代码
    api = AKShareAPI()

    # 测试1: 获取股票行情
    print("=== 测试1: 获取天孚通信(300394)最近30天行情 ===")
    hist = api.get_stock_hist("300394", start_date="20260201")
    print(hist.head())
    print(f"共 {len(hist)} 条数据\n")

    # 测试2: 获取股票信息
    print("=== 测试2: 获取股票基本信息 ===")
    info = api.get_stock_info("300394")
    print(info)
    print()

    # 测试3: 获取概念成分股
    print("=== 测试3: 获取光模块概念成分股 ===")
    stocks = api.get_concept_stocks("光模块")
    print(f"光模块概念共 {len(stocks)} 只股票")
    print(stocks[:10])
