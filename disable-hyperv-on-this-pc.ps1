# 出厂进桌面后：关掉本机已有的 Hyper-V/WSL/沙盒。没有的项会跳过。
# 右键「使用 PowerShell 运行」不够，必须管理员。
# 家庭版没有 Microsoft-Hyper-V-All 是正常的。

$ErrorActionPreference = "Continue"

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "请右键 disable-hyperv-on-this-pc.bat - 以管理员身份运行。"
    exit 1
}

Write-Host "关闭 hypervisor 启动（不连网）..."
& bcdedit /set hypervisorlaunchtype off

$names = @(
    "Microsoft-Hyper-V-All",
    "Microsoft-Hyper-V",
    "VirtualMachinePlatform",
    "HypervisorPlatform",
    "Microsoft-Windows-Subsystem-Linux",
    "Containers-DisposableClientVM"
)

Write-Host "查看本机已启用的虚拟化功能..."
$enabled = @()
try {
    $enabled = @(Get-WindowsOptionalFeature -Online -ErrorAction Stop |
        Where-Object { $names -contains $_.FeatureName -and $_.State -eq "Enabled" })
} catch {
    Write-Host "列功能失败（常因没联网，错误 0x8024402c）。跳过 DISM，只保留 bcdedit。"
    Write-Host $_.Exception.Message
}

if ($enabled.Count -eq 0) {
    Write-Host "没有已启用的 Hyper-V/WSL/沙盒，或家庭版本来就没有这些项。这是正常的。"
} else {
    foreach ($f in $enabled) {
        Write-Host ("正在关闭 " + $f.FeatureName)
        try {
            Disable-WindowsOptionalFeature -Online -FeatureName $f.FeatureName -NoRestart -ErrorAction Stop | Out-Null
        } catch {
            Write-Host ("跳过 " + $f.FeatureName + "：" + $_.Exception.Message)
        }
    }
}

Write-Host ""
Write-Host "请再手动：Windows 安全中心 - 设备安全性 - 核心隔离 - 内存完整性 - 关掉。"
Write-Host "不要安装 Ubuntu/WSL、Docker。不要双击 System32 里的 cmstp。"
Write-Host "重启后生效。"
