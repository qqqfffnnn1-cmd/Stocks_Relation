"""
批量分析板块内股票关联度
"""
import sys
from pathlib import Path
import json
from datetime import datetime
from itertools import combinations
import time

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from api.query_engine import StockRelationQuery
from data_sources.stock_mapper import get_mapper


# 板块股票池定义
SECTOR_STOCKS = {
    '光模块': [
        '300394',  # 天孚通信
        '300308',  # 中际旭创
        '300502',  # 新易盛
        '002281',  # 光迅科技
        '300620',  # 光库科技
        '688498',  # 源杰科技
        '688396',  # 华润微
        '002049',  # 紫光国微
        '300613',  # 富瀚微
        '688008',  # 澜起科技
        '002156',  # 通富微电
        '603986',  # 兆易创新
        '688126',  # 沪硅产业
        '688981',  # 中芯国际
        '688012',  # 中微公司
    ],
    'AI芯片': [
        '688256',  # 寒武纪
        '688041',  # 海光信息
        '688981',  # 中芯国际
        '688008',  # 澜起科技
        '002049',  # 紫光国微
        '603986',  # 兆易创新
        '688012',  # 中微公司
        '688126',  # 沪硅产业
        '688396',  # 华润微
        '002156',  # 通富微电
    ],
}


