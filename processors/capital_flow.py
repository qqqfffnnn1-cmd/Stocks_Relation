"""
龙虎榜资金共振分析
整合 TK_LHB 数据，分析游资席位重叠、资金共振等
"""
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict


class CapitalResonanceAnalyzer:
    """资金共振分析器"""

    def __init__(self, lhb_data_path: str = None):
        """
        Args:
            lhb_data_path: TK_LHB 数据路径，默认为 ../TK_LHB/data/
        """
        if lhb_data_path is None:
            base_path = Path(__file__).parent.parent.parent
            self.lhb_path = base_path / "TK_LHB" / "data"
        else:
            self.lhb_path = Path(lhb_data_path)

    def load_lhb_data(self, days: int = 90) -> pd.DataFrame:
        """
        加载最近N天的龙虎榜数据

        Args:
            days: 天数

        Returns:
            DataFrame: 龙虎榜数据
        """
        all_data = []
        start_date = datetime.now() - timedelta(days=days)

        # 遍历 data 目录下的所有日期文件夹
        if not self.lhb_path.exists():
            print(f"[!] TK_LHB 数据路径不存在: {self.lhb_path}")
            return pd.DataFrame()

        for date_folder in self.lhb_path.iterdir():
            if not date_folder.is_dir():
                continue

            try:
                folder_date = datetime.strptime(date_folder.name, "%Y%m%d")
                if folder_date < start_date:
                    continue

                # 读取该日期的龙虎榜数据
                lhb_file = date_folder / "lhb_detail.csv"
                if lhb_file.exists():
                    df = pd.read_csv(lhb_file)
                    df['date'] = folder_date
                    all_data.append(df)

            except ValueError:
                continue

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)

    def analyze_seat_overlap(self, stock1: str, stock2: str, days: int = 90) -> Dict:
        """
        分析两只股票的龙虎榜席位重叠

        Args:
            stock1: 股票代码1
            stock2: 股票代码2
            days: 分析天数

        Returns:
            dict: 席位重叠分析结果
        """
        lhb_df = self.load_lhb_data(days)

        if lhb_df.empty:
            return {'error': '无龙虎榜数据'}

        # 筛选两只股票的龙虎榜记录
        stock1_lhb = lhb_df[lhb_df['代码'] == stock1]
        stock2_lhb = lhb_df[lhb_df['代码'] == stock2]

        if stock1_lhb.empty or stock2_lhb.empty:
            return {
                'overlap_count': 0,
                'stock1_lhb_days': len(stock1_lhb),
                'stock2_lhb_days': len(stock2_lhb),
                'common_seats': []
            }

        # 提取买入席位
        stock1_seats = set(stock1_lhb['买方营业部'].dropna().unique())
        stock2_seats = set(stock2_lhb['买方营业部'].dropna().unique())

        # 计算重叠席位
        common_seats = stock1_seats & stock2_seats

        # 统计每个共同席位的出现次数
        seat_stats = []
        for seat in common_seats:
            count1 = len(stock1_lhb[stock1_lhb['买方营业部'] == seat])
            count2 = len(stock2_lhb[stock2_lhb['买方营业部'] == seat])
            seat_stats.append({
                'seat': seat,
                'stock1_count': count1,
                'stock2_count': count2,
                'total': count1 + count2
            })

        # 按总次数排序
        seat_stats.sort(key=lambda x: x['total'], reverse=True)

        return {
            'overlap_count': len(common_seats),
            'stock1_lhb_days': len(stock1_lhb['date'].unique()),
            'stock2_lhb_days': len(stock2_lhb['date'].unique()),
            'stock1_total_seats': len(stock1_seats),
            'stock2_total_seats': len(stock2_seats),
            'common_seats': seat_stats[:10],  # 返回前10个
            'overlap_rate': round(len(common_seats) / max(len(stock1_seats), len(stock2_seats)), 4) if max(len(stock1_seats), len(stock2_seats)) > 0 else 0
        }

    def find_hot_money_overlap(self, stock1: str, stock2: str, days: int = 90) -> List[str]:
        """
        找出同时操作两只股票的知名游资

        Args:
            stock1: 股票代码1
            stock2: 股票代码2
            days: 分析天数

        Returns:
            List[str]: 游资名单
        """
        # 知名游资关键词（可扩展）
        hot_money_keywords = [
            '章盟主', '小鳄鱼', '赵老哥', '欢乐海岸', '成都系',
            '佛山系', '温州帮', '宁波系', '杭州系', '深圳系'
        ]

        result = self.analyze_seat_overlap(stock1, stock2, days)

        if 'common_seats' not in result:
            return []

        hot_money_list = []
        for seat_info in result['common_seats']:
            seat = seat_info['seat']
            for keyword in hot_money_keywords:
                if keyword in seat:
                    hot_money_list.append(seat)
                    break

        return hot_money_list

    def calculate_capital_resonance_score(self, stock1: str, stock2: str, days: int = 90) -> int:
        """
        计算资金共振评分 (0-100)

        Args:
            stock1: 股票代码1
            stock2: 股票代码2
            days: 分析天数

        Returns:
            int: 共振评分
        """
        result = self.analyze_seat_overlap(stock1, stock2, days)

        if 'error' in result or result['overlap_count'] == 0:
            return 0

        # 评分逻辑
        score = 0

        # 1. 席位重叠数量 (最高40分)
        overlap_count = result['overlap_count']
        score += min(overlap_count * 4, 40)

        # 2. 重叠率 (最高30分)
        overlap_rate = result['overlap_rate']
        score += int(overlap_rate * 30)

        # 3. 知名游资加成 (最高30分)
        hot_money = self.find_hot_money_overlap(stock1, stock2, days)
        score += min(len(hot_money) * 10, 30)

        return min(score, 100)


if __name__ == "__main__":
    # 测试代码
    analyzer = CapitalResonanceAnalyzer()

    print("=== 测试龙虎榜数据加载 ===")
    lhb_df = analyzer.load_lhb_data(days=30)
    print(f"加载了 {len(lhb_df)} 条龙虎榜记录")

    if not lhb_df.empty:
        print(f"涉及 {lhb_df['代码'].nunique()} 只股票")
        print(f"日期范围: {lhb_df['date'].min()} 至 {lhb_df['date'].max()}\n")

        print("=== 测试席位重叠分析 ===")
        result = analyzer.analyze_seat_overlap("300394", "300308", days=90)

        for key, value in result.items():
            if key != 'common_seats':
                print(f"{key}: {value}")

        if result.get('common_seats'):
            print("\n共同席位 Top 5:")
            for seat in result['common_seats'][:5]:
                print(f"  {seat['seat']}: 股票1出现{seat['stock1_count']}次, 股票2出现{seat['stock2_count']}次")

        print("\n=== 资金共振评分 ===")
        score = analyzer.calculate_capital_resonance_score("300394", "300308", days=90)
        print(f"评分: {score}/100")
    else:
        print("[!] 未找到龙虎榜数据，请确保 TK_LHB 已运行并生成数据")
