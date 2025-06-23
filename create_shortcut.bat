@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

REM 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 设置快捷方式名称
set "SHORTCUT_NAME=AppLauncher.lnk"

REM 获取当前用户桌面路径
for /f "skip=2 tokens=2,*" %%A in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders" /v Desktop') do set "DESKTOP=%%B"

REM 检查桌面路径是否存在
if not exist "%DESKTOP%" (
    echo [错误] 未能获取桌面路径。
    pause
    exit /b 1
)

REM 设置目标vbs和图标路径
set "TARGET_VBS=%SCRIPT_DIR%start.vbs"
set "ICON_PATH=%SCRIPT_DIR%logo1.ico"

REM 检查目标文件是否存在
if not exist "%TARGET_VBS%" (
    echo [错误] 未找到 start.vbs 文件：%TARGET_VBS%
    pause
    exit /b 1
)
if not exist "%ICON_PATH%" (
    echo [错误] 未找到图标文件（仅支持ico格式）：%ICON_PATH%
    echo 请将 serverscan.png 转换为 logo1.ico 并放在本目录下。
    pause
    exit /b 1
)

REM 创建快捷方式的VBS脚本
set "VBS_FILE=%TEMP%\create_shortcut.vbs"
>"%VBS_FILE%" echo Set oWS = WScript.CreateObject("WScript.Shell")
>>"%VBS_FILE%" echo sLinkFile = "%DESKTOP%\%SHORTCUT_NAME%"
>>"%VBS_FILE%" echo Set oLink = oWS.CreateShortcut(sLinkFile)
>>"%VBS_FILE%" echo oLink.TargetPath = "%TARGET_VBS%"
>>"%VBS_FILE%" echo oLink.IconLocation = "%ICON_PATH%"
>>"%VBS_FILE%" echo oLink.WorkingDirectory = "%SCRIPT_DIR%"
>>"%VBS_FILE%" echo oLink.Save

REM 执行VBS脚本创建快捷方式
cscript //nologo "%VBS_FILE%"
if %errorlevel% neq 0 (
    echo [错误] 快捷方式创建失败。
    pause
    exit /b 1
)

REM 删除临时VBS脚本
if exist "%VBS_FILE%" del "%VBS_FILE%"

echo [成功] 快捷方式已创建在桌面：%DESKTOP%\%SHORTCUT_NAME%
pause
