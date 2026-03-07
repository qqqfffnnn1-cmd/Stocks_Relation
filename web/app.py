"""
股票关联度分析 Web 应用
Flask 后端 API
"""
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import traceback

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
from data_sources.stock_mapper import get_mapper

from api.query_engine import StockRelationQuery

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 创建查询引擎实例
# 创建股票映射器实例
stock_mapper = get_mapper()
query_engine = StockRelationQuery()


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    分析两只股票的关联度

    请求参数:
        stock1: 股票代码1
        stock2: 股票代码2
        days: 分析天数（默认90）

    返回:
        JSON 格式的分析结果
    """
    try:
        data = request.get_json()

        stock1 = data.get('stock1', '').strip()
        stock2 = data.get('stock2', '').strip()
        days = int(data.get('days', 90))

        # 参数验证
        if not stock1 or not stock2:
            return jsonify({
                'success': False,
                'error': '请输入股票代码'
            }), 400

        if days < 10 or days > 365:
            return jsonify({
                'success': False,
                'error': '分析天数必须在 10-365 之间'
            }), 400

        # 执行分析
        result = query_engine.analyze_stock_relation(stock1, stock2, days)

        # 检查是否有错误
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 400

        # 返回成功结果
        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        print(f"分析失败: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'服务器错误: {str(e)}'
        }), 500


@app.route('/api/search_stock', methods=['GET'])
def search_stock():
    """
    搜索股票（可选功能，用于自动补全）

    参数:
        q: 搜索关键词

    返回:
        匹配的股票列表
    """
    try:
        keyword = request.args.get('q', '').strip()

        if not keyword:
            return jsonify({
                'success': True,
                'data': []
            })

        # 使用 stock_mapper 搜索股票
        results = stock_mapper.search(keyword, limit=10)
        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'service': 'TK_StockRelation API',
        'stock_count': len(stock_mapper.stock_map)
    })


@app.route('/api/test_search', methods=['GET'])
def test_search():
    """测试搜索功能"""
    keyword = request.args.get('q', '天孚')
    results = stock_mapper.search(keyword, limit=5)
    return jsonify({
        'keyword': keyword,
        'stock_count': len(stock_mapper.stock_map),
        'results': results
    })


if __name__ == '__main__':
    print("\n" + "="*60)
    print("股票关联度分析 Web 服务")
    print("="*60)
    print("\n访问地址: http://localhost:5000")
    print("按 Ctrl+C 停止服务\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
