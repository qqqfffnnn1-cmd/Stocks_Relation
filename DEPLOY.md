# 部署到 Render 指南

## 步骤1：创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称：`TK_StockRelation`
3. 描述：`股票关联度分析工具 - Stock Relation Analysis Tool`
4. 选择 **Public** 或 **Private**
5. **不要**勾选 "Initialize this repository with a README"
6. 点击 "Create repository"

## 步骤2：推送代码到 GitHub

在 `TK_StockRelation` 目录下运行：

```bash
git remote add origin https://github.com/YOUR_USERNAME/TK_StockRelation.git
git branch -M main
git push -u origin main
```

替换 `YOUR_USERNAME` 为你的 GitHub 用户名。

## 步骤3：在 Render 部署

1. 访问 https://dashboard.render.com/
2. 点击 "New +" → "Web Service"
3. 连接你的 GitHub 仓库：`TK_StockRelation`
4. 配置如下：
   - **Name**: `stock-relation` （或其他名称）
   - **Region**: `Singapore` （或其他区域）
   - **Branch**: `main`
   - **Root Directory**: 留空
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `cd web && gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: `Free`

5. 点击 "Create Web Service"

## 步骤4：等待部署完成

- Render 会自动构建和部署
- 大约需要 3-5 分钟
- 部署完成后会显示 URL，类似：`https://stock-relation.onrender.com`

## 注意事项

### 1. 依赖 TK_EastMoney 数据

由于项目依赖 `TK_EastMoney/stock_names_cache.json`，需要：

**方案A（推荐）**：将股票名称缓存打包到项目中
```bash
# 复制缓存文件到项目
cp ../TK_EastMoney/stock_names_cache.json data_sources/

# 修改 stock_mapper.py 中的路径
# 将 TK_EastMoney 路径改为 data_sources
```

**方案B**：使用在线API获取股票列表（已实现fallback）

### 2. 免费版限制

Render 免费版限制：
- 15分钟无活动会休眠
- 首次访问需要等待唤醒（约30秒）
- 每月750小时免费运行时间

### 3. 环境变量（可选）

如果需要配置环境变量，在 Render 控制台：
- Settings → Environment
- 添加需要的环境变量

## 本地测试生产环境

在部署前，可以本地测试生产配置：

```bash
# 安装 gunicorn
pip install gunicorn

# 运行生产服务器
cd web
gunicorn app:app --bind 0.0.0.0:5000
```

访问 http://localhost:5000 测试。

## 更新部署

每次代码更新后：

```bash
git add .
git commit -m "Update: 描述更新内容"
git push
```

Render 会自动检测到更新并重新部署。

## 故障排查

### 部署失败

1. 查看 Render 的 "Logs" 标签页
2. 检查 `requirements.txt` 是否正确
3. 确认 `Procfile` 和 `runtime.txt` 存在

### 运行时错误

1. 查看 "Logs" 中的错误信息
2. 常见问题：
   - 缺少依赖文件（如 stock_names_cache.json）
   - 路径问题（使用相对路径）
   - 端口配置（必须使用 `$PORT` 环境变量）

### 性能问题

免费版资源有限，如果需要更好性能：
- 升级到付费计划（$7/月起）
- 或使用其他平台（Heroku, Railway, Fly.io）

## 访问地址

部署成功后，你的应用将在：
- `https://YOUR-APP-NAME.onrender.com`

可以分享这个地址给其他人使用。

## 自定义域名（可选）

如果有自己的域名：
1. 在 Render 控制台 → Settings → Custom Domains
2. 添加你的域名
3. 按照提示配置 DNS 记录
