---
name: ziwei-ai-html-report
description: Use when a user needs a saveable Zi Wei Dou Shu HTML report from birth data or chart context in an agent workflow that must stay self-contained, avoid invented placements, and validate K-line JSON before delivery.
---

# 紫微 AI 离线 HTML 报告（整合 Skill）

## Overview

本 skill 将本仓库内已验证的**排盘规则、提示词与命盘上下文格式**交给任意 agent：可从阳历出生资料生成命盘上下文，再输出**单个 HTML 文件**，含「综合批注 / 流年运势 / 人生 K 线」三节。

### 排盘策略（建议优先：无 Node + 真太阳时）

| 路径 | 命令要点 | 依赖 | 真太阳时 |
|------|-----------|------|----------|
| **A. 纯 Python（默认推荐）** | `python3 tools/ziwei_offline.py --solar ... --time ... --gender ... [--birthplace ...]` | **仅 Python 3**，无 Node / npm | **默认开启**：有经纬度/可解析 `birthplace` 时按经度+时间方程换算后再定农历与时辰；`--disable-true-solar-time` 可关 |
| **B. iztro 对齐 App 星曜** | 先 Python 输出「真太阳时后的阳历时分」，再喂 iztro，再拼上下文（见下） | 本目录 `npm install` + **Node.js** | **可一致**：用 `--emit-iztro-birth-json` 把真太阳时口径注入 iztro |
| **C. iztro 仅钟表（与 App 输入框一致）** | `IZTRO_MODE=raw-clock` 或直连 `chart_iztro.cjs --solar --time` | Node + npm | **否**（与用户在 App 里只填钟表时间相同） |

**结论**：希望**脱离 Node** → 只用 **路径 A**（已含真太阳时）。希望**主星与 App/iztro 一致且仍要真太阳时** → 用 **路径 B**（离不开 Node，因 iztro 为 JS 库），无法用「零依赖静态文件」替代。

**路径 B 一键**（环境变量；需已 `npm install`）：

```bash
cd skills/ziwei-ai-html-report
SOLAR=1995-07-19 TIME=11:40 GENDER=male BIRTHPLACE="广东省深圳市" TARGET_YEAR=2026 ./tools/report_payload_iztro.sh
```

**路径 B 分步**（真太阳 → iztro → 上下文）：

```bash
python3 tools/ziwei_offline.py --solar 1995-07-19 --time 11:40 --gender male \
  --birthplace "广东省深圳市" --target-year 2026 --emit-iztro-birth-json \
  | node tools/chart_iztro.cjs --birth-json - \
  | python3 tools/ziwei_offline.py --from-chart-json --target-year 2026 --format json
```

`--emit-iztro-birth-json` 输出一行 JSON（`solarDate`、`time`、`gender`、`trueSolarApplied`），`chart_iztro.cjs --birth-json -` 从 stdin 读取；Python 再补齐 `patterns`、校验与三份 Context。

**路径 C**（无真太阳、纯钟表 iztro）：`IZTRO_MODE=raw-clock ./tools/report_payload_iztro.sh -- ...` 或旧式 `node chart_iztro.cjs --solar ... | python3 ... --from-chart-json`。

纯 Python：[`tools/ziwei_offline.py`](tools/ziwei_offline.py)（标准库）。阳历范围 **1900-01-31 至 2100-12-31**。路径 A 为安星自研实现，**与 iztro 在个别命盘上可能仍有差异**；以 iztro 为准请用路径 B/C。

**核心约束：违反字面即违反本意**——不可因「节省时间」「用户急了」跳过输入校验或免责声明。

完整提示词与模板见同目录：[prompts.md](prompts.md)。HTML 样板见：[report-template.html](report-template.html)。

## 运行前提（简化）

本 skill 运行在 agent 环境中，默认已有模型参与解读生成。  
因此本文档聚焦于：离线排盘事实、提示词结构、HTML 交付一致性，不重复展开模型可用性说明。

## When to Use

- 需要在任意聊天模型 / agent 环境中输出**离线可打开**的命理报告；
- 用户只提供阳历生日、出生小时、性别、分析年份，且无法或不愿安装额外运行时依赖；
- 用户已粘贴**本命 AI 上下文**（及流年块，若做流年节），希望直接组装报告；
- 交付物必须是**单文件 HTML**（便于保存、邮件、网盘分享）。

