@echo off
chcp 65001 >nul
title AppLauncher 启动器

echo ========================================
echo        AppLauncher 智能程序启动器
echo ========================================
echo.

REM 获取当前脚本所在目录
set "currentDir=%~dp0"
cd /d "%currentDir%"

REM 检查launcher.py是否存在
if not exist "launcher.py" (
    echo 错误：找不到 launcher.py 文件！
    echo 请确保该脚本与 launcher.py 在同一目录下。
    pause
    exit /b 1
)

REM 检查Python是否可用
where python >nul 2>nul
if %errorlevel% neq 0 (
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo 错误：找不到Python环境！
        echo 请确保已安装Python并添加到系统PATH中。
        pause
        exit /b 1
    ) else (
        set "pythonCmd=python3"
    )
) else (
    set "pythonCmd=python"
)

echo 正在启动 AppLauncher...
echo.

%pythonCmd% launcher.py
if %errorlevel% neq 0 (
    echo.
    echo 程序启动失败！
    echo 请检查Python环境和依赖包是否正确安装。
    pause
)

echo.
echo 程序已退出。
pause
