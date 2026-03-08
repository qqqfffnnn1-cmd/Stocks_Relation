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
from data_sources.sector_api import get_sector_list, get_sector_stocks

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

        if days < 5 or days > 365:
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


@app.route('/api/sectors', methods=['GET'])
def sectors():
    """获取板块列表"""
    try:
        data = get_sector_list()
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analyze_sectors', methods=['POST'])
def analyze_sectors():
    """
    分析两个板块的关联度（取各板块涨跌幅均值作为板块指数）
    """
    try:
        data = request.get_json()
        sector1_code = data.get('sector1_code', '').strip()
        sector2_code = data.get('sector2_code', '').strip()
        sector1_name = data.get('sector1_name', sector1_code)
        sector2_name = data.get('sector2_name', sector2_code)
        days = int(data.get('days', 90))

        if not sector1_code or not sector2_code:
            return jsonify({'success': False, 'error': '请选择板块'}), 400
        if days < 5 or days > 365:
            return jsonify({'success': False, 'error': '分析天数必须在 5-365 之间'}), 400

        from datetime import datetime, timedelta
        import pandas as pd
        import numpy as np
        from scipy import stats
        import yfinance as yf

        start_dt = datetime.now() - timedelta(days=days + 30)  # 多取一些保证够数据
        start_str = start_dt.strftime("%Y-%m-%d")

        # 获取成分股
        stocks1 = get_sector_stocks(sector1_code)[:20]  # 最多取20只
        stocks2 = get_sector_stocks(sector2_code)[:20]

        if not stocks1 or not stocks2:
            return jsonify({'success': False, 'error': '无法获取板块成分股'}), 400

        def to_yf_ticker(code):
            """A股代码转Yahoo Finance格式"""
            if code.startswith('6'):
                return code + '.SS'
            else:
                return code + '.SZ'

        # 用yfinance批量下载，获取各板块每日平均涨跌幅
        def get_sector_pct(stock_list):
            tickers = [to_yf_ticker(c) for c in stock_list]
            try:
                raw = yf.download(tickers, start=start_str, progress=False, auto_adjust=True)
                if raw.empty:
                    return pd.Series(dtype=float)
                # 取收盘价
                if isinstance(raw.columns, pd.MultiIndex):
                    close = raw['Close']
                else:
                    close = raw[['Close']]
                pct = close.pct_change() * 100
                return pct.mean(axis=1).dropna()
            except Exception as e:
                print(f"yfinance下载失败: {e}")
                return pd.Series(dtype=float)

        pct1 = get_sector_pct(stocks1)
        pct2 = get_sector_pct(stocks2)

        merged = pd.concat([pct1.rename('s1'), pct2.rename('s2')], axis=1).dropna()

        if len(merged) < 5:
            return jsonify({'success': False, 'error': f'数据不足，仅有 {len(merged)} 个交易日重叠'}), 400

        corr, p_value = stats.pearsonr(merged['s1'], merged['s2'])
        sync = ((merged['s1'] > 0) == (merged['s2'] > 0)).mean()

        # 评分
        score = int(max(0, corr) * 40 + sync * 60)
        if score >= 90:
            grade, stars = "S (极强关联)", "★★★★★"
        elif score >= 70:
            grade, stars = "A (强关联)", "★★★★☆"
        elif score >= 50:
            grade, stars = "B (中等关联)", "★★★☆☆"
        elif score >= 30:
            grade, stars = "C (弱关联)", "★★☆☆☆"
        else:
            grade, stars = "D (无明显关联)", "★☆☆☆☆"

        return jsonify({
            'success': True,
            'data': {
                'sector1': {'code': sector1_code, 'name': sector1_name, 'stock_count': len(stocks1)},
                'sector2': {'code': sector2_code, 'name': sector2_name, 'stock_count': len(stocks2)},
                'correlation': round(float(corr), 4),
                'p_value': round(float(p_value), 4),
                'sync_rate': round(float(sync), 4),
                'data_points': len(merged),
                'score': score,
                'grade': grade,
                'stars': stars,
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/sector_divergence', methods=['GET'])
def sector_divergence():
    """
    读取最新的板块异类分析结果。
    优先读 TK_MLAnalysis/output/sector_divergence_*.csv（本地）；
    若不存在则读 web/static/sector_divergence_snapshot.json（线上静态快照）。
    """
    import glob
    import csv

    try:
        rows = []
        date_str = ''

        # 1. 尝试本地 CSV
        output_dir = Path(__file__).parent.parent.parent / 'TK_MLAnalysis' / 'output'
        files = sorted(glob.glob(str(output_dir / 'sector_divergence_*.csv')), reverse=True)
        if files:
            latest = files[0]
            date_str = Path(latest).stem.split('_')[-1]
            with open(latest, encoding='utf-8-sig') as f:
                for r in csv.DictReader(f):
                    rows.append({
                        'code': r['code'], 'name': r['name'], 'board': r['board'],
                        'amt': float(r['amt']), 'type': r['type'],
                        'd_sc': float(r['d_sc']), 'd_co': float(r['d_co']),
                        'd_di': float(r['d_di']), 'd_ex': float(r['d_ex']),
                        'd_cs': float(r['d_cs']), 'd_cb': float(r['d_cb']),
                        'w_sc': float(r['w_sc']), 'w_co': float(r['w_co']),
                        'w_di': float(r['w_di']), 'w_ex': float(r['w_ex']),
                        'w_cs': float(r['w_cs']), 'w_cb': float(r['w_cb']),
                        'total': float(r['total']),
                    })
        else:
            # 2. 线上静态快照
            snapshot = Path(__file__).parent / 'static' / 'sector_divergence_snapshot.json'
            if not snapshot.exists():
                return jsonify({'success': False, 'error': '暂无数据，请先运行 sector_divergence.py'}), 404
            import json as _json
            snap = _json.loads(snapshot.read_text(encoding='utf-8'))
            rows = snap['rows']
            date_str = snap['date']

        # 板块分化排行（板块内平均异类分）
        from collections import defaultdict
        board_map = defaultdict(list)
        for r in rows:
            board_map[r['board']].append(r)

        board_stats = []
        for board, stocks in board_map.items():
            n = len(stocks)
            avg_total = sum(s['total'] for s in stocks) / n
            avg_d = sum(s['d_sc'] for s in stocks) / n
            avg_w = sum(s['w_sc'] for s in stocks) / n
            strong = sum(1 for s in stocks if s['type'] == '独立走强')
            weak = sum(1 for s in stocks if s['type'] == '独立走弱')
            # 取综合分最高的前15只作为代表
            top_stocks = sorted(stocks, key=lambda x: x['total'], reverse=True)[:15]
            board_stats.append({
                'board': board, 'count': n,
                'avg_total': round(avg_total, 1),
                'avg_d': round(avg_d, 1),
                'avg_w': round(avg_w, 1),
                'strong': strong, 'weak': weak,
                'top_stocks': top_stocks,
            })
        board_stats.sort(key=lambda x: x['avg_total'], reverse=True)

        # 综合异类 TOP20
        top20 = sorted(rows, key=lambda x: x['total'], reverse=True)[:20]
        # 日度 TOP20
        top20_d = sorted(rows, key=lambda x: x['d_sc'], reverse=True)[:20]
        # 周度 TOP20
        top20_w = sorted(rows, key=lambda x: x['w_sc'], reverse=True)[:20]

        return jsonify({
            'success': True,
            'data': {
                'date': date_str,
                'total_stocks': len(rows),
                'board_stats': board_stats,
                'top20': top20,
                'top20_d': top20_d,
                'top20_w': top20_w,
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


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
