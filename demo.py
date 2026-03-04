"""
股票关联度分析 - 演示版本
使用模拟数据展示完整功能
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent))

from api.query_engine import StockRelationQuery
from processors.price_analyzer import PriceCorrelationAnalyzer


def generate_mock_data(stock_code: str, days: int = 90, correlation: float = 0.75, dates=None) -> pd.DataFrame:
    """
    生成模拟股票数据

    Args:
        stock_code: 股票代码
        days: 天数
        correlation: 与基准的相关性
        dates: 指定日期序列（可选）

    Returns:
        DataFrame: 模拟行情数据
    """
    # 生成交易日（排除周末）
    if dates is None:
        all_dates = pd.date_range(end=datetime.now(), periods=days*2, freq='D')
        # 只保留工作日
        dates = all_dates[all_dates.dayofweek < 5][:days]

    actual_days = len(dates)

    # 生成随机价格走势
    np.random.seed(int(stock_code) % 1000)

    # 基准走势
    base_returns = np.random.randn(actual_days) * 0.03

    # 个股走势 = 相关部分 + 独立部分
    stock_returns = correlation * base_returns + np.sqrt(1 - correlation**2) * np.random.randn(actual_days) * 0.03

    # 计算价格
    initial_price = 100 + np.random.rand() * 100
    prices = initial_price * np.exp(np.cumsum(stock_returns))

    df = pd.DataFrame({
        'date': dates,
        'open': prices * (1 + np.random.randn(actual_days) * 0.01),
        'close': prices,
        'high': prices * (1 + np.abs(np.random.randn(actual_days)) * 0.02),
        'low': prices * (1 - np.abs(np.random.randn(actual_days)) * 0.02),
        'volume': np.random.randint(1000000, 10000000, actual_days),
        'amount': prices * np.random.randint(1000000, 10000000, actual_days),
        'pct_change': stock_returns * 100
    })

    return df


def demo_analysis():
    """演示完整分析流程"""

    print("\n" + "="*70)
    print("股票关联度分析工具 - 演示版本")
    print("="*70 + "\n")

    # 生成模拟数据
    print("[1/3] 生成模拟数据...")

    # 生成共同的日期序列
    all_dates = pd.date_range(end=datetime.now(), periods=180, freq='D')
    common_dates = all_dates[all_dates.dayofweek < 5][:90]

    df1 = generate_mock_data("300394", days=90, correlation=0.78, dates=common_dates)
    df2 = generate_mock_data("300308", days=90, correlation=0.78, dates=common_dates)

    print(f"  天孚通信(300394): {len(df1)} 条数据")
    print(f"  中际旭创(300308): {len(df2)} 条数据\n")

    # 价格相关性分析
    print("[2/3] 计算价格相关性...")
    analyzer = PriceCorrelationAnalyzer()
    result = analyzer.calculate_correlation(df1, df2)

    # 检查是否有错误
    if 'error' in result:
        print(f"  错误: {result['error']}")
        return

    print("\n" + "-"*70)
    print("价格联动分析结果")
    print("-"*70)
    print(f"  价格相关系数: {result['correlation']:.4f}")
    print(f"  涨跌幅相关系数: {result['pct_correlation']:.4f}")
    print(f"  同涨同跌率: {result['sync_rate']*100:.1f}% ({result['sync_days']}/{result['total_days']}天)")
    print(f"    - 同时上涨: {result['both_up_days']}天")
    print(f"    - 同时下跌: {result['both_down_days']}天")
    print(f"  波动相似度: {result['volatility_ratio']:.4f}")

    lead_lag = result['lead_lag']
    if lead_lag['lead_stock'] == 0:
        print(f"  领先滞后: 基本同步")
    elif lead_lag['lead_stock'] == 1:
        print(f"  领先滞后: 天孚通信领先 {lead_lag['lag_days']} 天 (相关: {lead_lag['correlation']:.4f})")
    else:
        print(f"  领先滞后: 中际旭创领先 {lead_lag['lag_days']} 天 (相关: {lead_lag['correlation']:.4f})")

    print(f"  分析周期: {result['date_range']['start']} 至 {result['date_range']['end']}")

    # 综合评分
    print("\n" + "-"*70)
    print("综合评分")
    print("-"*70)

    corr = result['correlation']
    sync_rate = result['sync_rate']
    price_score = int(abs(corr) * 50 + sync_rate * 50)

    # 模拟资金共振评分
    capital_score = 65  # 模拟值

    overall_score = int(price_score * 0.6 + capital_score * 0.4)

    if overall_score >= 80:
        grade = "A (强关联)"
        stars = "★★★★★"
    elif overall_score >= 60:
        grade = "B (中等关联)"
        stars = "★★★★☆"
    elif overall_score >= 40:
        grade = "C (弱关联)"
        stars = "★★★☆☆"
    else:
        grade = "D (无明显关联)"
        stars = "★★☆☆☆"

    print(f"  价格联动评分: {price_score}/100")
    print(f"  资金共振评分: {capital_score}/100 (模拟)")
    print(f"  综合评分: {overall_score}/100 {stars}")
    print(f"  评级: {grade}")

    # 生成完整报告
    print("\n" + "-"*70)
    print("生成分析报告")
    print("-"*70)

    report = f"""# 股票关联度分析报告（演示版）

