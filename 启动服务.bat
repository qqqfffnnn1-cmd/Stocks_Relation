@echo off
echo.
echo ============================================================
echo 股票关联度分析工具 - 启动中...
echo ============================================================
echo.

cd /d "%~dp0"

echo [1] 启动服务...
start "StockRelation-Server" /MIN python web\app.py

echo [2] 等待服务启动...
timeout /t 5 /nobreak >nul

echo [3] 打开浏览器...
start http://localhost:5000

echo.
echo ============================================================
echo 服务已启动！
echo ============================================================
echo.
echo 访问地址: http://localhost:5000
echo.
echo 关闭此窗口不会停止服务
echo 要停止服务，请关闭标题为 "StockRelation-Server" 的窗口
echo.
pause