def batch_analyze_sector(sector_name: str, days: int = 90, output_dir: str = 'outputs'):
    """
    批量分析板块内股票关联度

    Args:
        sector_name: 板块名称
        days: 分析天数
        output_dir: 输出目录
    """
    if sector_name not in SECTOR_STOCKS:
        print(f"错误：未找到板块 '{sector_name}'")
        print(f"可用板块：{list(SECTOR_STOCKS.keys())}")
        return

    stocks = SECTOR_STOCKS[sector_name]
    mapper = get_mapper()
    query_engine = StockRelationQuery()

    # 获取股票名称
    stock_names = {code: mapper.get_name(code) for code in stocks}

    print(f"\n{'='*60}")
    print(f"批量分析：{sector_name} 板块")
    print(f"{'='*60}")
    print(f"股票数量：{len(stocks)}")
    print(f"配对数量：{len(stocks) * (len(stocks) - 1) // 2}")
    print(f"分析周期：{days}天")
    print(f"\n股票列表：")
    for code in stocks:
        print(f"  {code} - {stock_names[code]}")
    print(f"{'='*60}\n")

    # 生成所有配对
    pairs = list(combinations(stocks, 2))
    total_pairs = len(pairs)

    # 存储结果
    results = []
    grade_stats = {'S': 0, 'A': 0, 'B': 0, 'C': 0, 'D': 0}
    failed_pairs = []

    start_time = time.time()

    for idx, (stock1, stock2) in enumerate(pairs, 1):
        name1 = stock_names[stock1]
        name2 = stock_names[stock2]

        print(f"[{idx}/{total_pairs}] 分析 {name1}({stock1}) vs {name2}({stock2})...", end=' ')

        try:
            # 分析关联度
            result = query_engine.analyze_stock_relation(stock1, stock2, days=days)

            if 'error' in result:
                print(f"失败: {result['error']}")
                failed_pairs.append({
                    'stock1': stock1,
                    'stock2': stock2,
                    'name1': name1,
                    'name2': name2,
                    'error': result['error']
                })
                continue

            # 提取关键信息
            overall = result['overall_score']
            price = result['price_correlation']

            score = overall['score']
            grade = overall['grade'].split()[0]  # 提取等级字母

            # 统计等级
            grade_stats[grade] += 1

            # 保存结果
            pair_result = {
                'stock1': stock1,
                'stock2': stock2,
                'name1': name1,
                'name2': name2,
                'score': score,
                'grade': grade,
                'price_score': overall['price_score'],
                'capital_score': overall['capital_score'],
                'pct_corr': price['pct_correlation'],
                'sync_rate': price['sync_rate'],
                'both_up_days': price['both_up_days'],
                'both_down_days': price['both_down_days'],
                'total_days': price['total_days'],
            }
            results.append(pair_result)

            print(f"完成 - {score}分 ({grade}级)")

        except Exception as e:
            print(f"异常: {e}")
            failed_pairs.append({
                'stock1': stock1,
                'stock2': stock2,
                'name1': name1,
                'name2': name2,
                'error': str(e)
            })

        # 避免请求过快
        time.sleep(0.5)

    elapsed_time = time.time() - start_time

    # 按得分排序
    results.sort(key=lambda x: x['score'], reverse=True)

    # 生成报告
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存JSON结果
    json_file = output_path / f'{sector_name}_关联度分析_{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'sector': sector_name,
            'analysis_date': datetime.now().isoformat(),
            'days': days,
            'total_stocks': len(stocks),
            'total_pairs': total_pairs,
            'successful_pairs': len(results),
            'failed_pairs': len(failed_pairs),
            'elapsed_time': elapsed_time,
            'grade_stats': grade_stats,
            'results': results,
            'failed': failed_pairs
        }, f, ensure_ascii=False, indent=2)

    # 生成Markdown报告
    md_file = output_path / f'{sector_name}_关联度分析_{timestamp}.md'
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# {sector_name} 板块关联度分析报告\n\n")
        f.write(f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"**分析周期**: {days}天\n\n")
        f.write(f"**耗时**: {elapsed_time:.1f}秒\n\n")

        f.write(f"## 统计概览\n\n")
        f.write(f"- 股票数量: {len(stocks)}\n")
        f.write(f"- 配对总数: {total_pairs}\n")
        f.write(f"- 成功分析: {len(results)}\n")
        f.write(f"- 失败数量: {len(failed_pairs)}\n\n")

        f.write(f"## 等级分布\n\n")
        f.write(f"| 等级 | 数量 | 占比 |\n")
        f.write(f"|------|------|------|\n")
        for grade in ['S', 'A', 'B', 'C', 'D']:
            count = grade_stats[grade]
            pct = count / len(results) * 100 if results else 0
            f.write(f"| {grade} | {count} | {pct:.1f}% |\n")

        f.write(f"\n## Top 20 强关联配对\n\n")
        f.write(f"| 排名 | 股票1 | 股票2 | 得分 | 等级 | 价格得分 | 同步率 | 同涨天数 | 同跌天数 |\n")
        f.write(f"|------|-------|-------|------|------|----------|--------|----------|----------|\n")

        for idx, r in enumerate(results[:20], 1):
            f.write(f"| {idx} | {r['name1']}({r['stock1']}) | {r['name2']}({r['stock2']}) | "
                   f"{r['score']} | {r['grade']} | {r['price_score']} | "
                   f"{r['sync_rate']*100:.1f}% | {r['both_up_days']} | {r['both_down_days']} |\n")

        f.write(f"\n## 完整结果\n\n")
        f.write(f"| 排名 | 股票1 | 股票2 | 得分 | 等级 | 涨跌幅相关 | 同步率 |\n")
        f.write(f"|------|-------|-------|------|------|------------|--------|\n")

        for idx, r in enumerate(results, 1):
            f.write(f"| {idx} | {r['name1']}({r['stock1']}) | {r['name2']}({r['stock2']}) | "
                   f"{r['score']} | {r['grade']} | {r['pct_corr']:.3f} | {r['sync_rate']*100:.1f}% |\n")

        if failed_pairs:
            f.write(f"\n## 失败配对\n\n")
            for fp in failed_pairs:
                f.write(f"- {fp['name1']}({fp['stock1']}) vs {fp['name2']}({fp['stock2']}): {fp['error']}\n")

    # 打印总结
    print(f"\n{'='*60}")
    print(f"分析完成！")
    print(f"{'='*60}")
    print(f"总耗时: {elapsed_time:.1f}秒")
    print(f"成功: {len(results)}/{total_pairs}")
    print(f"失败: {len(failed_pairs)}/{total_pairs}")
    print(f"\n等级分布:")
    for grade in ['S', 'A', 'B', 'C', 'D']:
        count = grade_stats[grade]
        pct = count / len(results) * 100 if results else 0
        print(f"  {grade}级: {count} ({pct:.1f}%)")

    print(f"\nTop 5 强关联配对:")
    for idx, r in enumerate(results[:5], 1):
        print(f"  {idx}. {r['name1']} vs {r['name2']}: {r['score']}分 ({r['grade']}级)")

    print(f"\n报告已保存:")
    print(f"  JSON: {json_file}")
    print(f"  Markdown: {md_file}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='批量分析板块股票关联度')
    parser.add_argument('sector', nargs='?', default='光模块',
                       help='板块名称（默认：光模块）')
    parser.add_argument('--days', type=int, default=90,
                       help='分析天数（默认：90）')
    parser.add_argument('--output', default='outputs',
                       help='输出目录（默认：outputs）')

    args = parser.parse_args()

    batch_analyze_sector(args.sector, args.days, args.output)