## 基本信息

| 项目 | 股票1 | 股票2 |
|------|-------|-------|
| 代码 | 300394 | 300308 |
| 名称 | 天孚通信 | 中际旭创 |
| 行业 | 通信设备 | 通信设备 |
| 最新价 | {df1.iloc[-1]['close']:.2f} | {df2.iloc[-1]['close']:.2f} |
| 涨跌幅 | {df1.iloc[-1]['pct_change']:.2f}% | {df2.iloc[-1]['pct_change']:.2f}% |

---

## 综合评分: {overall_score}/100 {stars}

**评级**: {grade}

- 价格联动评分: {price_score}/100
- 资金共振评分: {capital_score}/100 (模拟)

---

## 价格联动分析

### 相关性指标
- **价格相关系数**: {result['correlation']:.4f}
- **涨跌幅相关系数**: {result['pct_correlation']:.4f}
- **同涨同跌率**: {result['sync_rate']*100:.1f}% ({result['sync_days']}/{result['total_days']}天)
  - 同时上涨: {result['both_up_days']}天
  - 同时下跌: {result['both_down_days']}天

### 波动特征
- **波动相似度**: {result['volatility_ratio']:.4f}

### 领先滞后关系
"""

    if lead_lag['lead_stock'] == 0:
        report += "- 两股基本**同步**，无明显领先滞后\n"
    elif lead_lag['lead_stock'] == 1:
        report += f"- **天孚通信** 领先 {lead_lag['lag_days']} 天（相关系数: {lead_lag['correlation']:.4f}）\n"
    else:
        report += f"- **中际旭创** 领先 {lead_lag['lag_days']} 天（相关系数: {lead_lag['correlation']:.4f}）\n"

    report += f"""
### 分析周期
- {result['date_range']['start']} 至 {result['date_range']['end']}

---

## 资金共振分析（模拟数据）

### 龙虎榜统计
- 天孚通信 上榜天数: 8天
- 中际旭创 上榜天数: 6天
- 共同席位数量: 5个
- 席位重叠率: 35.7%

### 共同席位 Top 5

| 席位名称 | 股票1出现次数 | 股票2出现次数 | 合计 |
|---------|--------------|--------------|------|
| 中信证券上海溧阳路 | 3 | 2 | 5 |
| 华泰证券深圳益田路 | 2 | 2 | 4 |
| 国泰君安深圳益田路 | 2 | 1 | 3 |
| 招商证券深圳蛇口 | 1 | 2 | 3 |
| 中信证券杭州延安路 | 1 | 1 | 2 |

---

## 分析结论

"""

    if overall_score >= 80:
        report += "[OK] **强关联**：两只股票在价格走势和资金流向上高度一致，存在显著的联动效应。\n"
    elif overall_score >= 60:
        report += "[!] **中等关联**：两只股票有一定的联动性，但并非完全同步。\n"
    else:
        report += "[X] **弱关联**：两只股票关联度较低，走势相对独立。\n"

    report += """
### 投资参考

- 价格高度正相关，可考虑配对交易或板块轮动策略
- 资金共振明显，游资可能同时关注这两只股票
- 建议关注领先股的信号作用

---

*报告生成时间: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "*\n"
    report += "*注: 本报告使用模拟数据演示，实际使用时将接入真实行情数据*\n"

    # 保存报告
    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"demo_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n[OK] 报告已保存至: {output_file}")

    print("\n" + "="*70)
    print("演示完成！")
    print("="*70)
    print("\n提示:")
    print("  - 实际使用时将自动从 AKShare 获取真实行情数据")
    print("  - 资金共振分析将整合 TK_LHB 龙虎榜数据")
    print("  - 支持通过 Skill 调用: /stock-relation 300394 300308")
    print()


if __name__ == "__main__":
    demo_analysis()
