"""
股票关联度查询引擎
整合价格相关性、资金共振等多维度分析
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

from data_sources.tencent_api import TencentAPI
from data_sources.stock_mapper import get_mapper
from processors.price_analyzer import PriceCorrelationAnalyzer
from processors.capital_flow import CapitalResonanceAnalyzer


class StockRelationQuery:
    """股票关联度查询引擎"""

    def __init__(self):
        self.api = TencentAPI()
        self.price_analyzer = PriceCorrelationAnalyzer()
        self.capital_analyzer = CapitalResonanceAnalyzer()
        self.mapper = get_mapper()

    def analyze_stock_relation(self, stock1: str, stock2: str, days: int = 90) -> Dict:
        """
        综合分析两只股票的关联度

        Args:
            stock1: 股票代码1（如 '300394'）
            stock2: 股票代码2
            days: 分析天数

        Returns:
            dict: 综合关联度分析结果
        """
        print(f"\n{'='*60}")
        print(f"正在分析 {stock1} vs {stock2} 的关联度...")
        print(f"{'='*60}\n")

        # 1. 获取股票基本信息
        print("[1/4] 获取股票信息...")
        info1 = self.api.get_stock_info(stock1)
        info2 = self.api.get_stock_info(stock2)

        # 即使获取信息失败，也继续分析（使用默认值）
        if not info1:
            info1 = {
                'code': stock1,
                'name': self.mapper.get_name(stock1) or stock1,
                'industry': '',
                'latest_price': 0.0,
                'pct_change': 0.0
            }
        else:
            info1['name'] = self.mapper.get_name(stock1) or stock1

        if not info2:
            info2 = {
                'code': stock2,
                'name': self.mapper.get_name(stock2) or stock2,
                'industry': '',
                'latest_price': 0.0,
                'pct_change': 0.0
            }
        else:
            info2['name'] = self.mapper.get_name(stock2) or stock2

        # 2. 获取历史行情
        print("[2/4] 获取历史行情数据...")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")

        df1 = self.api.get_stock_hist(stock1, start_date=start_date)
        df2 = self.api.get_stock_hist(stock2, start_date=start_date)

        if df1.empty or df2.empty:
            return {'error': '无法获取行情数据，请检查股票代码或网络连接'}

        # 3. 价格相关性分析
        print("[3/4] 计算价格相关性...")
        price_result = self.price_analyzer.calculate_correlation(df1, df2)

        # 4. 资金共振分析
        print("[4/4] 分析资金共振...")
        capital_result = self.capital_analyzer.analyze_seat_overlap(stock1, stock2, days)
        capital_score = self.capital_analyzer.calculate_capital_resonance_score(stock1, stock2, days)

        # 5. 计算综合评分
        overall_score = self._calculate_overall_score(price_result, capital_score)

        return {
            'stock1': info1,
            'stock2': info2,
            'price_correlation': price_result,
            'capital_resonance': {
                'score': capital_score,
                'details': capital_result
            },
            'overall_score': overall_score,
            'analysis_period': {
                'days': days,
                'start_date': start_date,
                'end_date': datetime.now().strftime("%Y%m%d")
            }
        }

    def _calculate_overall_score(self, price_result: Dict, capital_score: int) -> Dict:
        """
        计算综合关联度评分

        Args:
            price_result: 价格相关性结果
            capital_score: 资金共振评分

        Returns:
            dict: 综合评分和等级
        """
        # 价格相关性评分 (0-100)
        # 改进：更重视涨跌幅相关性（短期波动）而不是价格相关性（长期趋势）
        corr = price_result.get('correlation', 0)
        pct_corr = price_result.get('pct_correlation', 0)  # 涨跌幅相关性
        sync_rate = price_result.get('sync_rate', 0)

        # 新算法：涨跌幅相关性40% + 同涨同跌率60%
        # 只有正相关才算分，负相关不算
        pct_score = max(0, pct_corr) * 40  # 0-40分
        sync_score = sync_rate * 60  # 0-60分
        price_score = pct_score + sync_score

        # 龙虎榜资金共振作为加分项（0-30分）
        # 基础分 = 价格评分（0-100）
        # 加分 = 资金共振评分 × 0.3（最多加30分）
        capital_bonus = int(capital_score * 0.3)

        # 综合评分 = 价格评分 + 资金加分（可以超过100分）
        overall = int(price_score + capital_bonus)

        # 评级（适应0-130分范围）
        if overall >= 90:
            grade = "S (极强关联)"
            stars = "★★★★★"
        elif overall >= 70:
            grade = "A (强关联)"
            stars = "★★★★☆"
        elif overall >= 50:
            grade = "B (中等关联)"
            stars = "★★★☆☆"
        elif overall >= 30:
            grade = "C (弱关联)"
            stars = "★★☆☆☆"
        else:
            grade = "D (无明显关联)"
            stars = "★☆☆☆☆"

        return {
            'score': overall,
            'grade': grade,
            'stars': stars,
            'price_score': int(price_score),
            'capital_score': capital_score
        }

    def generate_report(self, result: Dict) -> str:
        """
        生成 Markdown 格式的分析报告

        Args:
            result: analyze_stock_relation 的返回结果

        Returns:
            str: Markdown 报告
        """
        if 'error' in result:
            return f"# 错误\n\n{result['error']}"

        stock1 = result['stock1']
        stock2 = result['stock2']
        price = result['price_correlation']
        capital = result['capital_resonance']
        overall = result['overall_score']

        report = f"""# 股票关联度分析报告

