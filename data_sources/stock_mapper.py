"""
股票名称和代码映射
从腾讯API获取并缓存
"""
import json
import requests
from pathlib import Path
from datetime import datetime, timedelta


class StockNameMapper:
    """股票名称映射器"""

    def __init__(self):
        self.cache_file = Path(__file__).parent.parent / "cache" / "stock_names.json"
        self.cache_file.parent.mkdir(exist_ok=True)
        self.stock_map = {}
        self._load_cache()

    def _load_cache(self):
        """加载缓存"""
        # 优先使用项目内的股票名称缓存（用于部署）
        local_eastmoney_cache = Path(__file__).parent / "stock_names_cache.json"

        if local_eastmoney_cache.exists():
            try:
                with open(local_eastmoney_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期（30天）
                    cache_date = datetime.fromisoformat(data.get('date', '2000-01-01'))
                    if datetime.now() - cache_date < timedelta(days=30):
                        self.stock_map = data.get('a', {})
                        print(f"已加载本地缓存：{len(self.stock_map)} 只股票")
                        return
            except Exception as e:
                print(f"加载本地缓存失败: {e}")

        # 其次尝试 TK_EastMoney 的完整缓存（本地开发环境）
        ccvscode_root = Path(__file__).parent.parent.parent
        eastmoney_cache = ccvscode_root / "TK_EastMoney" / "stock_names_cache.json"

        if eastmoney_cache.exists():
            try:
                with open(eastmoney_cache, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期（30天）
                    cache_date = datetime.fromisoformat(data.get('date', '2000-01-01'))
                    if datetime.now() - cache_date < timedelta(days=30):
                        self.stock_map = data.get('a', {})
                        print(f"已加载 TK_EastMoney 缓存：{len(self.stock_map)} 只股票")
                        return
            except Exception as e:
                print(f"加载 TK_EastMoney 缓存失败: {e}")

        # 再次使用 cache 目录缓存
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 检查缓存是否过期（7天）
                    cache_date = datetime.fromisoformat(data.get('date', '2000-01-01'))
                    if datetime.now() - cache_date < timedelta(days=7):
                        self.stock_map = data.get('stocks', {})
                        print(f"已加载本地缓存：{len(self.stock_map)} 只股票")
                        return
            except:
                pass

        # 缓存不存在或过期，重新获取
        self._fetch_stock_list()

    def _fetch_stock_list(self):
        """从东方财富获取股票列表"""
        try:
            # 使用东方财富的股票列表API
            session = requests.Session()
            session.trust_env = False

            url = "http://80.push2.eastmoney.com/api/qt/clist/get"
            params = {
                'pn': '1',
                'pz': '5000',
                'po': '1',
                'np': '1',
                'fltt': '2',
                'invt': '2',
                'fid': 'f3',
                'fs': 'm:0 t:6,m:0 t:80,m:1 t:2,m:1 t:23',  # A股
                'fields': 'f12,f14'  # 代码和名称
            }

            response = session.get(url, params=params, timeout=10)
            data = response.json()

            if data.get('data') and data['data'].get('diff'):
                stocks = {}
                for item in data['data']['diff']:
                    code = item.get('f12', '')
                    name = item.get('f14', '')
                    if code and name:
                        stocks[code] = name

                self.stock_map = stocks

                # 保存缓存
                with open(self.cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'date': datetime.now().isoformat(),
                        'stocks': stocks
                    }, f, ensure_ascii=False, indent=2)

                print(f"已缓存 {len(stocks)} 只股票")

        except Exception as e:
            print(f"获取股票列表失败: {e}")
            # 使用内置的常用股票列表作为后备
            self._use_fallback_list()

    def _use_fallback_list(self):
        """使用内置的常用股票列表"""
        self.stock_map = {
            # 光模块
            '300394': '天孚通信',
            '300308': '中际旭创',
            '300502': '新易盛',
            '002281': '光迅科技',
            '300620': '光库科技',
            '688498': '源杰科技',
            '688396': '华润微',
            # AI芯片
            '688256': '寒武纪',
            '688041': '海光信息',
            '688981': '中芯国际',
            # 更多可以继续添加...
        }

    def search(self, keyword: str, limit: int = 10):
        """
        搜索股票

        Args:
            keyword: 关键词（代码或名称）
            limit: 返回数量限制

        Returns:
            list: [{'code': '300394', 'name': '天孚通信'}, ...]
        """
        if not keyword:
            return []

        keyword = keyword.strip()
        keyword_upper = keyword.upper()  # 用于匹配代码
        results = []

        for code, name in self.stock_map.items():
            # 匹配代码（不区分大小写）或名称（精确匹配）
            if keyword_upper in code.upper() or keyword in name:
                results.append({
                    'code': code,
                    'name': name,
                    'display': f'{name}({code})'
                })

                if len(results) >= limit:
                    break

        return results

    def get_name(self, code: str) -> str:
        """获取股票名称"""
        return self.stock_map.get(code, f'股票{code}')

    def get_code(self, name: str) -> str:
        """通过名称获取代码"""
        for code, stock_name in self.stock_map.items():
            if name == stock_name:
                return code
        return name  # 如果找不到，返回原值


# 全局实例
_mapper = None


def get_mapper():
    """获取全局映射器实例"""
    global _mapper
    if _mapper is None:
        _mapper = StockNameMapper()
    return _mapper


if __name__ == "__main__":
    # 测试
    mapper = StockNameMapper()

    print("\n=== 测试搜索功能 ===")

    # 测试1: 搜索代码
    print("\n[1] 搜索 '300':")
    results = mapper.search('300', limit=5)
    for r in results:
        print(f"  {r['display']}")

    # 测试2: 搜索名称
    print("\n[2] 搜索 '通信':")
    results = mapper.search('通信', limit=5)
    for r in results:
        print(f"  {r['display']}")

    # 测试3: 获取名称
    print("\n[3] 获取名称:")
    print(f"  300394 -> {mapper.get_name('300394')}")
    print(f"  300308 -> {mapper.get_name('300308')}")

    print(f"\n总共缓存了 {len(mapper.stock_map)} 只股票")
