"""
快速测试脚本 - 验证股票关联度分析功能
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))

from api.query_engine import StockRelationQuery

def test_analysis():
    """测试分析功能"""
    print("\n" + "="*60)
    print("测试股票关联度分析")
    print("="*60 + "\n")

    query = StockRelationQuery()

    # 测试分析
    print("分析: 300394 vs 300308 (最近30天)\n")

    try:
        result = query.analyze_stock_relation("300394", "300308", days=30)

        if 'error' in result:
            print(f"[错误] {result['error']}")
            return False

        # 显示结果
        print("\n[成功] 分析完成！\n")
        print(f"综合评分: {result['overall_score']['score']}/100")
        print(f"评级: {result['overall_score']['grade']}")
        print(f"价格相关系数: {result['price_correlation']['correlation']:.4f}")
        print(f"同涨同跌率: {result['price_correlation']['sync_rate']*100:.1f}%")

        return True

    except Exception as e:
        print(f"[异常] {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_analysis()
    sys.exit(0 if success else 1)
