@echo off
echo ========================================
echo Facebook好友可见性检查工具 - 打包脚本
echo ========================================
echo.

echo [1/3] 检查依赖...
pip install -r requirements.txt
if errorlevel 1 (
    echo 依赖安装失败！
    pause
    exit /b 1
)

echo.
echo [2/3] 开始打包...
pyinstaller build.spec
if errorlevel 1 (
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo [3/3] 打包完成！
echo.
echo 可执行文件位置: dist\Facebook好友可见性检查工具.exe
echo.
echo ========================================
pause