## When NOT to Use

- 用户生日超出 1900-2100 且无法提供农历/命盘上下文——当前离线历法表无法覆盖；
- 仅需合盘：当前发布版不内置合盘节；若需要，请在本目录内新增独立提示词节；
- 只想在现成产品 UI 内查看，而非交付离线 HTML。

## 输入契约（必填 / 可选用）

### A. 出生资料（首选，可独立排盘）

最小输入：

| 字段 | 说明 |
|------|------|
| 阳历日期 | `YYYY-MM-DD`，范围 1900-01-31 至 2100-12-31 |
| 出生时间 | `HH:mm`（推荐）或 `hour(0-23)`；`23:00-23:59` 按晚子时换日 |
| 性别 | `male/female` 或 男/女 |
| 出生地 | 可选；用于真太阳时换算，默认 `hybrid` 模式下优先在线地理编码，失败回退内置城市表 |
| 流年分析年 | 可选，默认当前年 |

**年龄口径**：大限与流年叠宫使用**虚岁**（`分析年 − 农历生年 + 1`）。报告页眉与流年上下文会同时标注**周岁**（截至分析年 12 月 31 日，以及截至生成日若与年末不同）。

运行工具生成上下文：

```bash
python3 tools/ziwei_offline.py \
  --solar 1996-01-06 \
  --time 11:30 \
  --gender female \
  --birthplace "广东省佛山市顺德区" \
  --target-year 2026 \
  --format json
```

输出 JSON 含：

| 字段 | 用途 |
|------|------|
| `chart` | 离线命盘结构化数据 |
| `natalContext` | 综合批注用户上下文 |
| `yearlyContext` | 流年运势用户上下文 |
| `klineData` | 确定性人生 K 线数据，直接嵌入 HTML |
| `klineContext` | K 线文字解读上下文；不得作为数值走势来源 |

标准示例（展示层）：
- 阳历生日：1996年1月6日
- 农历生日：可不填（系统自动计算）
- 出生时间：11:30
- 性别：女
- 出生地：广东省佛山市顺德区

对应机器字段：
- `solar=1996-01-06`
- `time=11:30`（或 `hour=11`）
- `gender=female`
- `birthplace=广东省佛山市顺德区`
- `targetYear=2026`（可选）

### B. 本命上下文（备选）

在本 skill 的中州派规则下，以下内容之一视为**有效本命输入**：

1. **首选**：与本工具 `build_prompt_context` 输出等价的 Markdown 文本（以 `【命盘完整信息】` 开头，含 `## 十二宫星曜分布`、`## 十二大限`、按需含 `## 近年流年信息` 等）。
2. **备选**：结构化 JSON（可还原为同上 Markdown）。最小字段映射：

| 字段 | 含义 |
|------|------|
| `命宫主星` | `{ name, group?, description? }[]`，至少 `name` |
| `身宫主星` | 同上 |
| `身宫位置` | 宫位名字符串 |
| `十二宫` | `{ name, stem, majorStars[], minorStars[], adjectiveStars?, isBodyPalace?, decadalRange? }[]` |
| `大限` | `{ palaceName, ageRange, stem, mutagens[] }[]` |
| `流年` | `{ year, stem, branch, mutagens[], palaceName }[]`（可为空数组） |
| `四化分布` | `{ star, sihua: { name, effect }, palace }[]` |
| `格局提示` | `string[]` |

若出生日期超出离线工具范围且无上述内容：**停止生成断语**，请用户补充可靠上下文，或输出仅含「信息不足说明」的 HTML（不得编造星曜）。

### 流年节（若 HTML 含「年度运势」）

若使用离线工具，直接使用输出的 `yearlyContext`。若用户提供上下文，则除本命上下文外，还须 **【流年盘信息】** 块：流年干支、流年四化、流年命宫；当前大限干支与四化；重点宫位星曜。**禁止**仅靠公历年份自行臆造叠宫。

### K 线节

