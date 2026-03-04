"""
股票关联度分析 Skill
用法: /stock-relation <股票1> <股票2> [--days N]
"""
import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from api.query_engine import StockRelationQuery


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='股票关联度分析工具')

    parser.add_argument('stock1', type=str, help='股票代码1 (如: 300394 或 天孚通信)')
    parser.add_argument('stock2', type=str, help='股票代码2 (如: 300308 或 中际旭创)')
    parser.add_argument('--days', type=int, default=90, help='分析天数 (默认: 90)')
    parser.add_argument('--output', type=str, help='输出文件路径 (可选)')

    return parser.parse_args()


def resolve_stock_code(stock_input: str) -> str:
    """
    解析股票输入（支持代码或名称）

    Args:
        stock_input: 股票代码或名称

    Returns:
        str: 股票代码
    """
    # 如果是纯数字，直接返回
    if stock_input.isdigit():
        return stock_input

    # 否则尝试通过名称查询（这里简化处理，实际可接入 KYC 的 company_aliases）
    # 暂时返回原值，让 API 自己处理
    return stock_input


def main():
    """主函数"""
    args = parse_args()

    # 解析股票代码
    stock1 = resolve_stock_code(args.stock1)
    stock2 = resolve_stock_code(args.stock2)

    print(f"\n🔍 股票关联度分析工具")
    print(f"📊 分析对象: {stock1} vs {stock2}")
    print(f"📅 分析周期: 最近 {args.days} 天\n")

    # 创建查询引擎
    query = StockRelationQuery()

    # 执行分析
    try:
        result = query.analyze_stock_relation(stock1, stock2, days=args.days)

        # 生成报告
        report = query.generate_report(result)

        # 打印报告
        print("\n" + "="*60)
        print(report)
        print("="*60 + "\n")

        # 保存报告
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = project_root / "outputs"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"relation_{stock1}_{stock2}_{args.days}d.md"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"✅ 报告已保存至: {output_path}\n")

    except Exception as e:
        print(f"\n❌ 分析失败: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
