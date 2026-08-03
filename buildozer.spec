[app]

# 应用标识
title = 四方阁易爪
package.name = sifanggeyizhua
package.domain = com.sifangge

# 版本
version = 1.0.0
version.code = 1
source.dir = .

# 主入口
main = app.py

# 依赖
requirements = python3,httpx

# Android 权限
android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_WIFI_STATE,FOREGROUND_SERVICE

# 横竖屏自适应
orientation = all
android.landscape_mode = True
android.portrait_mode = True

# Android 最低 API
android.minapi = 24
android.api = 33

# Android 架构
android.arch = armeabi-v7a, arm64-v8a

# 文件包含
source.include_exts = py,png,jpg,jpeg,gif,bmp,ttf,otf,html,css,js,json,txt,md,yaml,yml,xml,csv
source.include_patterns = frontend/**,python_engines/**,ziwei_data/**,*.py,*.html,*.css,*.js,*.json

# 排除
source.exclude_dirs = __pycache__,.git,.github,node_modules,tests,test*,examples,docs,work,.github

# 清理构建
android.allow_backup = True
android.presplash_color = #F9F8FF
android.splash_color = #5B68AA

# 日志
android.logcat_filters = *:S python:D

# 打包
android.release_artifact = apk

# 跳过 Android 检查
p4a.branch = develop

# 超时
buildozer.build_timeout = 3600

[buildozer]
log_level = 2
warn_on_root = 1