默认使用离线工具输出的 `klineData` 作为数值来源，直接填入 `report-template.html` 中 `#kline-data`。`klineContext` 只用于生成 `reason/brief` 等文字补充，不得让模型自由决定 `open/high/low/close`。

**数值口径（示意分，峰值稀缺）**：`tools/ziwei_offline.py` 先计算 1-100 岁 raw score，再做全生命相对映射；收盘上限约 **98**、最高可到 **100**（常量 `KLINE_CLOSE_CAP` / `KLINE_HIGH_CAP`），允许少数最强年份接近满分，但应避免长段贴顶。校验允许 ∈ [0,100]。

**路径 A 亮度**：纯 Python 排盘会为主星写入 `庙/旺/得/利/平/不/陷` 亮度（对齐 iztro `STARS_INFO`），并用于 K 线评分与 HTML 排盘图展示。路径 B 仍可用于 App/iztro 对齐验证。

**每条 `klineData` 含**：`age/year/ganZhi/daYun/daYunRange`、OHLC、`score`、`dimensions`（事业/财/情/健）、`yearlyMutagens`；合并 `kline-brief.json` 后可加 `brief`、可选 `reason`。

**报告页交互**：`report-template.html` 在 K 线图下提供**悬停详情**与**可展开的 1–100 岁数值表**；用户无需另查 JSON 即可看每年数字与简评。流年长文仍在「年度流年运势」节。

## 产品对齐（历法与派别）

与本目录规则基线一致（见 [`docs/rules-baseline.md`](docs/rules-baseline.md)）：**中州派**、正月初一分年/运限、`23:00` 晚子时换日。**不得**在未说明的情况下改用立春或其它流派。

时间口径：
- 默认固定 **UTC+8**（不回溯历史夏令时）；
- 若提供经纬度或可解析出生地，将使用真太阳时：`标准时 + 经度修正 + 时间方程`；
- CLI 默认 `--geocode-mode hybrid`：在线优先，失败回退 `tools/cn_locations.json`，再失败则回退标准时；
- 若需完全离线，可显式传 `--geocode-mode offline`；若需可复现坐标，优先传 `--longitude/--latitude`；
- 若缺少可用经纬度，则回退标准时并在输出中给出提示。

离线工具内置：

- 1900-2100 阳历转农历压缩表；
- 命宫/身宫、十二宫、五虎遁宫干、五行局；
- 紫微/天府与十四主星；
- 左辅右弼、文昌文曲、魁钺、禄存羊陀、火铃、空劫；
- 生年四化、大限、目标流年上下文。

当前有意保守：

- 不依赖外部排盘库的亮度体系，输出中亮度可为空；
- 不宣称与任何商业排盘工具 100% 一致，除非后续用样例逐条对齐。

## 执行步骤（agent）

1. **校验输入**：若有出生资料，先运行 `tools/ziwei_offline.py` 生成 JSON；若已有上下文，确认存在 `natalContext` 等价文本与 `yearlyContext`。
2. **排盘自检**：确认 JSON 含 `chart.palaces` 12 宫、`fiveElementsClass`、`natalContext`、`yearlyContext`、`klineContext`、`klineData`。
3. **渲染提示词（推荐）**：运行 `tools/render_prompts.py --payload-json payload.json --out-dir work --work-root work`，读取 `prompt-manifest.json`；**勿手抄** [prompts.md](prompts.md)，以渲染文件为唯一注入来源。
4. **模型生成产物**：
   - `natal.html`：用 `prompts/natal.system.md` + `natal.user.md`；
   - `yearly.html`：用 `yearly.system.md` + `yearly.user.md`；
   - `kline-brief.json`：用 `kline.system.md` + `kline.user.md`，仅可返回 `age/brief/reason`，不得返回或改写 `open/high/low/close`。
5. **K 线**：数值必须使用离线工具输出的 `klineData`；如需文字说明，只能将模型生成的 `brief/reason` 合并到对应年龄。
6. **K 线自检**（修正前不得写入 HTML）：
   - 恰 **100** 条，`age` 为 1–100 各出现一次；
   - `age===1` 时 `open === 50`；
   - 对 `age>1`：`open` 与上一条 `close` 在数值上一致（容差 1e-6，或两位小数相等）；
   - `high >= max(open,close)`，`low <= min(open,close)`，且所有数值 ∈ [0,100]；满分附近应是少数高峰，勿人为改成长段顶格。