## 基本信息

| 项目 | 股票1 | 股票2 |
|------|-------|-------|
| 代码 | {stock1['code']} | {stock2['code']} |
| 名称 | {stock1['name']} | {stock2['name']} |
| 行业 | {stock1.get('industry', 'N/A')} | {stock2.get('industry', 'N/A')} |
| 最新价 | {stock1['latest_price']:.2f} | {stock2['latest_price']:.2f} |
| 涨跌幅 | {stock1['pct_change']:.2f}% | {stock2['pct_change']:.2f}% |

---

## 综合评分: {overall['score']}/100 {overall['stars']}

**评级**: {overall['grade']}

- 价格联动评分: {overall['price_score']}/100
- 资金共振评分: {overall['capital_score']}/100

---

## 价格联动分析

### 相关性指标
- **价格相关系数**: {price['correlation']:.4f}
- **涨跌幅相关系数**: {price['pct_correlation']:.4f}
- **同涨同跌率**: {price['sync_rate']*100:.1f}% ({price['sync_days']}/{price['total_days']}天)
  - 同时上涨: {price['both_up_days']}天
  - 同时下跌: {price['both_down_days']}天

### 波动特征
- **波动相似度**: {price['volatility_ratio']:.4f}

### 领先滞后关系
"""

        lead_lag = price['lead_lag']
        if lead_lag['lead_stock'] == 0:
            report += "- 两股基本**同步**，无明显领先滞后\n"
        elif lead_lag['lead_stock'] == 1:
            report += f"- **{stock1['name']}** 领先 {lead_lag['lag_days']} 天（相关系数: {lead_lag['correlation']:.4f}）\n"
        else:
            report += f"- **{stock2['name']}** 领先 {lead_lag['lag_days']} 天（相关系数: {lead_lag['correlation']:.4f}）\n"

        report += f"\n### 分析周期\n- {price['date_range']['start']} 至 {price['date_range']['end']}\n"

        # 资金共振部分
        report += "\n---\n\n## 资金共振分析\n\n"

        cap_details = capital['details']
        if 'error' in cap_details:
            report += f"⚠️ {cap_details['error']}\n"
        else:
            report += f"### 龙虎榜统计\n"
            report += f"- {stock1['name']} 上榜天数: {cap_details['stock1_lhb_days']}天\n"
            report += f"- {stock2['name']} 上榜天数: {cap_details['stock2_lhb_days']}天\n"
            report += f"- 共同席位数量: {cap_details['overlap_count']}个\n"
            report += f"- 席位重叠率: {cap_details['overlap_rate']*100:.1f}%\n\n"

            if cap_details['common_seats']:
                report += "### 共同席位 Top 10\n\n"
                report += "| 席位名称 | 股票1出现次数 | 股票2出现次数 | 合计 |\n"
                report += "|---------|--------------|--------------|------|\n"

                for seat in cap_details['common_seats']:
                    report += f"| {seat['seat']} | {seat['stock1_count']} | {seat['stock2_count']} | {seat['total']} |\n"

        # 结论
        report += "\n---\n\n## 分析结论\n\n"

        if overall['score'] >= 80:
            report += "✅ **强关联**：两只股票在价格走势和资金流向上高度一致，存在显著的联动效应。\n"
        elif overall['score'] >= 60:
            report += "⚠️ **中等关联**：两只股票有一定的联动性，但并非完全同步。\n"
        elif overall['score'] >= 40:
            report += "❌ **弱关联**：两只股票关联度较低，走势相对独立。\n"
        else:
            report += "❌ **无明显关联**：两只股票基本独立，无明显联动关系。\n"

        # 投资建议
        report += "\n### 投资参考\n\n"

        if price['correlation'] > 0.7:
            report += "- 价格高度正相关，可考虑配对交易或板块轮动策略\n"
        elif price['correlation'] < -0.5:
            report += "- 价格负相关，可用于对冲或分散风险\n"

        if capital['score'] > 60:
            report += "- 资金共振明显，游资可能同时关注这两只股票\n"

        if lead_lag['lead_stock'] != 0:
            report += f"- 存在领先滞后关系，可关注领先股的信号作用\n"

        report += f"\n---\n\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return report


if __name__ == "__main__":
    # 测试代码
    query = StockRelationQuery()

    # 分析天孚通信 vs 中际旭创
    result = query.analyze_stock_relation("300394", "300308", days=90)

    # 生成报告
    report = query.generate_report(result)

    # 打印报告
    print("\n" + report)

    # 保存报告
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"relation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n✅ 报告已保存至: {output_file}")
