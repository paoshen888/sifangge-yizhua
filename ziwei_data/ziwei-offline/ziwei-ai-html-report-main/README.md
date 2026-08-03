# ziwei-ai-html-report

用 **AI 编程助手**（Cursor、Claude Code、Codex 等）为你的出生资料生成一份 **可保存、可分享的紫微斗数 AI 命盘报告**（单个 HTML 文件，含排盘示意图、综合解读、流年与人生运势 K 线示意）。

> 报告内容为传统术数的结构化展示与文字解读，**仅供文化学习与个人参考**，请勿用于医疗、投资或重大决策依据。

---

## 快速开始

你 **不需要** 自己懂紫微斗数，也 **不必会写代码**——装好 Skill 后，在对话里按格式提供出生信息即可；排盘与 HTML 组装由 AI 按本仓库规则完成。

### 路径 A：已安装 Skill

1. **新开一次 AI 对话**（让 Skill 生效）。
2. **复制下面这段话，改成你的信息**，发送给 AI。
3. 等待生成 **单个 HTML 文件**（可双击打开、保存或分享）。

```text
/ziwei-ai-html-report 帮我生成我的紫微斗数 AI 命盘报告

阳历生日: 1995-08-21
出生时间: 11:40
性别: 男
出生地: 广东省深圳市
流年分析年: 2026
```

触发方式因环境而异：优先用 **`/ziwei-ai-html-report`**；若未注册斜杠命令，可在对话里说明「请严格按 `ziwei-ai-html-report` skill 生成离线 HTML 报告」，或用 **`@`** 引用已安装目录下的 `SKILL.md`。

### 路径 B：尚未安装 Skill

