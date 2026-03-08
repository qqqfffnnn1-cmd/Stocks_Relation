"""
板块数据获取 - 东方财富 API
获取同花顺概念/行业板块列表及成分股
"""
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta

CACHE_FILE = Path(__file__).parent.parent / "cache" / "sectors_cache.json"
CACHE_DAYS = 1  # 板块列表每天更新


def _get_session():
    s = requests.Session()
    s.trust_env = False
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    return s


def _load_cache():
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
            cached_date = datetime.strptime(data["date"], "%Y-%m-%d")
            if datetime.now() - cached_date < timedelta(days=CACHE_DAYS):
                return data
        except Exception:
            pass
    return None


def _save_cache(data):
    CACHE_FILE.parent.mkdir(exist_ok=True)
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def get_sector_list():
    """
    获取东方财富概念板块列表
    返回: [{"code": "BK0493", "name": "光模块"}, ...]
    """
    cached = _load_cache()
    if cached:
        return cached.get("sectors", [])

    session = _get_session()
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 200,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": "m:90 t:3",  # 概念板块
        "fields": "f2,f3,f4,f12,f14",
    }
    try:
        resp = session.get(url, params=params, timeout=10)
        items = resp.json()["data"]["diff"]
        sectors = [{"code": x["f12"], "name": x["f14"]} for x in items]
        sectors.sort(key=lambda x: x["name"])
        _save_cache({"date": datetime.now().strftime("%Y-%m-%d"), "sectors": sectors})
        return sectors
    except Exception as e:
        print(f"获取板块列表失败: {e}")
        return []


def get_sector_stocks(sector_code: str):
    """
    获取板块成分股代码列表
    返回: ["300394", "300308", ...]
    """
    session = _get_session()
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        "pn": 1,
        "pz": 200,
        "po": 1,
        "np": 1,
        "ut": "bd1d9ddb04089700cf9c27f6f7426281",
        "fltt": 2,
        "invt": 2,
        "fid": "f3",
        "fs": f"b:{sector_code} f:!50",
        "fields": "f12,f14",
    }
    try:
        resp = session.get(url, params=params, timeout=10)
        items = resp.json()["data"]["diff"]
        return [x["f12"] for x in items]
    except Exception as e:
        print(f"获取板块成分股失败: {e}")
        return []
