# 四方阁易爪 v1.0.0 — APK 构建指南

## 项目结构
```
四方阁易爪888/
├── main.py              # FastAPI 主服务器（18引擎 + 六层降级）
├── app.py               # Kivy WebView 启动器
├── buildozer.spec       # Buildozer 构建配置
├── requirements.txt     # Python 依赖
├── BUILD.md             # 本文件
├── frontend/
│   ├── index.html       # 前端 SPA（含六层降级链）
│   ├── chat_ui.css      # 浅色国风主题
│   └── chat_ui.js       # 前端交互逻辑
├── python_engines/      # 18 个命理排盘引擎
│   ├── bazi.py          # 八字命理
│   ├── ziwei.py         # 紫微斗数
│   ├── liuren.py        # 大六壬
│   ├── qimen.py         # 奇门遁甲
│   ├── liuyao.py        # 六爻纳甲
│   ├── qizheng.py       # 七政四余
│   ├── bazhai.py        # 八宅+紫白飞星
│   ├── huangli.py       # 黄历万年历
│   ├── fengshui.py      # 玄空飞星风水
│   ├── xingming.py      # 姓名学
│   ├── haoma.py         # 号码吉凶
│   ├── reading.py       # 命盘解读
│   ├── hehun.py         # 八字合婚
│   ├── yunshi.py        # 每日运势
│   ├── reading_offline.py # 离线解读引擎
│   ├── stock.py         # 股票行情
│   ├── security_tools.py  # 安全工具
│   └── location_time.py   # 位置/时间工具
└── ziwei_data/
    └── ziwei-offline/   # 紫微斗数离线数据（43文件）
```

## AI 六层降级链路
| 层 | 通道 | 条件 |
|---|------|------|
| ① | 直连 Gateway SSE | 电脑开机+有网 |
| ② | /api/gateway-proxy SSE | 电脑开机+有网（手机/APK） |
| ③ | EasyClaw 远程 Agent | APK有网+电脑开机 |
| ④ | 硅基流动 FC | APK有网即可 |
| ⑤ | 离线规则引擎 | 纯本地，无网 |
| ⑥ | 最简JS模板 | 兜底 |

## 构建步骤（需要 Linux + buildozer）

### 环境准备
```bash
# 安装 buildozer
pip install buildozer

# 安装 Android SDK/NDK
buildozer init  # 首次运行会自动下载
```

### 构建 APK
```bash
cd 四方阁易爪888/
buildozer android debug
```

### 输出
```
bin/sifanggeyizhua-1.0.0-debug.apk
```

## 运行模式

### 纯离线模式
APK 自带 18 引擎 + 离线解读，无网络也能排盘+解读

### 联网模式
设置环境变量启用远程 AI：
```bash
export GATEWAY_URL=http://192.168.2.107:10089
export GATEWAY_TOKEN=b469ba6c1657aa35c1ad1b4f1600a41e7a80b452519f0d1c
export SILICONFLOW_API_KEY=sk-xxx
# 然后启动 main.py
python main.py --lan
```
