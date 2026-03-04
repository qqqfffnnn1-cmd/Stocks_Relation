# 股票关联度分析 Web 应用

## 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Web 服务
cd web
python app.py

# 3. 打开浏览器访问
http://localhost:5000
```

## 功能特性

- ✅ 实时股票关联度分析
- ✅ 价格联动分析（相关系数、同涨同跌率、领先滞后）
- ✅ 资金共振分析（龙虎榜席位重叠）
- ✅ 综合评分和评级（A/B/C/D）
- ✅ 响应式设计，支持移动端

## 使用说明

1. 输入两只股票代码（如：300394、300308）
2. 选择分析天数（10-365天，默认90天）
3. 点击"开始分析"按钮
4. 查看详细的关联度分析报告

## 技术栈

- **后端**: Flask + Python
- **前端**: HTML5 + CSS3 + JavaScript
- **数据源**: AKShare API + TK_LHB 龙虎榜

## API 接口

### POST /api/analyze

分析两只股票的关联度

**请求参数:**
```json
{
  "stock1": "300394",
  "stock2": "300308",
  "days": 90
}
```

**返回结果:**
```json
{
  "success": true,
  "data": {
    "stock1": {...},
    "stock2": {...},
    "price_correlation": {...},
    "capital_resonance": {...},
    "overall_score": {...}
  }
}
```

### GET /api/health

健康检查接口

## 部署建议

### 本地开发
```bash
python web/app.py
```

### 生产环境（使用 Gunicorn）
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web.app:app
```

### Docker 部署
```bash
# 构建镜像
docker build -t stock-relation .

# 运行容器
docker run -p 5000:5000 stock-relation
```

## 注意事项

1. 首次使用需要安装依赖：`pip install -r requirements.txt`
2. 数据来源于 AKShare 公开 API，请遵守使用频率限制
3. 龙虎榜数据依赖 TK_LHB，如未运行则该部分评分为0
4. 建议在稳定的网络环境下使用

## 截图

（待添加）

## 更新日志

- 2026-03-04: 初始版本，实现基础 Web 界面和 API