1. **先安装**（推荐一条命令，见下文 [安装方式](#安装方式)）。
2. **新开一次 AI 对话**。
3. **复制 [路径 A](#路径-a已安装-skill) 中的对话模板**，改成你的信息后发送。

安装后你会得到与路径 A 相同的体验；无需先 `git clone` 整个仓库（CLI 会从 GitHub 拉取并链到 agent 的 skills 目录）。

---

## 安装方式

思路都一样：**让 AI 能读到本仓库的 `SKILL.md` 和配套文件**（`prompts.md`、`report-template.html`、`tools/` 等）。下面按推荐顺序排列。

### 推荐：一条命令安装（Cursor / Claude Code / Codex 等）

在任意项目目录执行（安装到**当前项目**，便于团队共享）：

```bash
npx skills add archlizheng/ziwei-ai-html-report -y
```

安装到**本机所有项目**（个人常用）：

```bash
npx skills add archlizheng/ziwei-ai-html-report -g -y
```

仅安装到 **Cursor**：

```bash
npx skills add archlizheng/ziwei-ai-html-report -a cursor -y
```

安装后请 **新开对话**。Skill 名称为 **`ziwei-ai-html-report`**（与 `SKILL.md` 一致）。更新已安装的 skill：

```bash
npx skills update ziwei-ai-html-report
```

仅查看本仓库里有哪些 skill、不实际安装：

```bash
npx skills add archlizheng/ziwei-ai-html-report --list
```

`npx skills add` 会从 GitHub 拉取仓库并写入 agent 约定的 skills 目录，**不必先手动 clone**。

### 备选：手动克隆或复制仓库

若你更习惯本地有一份完整源码，或当前环境不支持 skills CLI，可用下面三种常见做法。

#### 1）Cursor

- **做法 A（推荐）**：把整个仓库克隆到你的电脑，在 Cursor 里 **打开该文件夹作为工作区**，或把仓库放进你当前项目下的子目录（例如 `skills/ziwei-ai-html-report/`）。
- **做法 B**：若你使用 Cursor 的 **Agent Skills**：把本仓库复制到 Cursor 约定的 skills 目录（以你当前 Cursor 版本说明为准），保证其中有 `SKILL.md`。

在对话里可以：

- 用 **`@`** 引用本仓库的 `SKILL.md`，或
- 若你已配置技能别名，使用类似 **`/ziwei-ai-html-report`** 触发（取决于你的规则/技能配置是否绑定了该指令）。

#### 2）Claude Code

将本仓库整体复制到 Claude Code 的 **skills 目录**（具体以官方文档为准），例如用户级 `~/.claude/skills/` 或项目内的 `.claude/skills/`，在其中新建一个子文件夹（名称随意，建议与本仓库目录名一致），并保证其中有 **`SKILL.md`**。之后在项目里按该工具的说明加载 skill 即可。

#### 3）Codex / 其它 CLI 或 IDE 插件

- 若支持 **skills 目录**：同样在对应位置放入本仓库（含 `SKILL.md`）。
- 若暂不支持：**把 `SKILL.md` 的全文或路径提供给对话**，并说明「请严格按该 skill 生成离线 HTML 报告」。

#### 你需要保留哪些文件？

最少要保证 AI 能访问：**`SKILL.md`**、**`prompts.md`**、**`report-template.html`**、**`tools/ziwei_offline.py`**（以及 `tools/` 下的数据文件）。本仓库已打包齐全，**整体克隆或复制**最省事。

---

## 字段说明（照抄格式最稳）

| 信息 | 怎么填 |
|------|--------|
| 阳历生日 | `YYYY-MM-DD`，例如 `1995-08-21` |
| 出生时间 | `HH:mm`（24 小时制）；**23:00–23:59** 在本工具里按**晚子时换日**处理 |
| 性别 | `男` / `女`（或 `male` / `female`） |
| 出生地 | 建议写到市/区，用于**真太阳时**换算；也可在 skill 说明里改用纯离线或经纬度 |
| 流年分析年 | 想重点看的公历年份，例如 `2026` |

**支持范围**：阳历 **1900-01-31 至 2100-12-31**。超出范围需换其它工具或自备命盘上下文。

---

## 适合谁

- 希望 **对话里说清生日**，就让 AI 按固定规则排盘并写出报告的人。
- 需要 **离线 HTML**（可双击打开、发邮件、存网盘），而不是只在某个 App 里看的人。

AI 会依照本仓库里的 **Skill**（[`SKILL.md`](./SKILL.md)）与提示词约定来生成内容。

---

## AI 会为你做什么（你只需要知道结果）

1. 用本仓库自带的 **Python 排盘脚本** 生成结构化命盘、`klineData` 与提示词上下文。
2. 渲染综合批注、流年与 K 线文字补充提示词，供模型撰写正文。
3. 模型撰写综合/流年解读与可选 K 线简述；K 线数值始终来自工具生成的 `klineData`，不由模型编造。
4. 将内容填入 **`report-template.html`**，校验通过后输出 **单个 HTML 文件**。

若某一步信息不足（例如日期超范围），按约定应 **停止编造**，并提示你补资料——这是正常现象。

---

## 可选：命令行与标准 Agent 工作流

本节面向熟悉终端的用户；日常生成报告走 [快速开始](#快速开始) 即可。

### 只要排盘 JSON

本机安装 **Python 3** 后，在仓库根目录执行：

```bash
python3 tools/ziwei_offline.py \
  --solar 1996-01-06 \
  --time 11:30 \
  --gender female \
  --birthplace "广东省佛山市顺德区" \
  --target-year 2026 \
  --format json
```

输出中含 `natalContext`、`yearlyContext`、`klineContext`、`klineData`。完整 HTML 仍建议走 **Skill + 模板** 流程。

### 标准 Agent 工作流

```bash
python3 tools/ziwei_offline.py \
  --solar 1996-01-06 \
  --time 11:30 \
  --gender female \
  --birthplace "广东省佛山市顺德区" \
  --target-year 2026 \
  --format json > work/payload.json

python3 tools/render_prompts.py \
  --payload-json work/payload.json \
  --out-dir work \
  --work-root work

# 按 work/prompt-manifest.json 调用模型，生成：
# - work/natal.html
# - work/yearly.html
# - work/kline-brief.json（可选，只含 age/brief/reason）

python3 tools/generate_report.py \
  --payload-json work/payload.json \
  --natal-html work/natal.html \
  --yearly-html work/yearly.html \
  --kline-brief-json work/kline-brief.json \
  -o work/report.html
```

---

## 常见问题

- **一定要联网吗？**  
  不必须。联网主要用于出生地地理编码；失败会回退内置城市表或标准时，详见 [`SKILL.md`](./SKILL.md)。
- **和某 App 排盘是否每个字都一样？**  
  本仓库默认是**中州派口径**的离线实现；若要与某 App **星曜完全一致**，`SKILL.md` 中说明了可选的 iztro（Node）路径。
- **报告里的 K 线是预测吗？**  
  不是。K 线为基于命盘语义的**示意曲线**，模板内亦有说明。
- **日期格式不对或超出范围？**  
  须为 `YYYY-MM-DD`，且在 **1900-01-31～2100-12-31** 内；超出范围请勿让 AI 编造命盘。
- **出生地无法解析？**  
  对话场景下可让 AI 按 skill 中的回退规则处理；命令行可在 `SKILL.md` 中查阅 `--geocode-mode offline` 或 `--longitude` / `--latitude`。
- **命令行报时间相关错误？**  
  推荐 `HH:mm`，须提供 `--time` 或 `--hour`。

---

## 开发者与仓库信息

- 规则与契约：**[SKILL.md](./SKILL.md)**、**[prompts.md](./prompts.md)**
- 历法与派别说明：**[docs/rules-baseline.md](./docs/rules-baseline.md)**
- 运行测试：`python3 -m unittest discover -s tests -p "test_*.py"`
- 许可证：**[LICENSE](./LICENSE)**

本仓库可 **单独克隆使用**，不依赖其它项目目录。

---

## GitHub 发布版保证（给集成者与 Agent）

- 本仓库可单独克隆、复制、运行，不依赖其它私有目录。
- 核心排盘、提示词渲染、HTML 组装与校验仅需 **Python 3 标准库**；iztro 仅用于可选对齐路径。
- **失败契约**：输入越界、上下文不完整、或 K 线数据未通过校验时，应停止杜撰星曜落宫，并提示用户补资料或修正数据。
