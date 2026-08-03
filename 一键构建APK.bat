@echo off
echo ===== 四方阁易爪 — WSL2 一键安装 + APK 构建脚本 =====
echo.

:: ===== 第一步：启用 WSL =====
echo [1/4] 启用 WSL 功能（需要管理员权限，系统会弹出 UAC 确认框）...
echo 以管理员身份运行 PowerShell，粘贴以下两条命令：
echo.
echo   dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
echo   dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
echo.
echo 执行完后，重启电脑。
echo.
echo 重启后，双击此脚本继续...
pause

:: ===== 第二步：安装 WSL + Ubuntu =====
echo [2/4] 安装 WSL + Ubuntu...
wsl --install -d Ubuntu-22.04
echo 等待安装完成，会弹出 Ubuntu 终端让你设置用户名密码。
echo 设置完后关闭 Ubuntu 窗口，按任意键继续...
pause

:: ===== 第三步：在 WSL 中安装 buildozer =====
echo [3/4] 在 WSL 中安装 buildozer...
wsl bash -c "sudo apt update && sudo apt install -y python3-pip git openjdk-17-jdk zlib1g-dev libncurses5-dev libtinfo5 && pip3 install buildozer cython"
echo 等待安装完成...
pause

:: ===== 第四步：构建 APK =====
echo [4/4] 开始构建 四方阁易爪 APK...
echo.
echo 源码目录: %~dp0
wsl bash -c "cd /mnt/c/Users/Administrator/.easyclaw/workspace/四方阁易爪888 && buildozer init 2>/dev/null; buildozer android debug"

echo.
echo ===== 完成！ =====
echo APK 位于: 四方阁易爪888\bin\sifanggeyizhua-1.0.0-debug.apk
pause
