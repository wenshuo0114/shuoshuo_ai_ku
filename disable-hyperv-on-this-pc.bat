@echo off
chcp 65001 >nul
setlocal EnableExtensions

echo.
echo ==== 荣耀本机：出厂之后用这一份 ====
echo 前两步只能你在笔记本上点，这边点不到。
echo.
echo [1 安全芯片] 蓝底「安全芯片配置变更」选 确定（清除内容）。
echo     插电等出厂跑完。不要关安全启动。学校/企业包、可选配置包不要装。
echo.
echo [2 跳过 Wi-Fi] 选网络那一页按 Shift+F10（或 Fn+Shift+F10），输入其中一句回车：
echo     OOBE\BYPASSNRO
echo     若没用再试：
echo     start ms-cxh:localonly
echo     用本地账户进桌面。不要在设置阶段改服务、防火墙。
echo.
echo [3 下面关掉 Hyper-V / WSL / 沙盒] 必须「以管理员身份运行」本文件。
echo.

net session >nul 2>&1
if errorlevel 1 (
  echo 现在不是管理员。请右键本文件 - 以管理员身份运行。
  pause
  exit /b 1
)

echo 正在关闭虚拟化相关功能（没有的项会失败，可忽略）...
dism.exe /Online /Disable-Feature /FeatureName:Microsoft-Hyper-V-All /NoRestart
dism.exe /Online /Disable-Feature /FeatureName:VirtualMachinePlatform /NoRestart
dism.exe /Online /Disable-Feature /FeatureName:HypervisorPlatform /NoRestart
dism.exe /Online /Disable-Feature /FeatureName:Microsoft-Windows-Subsystem-Linux /NoRestart
dism.exe /Online /Disable-Feature /FeatureName:Containers-DisposableClientVM /NoRestart

bcdedit /set hypervisorlaunchtype off

echo.
echo 请手动：设置 - Windows 安全中心 - 设备安全性 - 核心隔离 - 内存完整性 - 关掉（若要 hypervisor 停住）。
echo 不要安装 Ubuntu/WSL、Docker Desktop，不要把用户目录做成共享盘。
echo.
echo 需要重启后才完全生效。按任意键结束（不会自动重启）。
pause
endlocal
