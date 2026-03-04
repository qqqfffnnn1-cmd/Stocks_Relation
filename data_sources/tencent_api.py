"""
腾讯财经数据接口（参考 TK_MLAnalysis）
替代 AKShare，更稳定
"""
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from datetime import datetime, timedelta
from typing import Optional
import os


class TencentAPI:
    """腾讯财经数据接口"""

    def __init__(self):
        # 配置 HTTP Session（绕过代理）
        self.session = requests.Session()
        self.session.trust_env = False  # 关键：绕过 Clash 系统代理

        # 配置重试策略
        retry = Retry(
            total=3,
            backoff_factor=1.0,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=['GET']
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retry))
        self.session.mount('http://', HTTPAdapter(max_retries=retry))

        # 清除环境变量代理
        for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']:
            if key in os.environ:
                del os.environ[key]

        self.kline_url = 'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
        self.headers = {'User-Agent': 'Mozilla/5.0'}

    def _get_symbol(self, code: str) -> str:
        """转换股票代码为腾讯格式"""
        if code.startswith(('6', '9')):
            return f'sh{code}'
        return f'sz{code}'

    def get_stock_hist(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取股票历史行情

        Args:
            symbol: 股票代码（如 '300394'）
            start_date: 开始日期 'YYYYMMDD'
            end_date: 结束日期 'YYYYMMDD'

        Returns:
            DataFrame: 包含 date, open, close, high, low, volume, pct_change
        """
        try:
            qq_symbol = self._get_symbol(symbol)

            # 日期处理
            if not end_date:
                end_dt = datetime.now()
            else:
                end_dt = datetime.strptime(end_date, '%Y%m%d')

            if not start_date:
                start_dt = end_dt - timedelta(days=365)
            else:
                start_dt = datetime.strptime(start_date, '%Y%m%d')

            start_str = start_dt.strftime('%Y-%m-%d')
            end_str = end_dt.strftime('%Y-%m-%d')

            # 构造 URL
            count = max(500, (end_dt - start_dt).days)
            url = f'{self.kline_url}?param={qq_symbol},day,{start_str},{end_str},{count},qfq'

            # 请求数据
            response = self.session.get(url, headers=self.headers, timeout=20)
            response.raise_for_status()

            data = response.json()
            if data.get('code') != 0:
                print(f"腾讯API错误 {symbol}: {data.get('msg')}")
                return pd.DataFrame()

            # 解析数据
            stock_data = data.get('data', {}).get(qq_symbol, {})
            rows = stock_data.get('qfqday') or stock_data.get('day') or []

            if not rows:
                print(f"无数据 {symbol}")
                return pd.DataFrame()

            # 转换为 DataFrame
            records = []
            for row in rows:
                records.append({
                    'date': row[0],
                    'open': float(row[1]),
                    'close': float(row[2]),
                    'high': float(row[3]),
                    'low': float(row[4]),
                    'volume': float(row[5]) if len(row) > 5 else 0
                })

            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])

            # 计算涨跌幅
            df['pct_change'] = df['close'].pct_change() * 100
            df['amount'] = 0  # 腾讯API不提供成交额

            return df

        except Exception as e:
            print(f"获取 {symbol} 行情失败: {e}")
            return pd.DataFrame()

    def get_stock_info(self, symbol: str) -> dict:
        """
        获取股票基本信息（从最新行情推断）

        Args:
            symbol: 股票代码

        Returns:
            dict: 股票信息
        """
        try:
            # 获取最近1天的数据
            df = self.get_stock_hist(symbol)

            if df.empty:
                return {
                    'code': symbol,
                    'name': f'{symbol}',
                    'industry': '',
                    'latest_price': 0.0,
                    'pct_change': 0.0
                }

            latest = df.iloc[-1]
            return {
                'code': symbol,
                'name': f'{symbol}',  # 腾讯API不提供名称
                'industry': '',
                'latest_price': float(latest['close']),
                'pct_change': float(latest['pct_change']) if pd.notna(latest['pct_change']) else 0.0
            }

        except Exception as e:
            print(f"获取 {symbol} 信息失败: {e}")
            return {
                'code': symbol,
                'name': f'{symbol}',
                'industry': '',
                'latest_price': 0.0,
                'pct_change': 0.0
            }


if __name__ == "__main__":
    # 测试代码
    api = TencentAPI()

    print("=== 测试腾讯财经 API ===\n")

    # 测试1: 获取行情
    print("[1] 获取天孚通信(300394)最近30天行情")
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
    df = api.get_stock_hist("300394", start_date=start_date)
    print(f"获取 {len(df)} 条数据")
    if not df.empty:
        print(df.head())
        print()

    # 测试2: 获取股票信息
    print("[2] 获取股票信息")
    info = api.get_stock_info("300394")
    print(info)
