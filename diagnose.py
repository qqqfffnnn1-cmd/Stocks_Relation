"""
网络诊断脚本
"""
import os
import requests

print("="*60)
print("网络环境诊断")
print("="*60 + "\n")

# 1. 检查代理设置
print("[1] 代理设置:")
proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY']
for var in proxy_vars:
    value = os.environ.get(var, '未设置')
    print(f"  {var}: {value}")

# 2. 测试直连
print("\n[2] 测试直连东方财富:")
try:
    # 清除代理
    for key in proxy_vars:
        if key in os.environ:
            del os.environ[key]

    response = requests.get(
        'http://push2his.eastmoney.com',
        timeout=5,
        proxies={'http': None, 'https': None}
    )
    print(f"  状态码: {response.status_code}")
    print("  ✓ 连接成功")
except Exception as e:
    print(f"  ✗ 连接失败: {e}")

# 3. 测试 AKShare
print("\n[3] 测试 AKShare:")
try:
    import akshare as ak

    # 清除代理
    for key in proxy_vars:
        if key in os.environ:
            del os.environ[key]

    # 尝试获取简单数据
    df = ak.stock_zh_a_hist(symbol="000001", period="daily", adjust="")
    print(f"  获取数据: {len(df)} 条")
    print("  ✓ AKShare 正常")
except Exception as e:
    print(f"  ✗ AKShare 失败: {e}")

print("\n" + "="*60)
