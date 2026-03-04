@echo off
chcp 65001 >nul
cls
echo.
echo ============================================================
echo 股票关联度分析工具 - 一键启动
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] 检查依赖...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [!] 缺少 Flask，正在安装...
    pip install flask flask-cors -q
)

echo [2/3] 启动服务...
start /B python app.py

echo [3/3] 等待服务启动...
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo 服务已启动！
echo ============================================================
echo.
echo 访问地址: http://localhost:5000
echo.
echo 正在打开浏览器...
start http://localhost:5000
echo.
echo 按任意键停止服务...
pause >nul

echo.
echo 正在停止服务...
taskkill /F /FI "WINDOWTITLE eq *python*app.py*" >nul 2>&1
echo 服务已停止
timeout /t 2 /nobreak >nul
