@echo off
chcp 65001 >nul
echo.
echo ==== 荣耀本机：出厂之后 ====
echo [1] 安全芯片选 确定（清除）。不要关安全启动。学校/企业包不要装。
echo [2] Wi-Fi 页 Shift+F10，输入 OOBE\BYPASSNRO 或 start ms-cxh:localonly
echo [3] 下面需要管理员：关掉虚拟化。家庭版没有 Hyper-V 全家桶是正常的。
echo     DISM 报 0x8024402c = 没连上 Windows 更新，不是中招。
echo.
net session >nul 2>&1
if errorlevel 1 (
  echo 请右键本文件 - 以管理员身份运行。
  pause
  exit /b 1
)
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0disable-hyperv-on-this-pc.ps1"
echo.
pause