7. **组装 HTML**：使用 `tools/generate_report.py` 与 [report-template.html](report-template.html) 组装；正式交付禁止 `--skip-validation`。页面顺序固定：**紫微排盘图** → **紫微命盘综合批注** → **流年运势** → **人生运势 K 线**（含悬停/表格查每年 OHLC 与 brief）→ **数据完整性状态**。将命盘 JSON 填入 `script#chart-data`，将综合/流年正文填入对应 `#content-*`，将合并后的 K 线 JSON 嵌入 `script#kline-data`；页脚保留与提示词等价的**免责声明**。
8. **输出**：向用户交付**完整** `<!DOCTYPE html>` 文档（可复制为 `.html` 文件后直接双击打开）。

## 运行模式

### 模式 A：模型增强（推荐）

- 使用离线工具得到 `natalContext/yearlyContext/klineData/klineContext`；
- 用 `render_prompts.py` 生成 prompt 文件与 `prompt-manifest.json`；
- 得到综合批注、流年正文与可选 `kline-brief.json` 后，用 `generate_report.py` 组装 HTML；
- K 线数值由工具生成并通过强校验；模型只可补充文字，不可改变走势数值。

## Quick Reference

| 报告章节 | System 提示来源 | User 数据来源 |
|---------|-----------------|---------------|
| 排盘上下文 | `tools/ziwei_offline.py` | 阳历日期 + 小时 + 性别 + 分析年 |
| 综合批注 | prompts.md 第 1 节 | `natalContext` |
| 年度运势 | prompts.md 第 2 节 | `natalContext` + `yearlyContext` |
| 人生 K 线 | 离线工具确定性评分 | `klineData`（数值）+ `klineContext`（文字参考） |

## Baseline Pressure Scenarios（无 skill 时常见失效）

记录在案，用于自检 skill 是否被遵守：

| 场景 | 常见错误行为 |
|------|----------------|
| 仅有生日性别 | 不运行离线工具，直接写命宫主星与断语 |
| 用户催促 | 跳过 K 线 JSON 连续性校验，或让模型替代确定性 K 线数值 |
| 环境惯性 | 在仅需 Python 路径时仍强迫 `npm install` / iztro（路径 A 不要 Node） |
| 交付形式 | 仅给 Markdown 片段，不给单文件 HTML |
| 流派 | 自行改用立春换年 |

## Red Flags — STOP & Realign

- 有出生资料却未运行 `tools/ziwei_offline.py` 就产出具体星曜落宫；
- 离线工具报错（日期超范围/输入缺失）仍继续断语；
- K 线 `open[n] ≠ close[n-1]` 仍入库；
- 有 `klineData` 却改用模型自由生成 `open/high/low/close`；
- 删除或改写免责声明以「更好看」；
- 将 `npm`、`iztro` 或 Node 列为**必选**才能完成报告（默认可用纯 Python；iztro 仅在为对齐 App 星曜时可选）。

## Rationalization Table

| 借口 | 事实 |
|------|------|
| 「差不多能推出命宫」 | 必须运行离线工具或读取可靠上下文 |
| 「用户没空打开应用」 | 正是使用离线工具的场景 |
| 「Markdown 对用户更方便」 | 本 skill 明确要求单文件 HTML |
| 「测试后再校验 K 线」 | 必须先校验再写入模板 |
| 「模型更懂走势」 | 模型只适合补充描述；数值走势必须来自确定性评分工具 |
| 「描述性一句话即可代替免责声明」 | 必须保留提示词中与参考性、勿执着一致的表述 |

## Common Mistakes

- 把 **HTML 外的裸 JSON** 当作最终交付物；
- **排盘**：手写星曜落宫而不是运行 `tools/ziwei_offline.py`；
- **流年**：缺大限锚点或 `yearlyContext` 却仍写叠宫；
- **K 线**：优先嵌入工具输出的 `klineData`；`year` 字段若填入，应与 `birthYear + age - 1` 一致；
- 在 skill 正文重复粘贴全套 system prompt——应引用 [prompts.md](prompts.md) 以保持单一事实来源。
