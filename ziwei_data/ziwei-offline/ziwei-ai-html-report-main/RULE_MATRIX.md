# ziwei-ai-html-report 规则映射矩阵

本文用于把本 skill 的规则基线映射到离线引擎实现与测试，确保规则可追溯、可校验、可回归。规则基线文档见 [`docs/rules-baseline.md`](docs/rules-baseline.md)。

## 1) 排盘算法规则映射

| 来源 | 规则要点 | 引擎实现 | 测试覆盖 | 状态 |
|---|---|---|---|---|
| `docs/rules-baseline.md#2. 排盘算法要点` | 命宫：月顺时逆，身宫：月顺时顺；十二宫逆布 | `life_palace_branch` `body_palace_branch` `arrange_palaces` | `test_life_and_body_palace_examples_match_algorithm_docs` | 已覆盖 |
| `docs/rules-baseline.md#2. 排盘算法要点` | 命宫干支定五行局（水二木三金四土五火六） | `five_elements_class` | `test_generate_chart_contains_required_context_blocks`（结构） | 部分覆盖（缺精确断言） |
| `docs/rules-baseline.md#2. 排盘算法要点` | 出生日与局数定紫微 | `ziwei_position` | `test_ziwei_position_examples_match_algorithm_docs` | 已覆盖 |
| `docs/rules-baseline.md#2. 排盘算法要点` | 紫微/天府两系十四主星排布 | `arrange_major_stars` | `test_major_star_series_from_documented_midday_example` | 已覆盖 |
| `docs/rules-baseline.md#2. 排盘算法要点` | 左右昌曲魁钺、禄存羊陀、火铃空劫、天马 | `auxiliary_stars` | `test_auxiliary_stars_includes_tianma` | 已覆盖 |
| `docs/rules-baseline.md#2. 排盘算法要点` | 年干起寅宫宫干 | `palace_stems` + `WUHU_START` | 结构已覆盖（待补精确值样例） | 部分覆盖 |

## 2) 四化与运限规则映射

| 来源 | 规则要点 | 引擎实现 | 测试覆盖 | 状态 |
|---|---|---|---|---|
| `docs/rules-baseline.md#2. 排盘算法要点` | 十干四化表 | `SIHUA_TABLE` `sihua_list` `mutagen_by_star` | `test_sihua_table_matches_reference` | 已覆盖（关键项） |
| `docs/rules-baseline.md#2. 排盘算法要点` | 起运=五行局数；阳男阴女顺、阴男阳女逆 | `decadal_ranges` `_current_decadal` | 新增顺逆分叉测试 | 部分覆盖 |
| `docs/rules-baseline.md#2. 排盘算法要点` | 流年地支定流年命宫，流年天干定四化 | `build_yearly_data` | 新增年份锚点测试 | 部分覆盖 |

## 3) 解读语义规则映射

| 来源 | 语义要点 | 当前实现 | 风险 | 改造策略 |
|---|---|---|---|---|
| `tools/knowledge_semantics.json#major_star_profiles` | 主星/吉煞基础语义 | `MAJOR_STAR_DESCRIPTIONS`（硬编码简版） | 语义浅、难维护 | 外置语义映射文件 |
| `tools/knowledge_semantics.json#palace_focus` | 十二宫解释框架 | 上下文仅列宫位与星曜 | 宫位意义缺失 | 外置宫位语义模板 |
| `tools/knowledge_semantics.json#pattern_rules` | 格局条件与提示 | `detect_patterns`（少量规则） | 成格条件过宽 | 外置格局规则并收紧条件 |

当前已实现：
- 语义外置文件：`tools/knowledge_semantics.json`
- 来源锚点：`major_star_sources` / `palace_focus_sources` / `pattern_rule_sources`
- 主星结构化释义：`major_star_profiles`（优点/风险/适配场景）在 `natalContext` 的命宫、身宫节按固定模板输出
- 模式识别由 `pattern_rules` 驱动，并在输出中附来源字符串，便于追溯。

## 4) 可靠性交付护栏映射

| 需求 | 实现位置 | 状态 |
|---|---|---|
| 上下文字段完整性校验（12宫/五行局/四化/大限/流年） | `validate_chart_integrity` | 已实现 |
| K线 100 条与 OHLC 连续性校验 | `validate_kline_data` + 模板前端校验 | 已实现 |
| 模板可见完整性状态提示 | `report-template.html` | 已实现 |
| prompts 生成前检查清单 | `prompts.md` | 已实现 |

## 5) 明确不覆盖项（当前版本）

- 不引入立春分年；坚持正月初一分年与晚子时换日。
- 不依赖 iztro 亮度体系；亮度字段保留可选空值。
- 不承诺与商业排盘工具 100% 一致（需样例逐条回归）。
