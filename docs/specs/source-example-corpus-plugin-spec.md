# TIKZ-FunFig 源码示例知识库、论文级模板与 Codex Plugin 重构 Spec

| 项目 | 内容 |
| --- | --- |
| 文档编号 | TFF-SPEC-002 |
| 文档版本 | 0.1-draft |
| 日期 | 2026-09-24 |
| 状态 | **已确认，实施中；M0 起按本文件作为施工基线** |
| 产品 | TIKZ-FunFig / plugin id `tikz-funfig` |
| 当前产品版本 | 0.9.0 |
| 当前仓库基线 | `main` @ `6c27000`；M0 从用户提供的 PGF 3.1.11a 文档源码快照开始 |
| 本轮目标 | 清理仓库职责边界；建立 PGF/TikZ/PGFPlots 源码示例知识库；建立论文级模板/Golden/QA 体系；保持可安装 Codex Plugin |
| 非本轮动作 | 本 Spec 未确认前，不移动现有目录、不改 runtime、不批量导入第三方仓库、不改变现有 Plugin 行为 |

### 实施状态（2026-09-24）

- M0–M7 已实现并纳入全仓回归检查。
- M8 gate 已执行：官方语法、PGFPlots、中文自然语言以及社区长尾
  architecture/scientific queries 均能由现有 FTS5/BM25 检索稳定命中。
- 因当前 benchmark 未证明向量检索能解决一个实际失败模式，**M8 不实施
  embedding/vector DB**；继续以来源可审计的 lexical/metadata 检索为基线。

## 0. 结论

TIKZ-FunFig 不应继续发展成“一个装了很多 TeX 文件的 Skill”，而应收敛为一个可安装的 **学术图形生成 Plugin**：

1. 用户以自然语言描述论文图；
2. Plugin 判断图形家族、语义、数据、布局与出版目标；
3. 先查询稳定 Recipe/Template，再查询已编译示例和官方源码案例；
4. 生成或修改结构化 FigureSpec；
5. 由确定性 renderer 输出 TikZ/PGFPlots；
6. 编译为矢量 PDF，并按需生成 SVG/预览；
7. 在最终论文尺寸上执行技术 QA + 视觉 QA；
8. 将新的高质量模式逐步提升为 Template、Golden 或 Recipe。

核心原则：

> **原始源码负责“提供证据和长尾技巧”，Template/Golden/Recipe 负责“提供稳定生产能力”。**

不把几千个外部例子直接当模板，也不让 Agent 每次从整本手册重新学习。

---

## 1. 当前仓库审计

### 1.1 已经正确的主架构

当前主线应保留：

```text
Natural language / existing FigureSpec
                ↓
          Skill routing
                ↓
       Recipe + Knowledge
                ↓
           FigureSpec
                ↓
      deterministic renderer
                ↓
            figure.tex
                ↓
             compile
                ↓
       PDF / SVG / manifest
                ↓
              QA
```

现有 `FigureSpec → Recipe → Renderer → Build → QA` 方向正确，不需要推翻。

### 1.2 当前已经存在的稳定资产

- `schemas/`：FigureSpec contract。
- `recipes/`：20 个左右 Recipe，包括 plots、flowchart、framework、relations、schematic。
- `themes/`：期刊黑白、低饱和彩色、演示等主题。
- `profiles/`：single-column、double-column、presentation 出版尺寸/可读性约束。
- `knowledge/cards/`：人工整理的可验证知识卡。
- `knowledge/examples/`：与知识卡关联的最小可编译例子。
- `knowledge/manual-index/`：PGF/TikZ 3.1.11a section-level corpus。
- `examples/golden/`：已验证的回归图。
- `packages/skills/`：5 个专项 Skill。
- `packages/skill/`：统一入口 Skill。
- `packages/plugin/tikz-funfig/`：生成后的 portable Plugin。

这些层应该继续保留，但需要更清楚地区分：

1. 原始外部源码；
2. 规范化检索语料；
3. 人工/项目维护知识；
4. 可编辑模板；
5. 回归 Golden；
6. 确定性 Recipe；
7. 生成后的 Plugin 副本。

### 1.3 新增的 PGF 官方源码

当前 `doc/generic/pgf/` 是一套非常有价值的上游文档源码：

- 约 **133 个 `.tex` 文件**；
- 约 **2870 个 `codeexample`**；
- 约 **1101 个 `tikzpicture`**；
- 总体约 **4.9 MB**；
- 包含官方 `extract.lua`；
- 包含 PGF 文档许可证与 manifest。

它应成为第一套 **Source Example Corpus** 的原始来源，但不能继续以顶层 `doc/` 的身份混在产品代码旁边。

### 1.4 当前混乱的主要原因

| 问题 | 后果 |
| --- | --- |
| 顶层 `doc/`、`references/`、`knowledge/` 都能看起来像“知识源” | 后续 Agent/贡献者不知道哪一层可运行、哪一层只溯源 |
| `knowledge/examples` 与 `examples/golden` 名称接近但职责不同 | 容易把最小语法例当成产品模板 |
| 外部源码没有统一 source registry | 无法稳定记录版本、许可证、hash、导入策略 |
| Template 概念尚未成为一级产品对象 | Agent 常需要从零设计，不能优先复用成熟布局 |
| Knowledge search 主要覆盖 cards/manual | 尚不能检索几千个真实源码案例 |
| 第三方图库没有引入门槛 | 容易把许可证、风格质量、可编译性混在一起 |
| Plugin 目前可携带 manual corpus，但还没有 corpus 分层策略 | 随着源码库增长会变重、难审计 |

---

## 2. 产品目标

### 2.1 用户体验

典型输入：

- “画一个三层研究框架图，上层是政策环境，中层是学校和家庭，下层是学习者结果。”
- “把这个机制图改成黑白中文期刊风格，宋体，箭头更细，分组框用虚线。”
- “根据 CSV 画均值、95% CI 和显著性标注，适合双栏论文。”
- “画一个 Transformer encoder–decoder 架构，突出 cross-attention。”
- “画一个实验装置示意图，标出激光、透镜、样品、探测器和传播方向。”
- “这张截图保持语义关系不变，用优雅的 TikZ 学术风格重画。”

期望输出：

```text
figure.funfig.json      可继续修改的语义源
figure.tex              可独立审阅的 TikZ/PGFPlots
figure.pdf              论文级矢量主产物
figure.svg              可选
.funfig/manifest.json   来源、Recipe、依赖、验证状态
```

### 2.2 质量目标

“论文级”至少同时满足：

- 语义没有被 Agent 擅自添加或改变；
- 最终尺寸下文字可读；
- 节点、标签、箭头无明显遮挡；
- 留白和视觉层次稳定；
- 黑白打印或色觉友好主题可用；
- 线宽、marker、箭头尺度与最终版面匹配；
- PDF 为矢量主产物；
- TeX 源可编译、可复现、无机器绝对路径；
- 用户后续只改数据、标签、结构时不需要整图重写。

---

## 3. 目标仓库目录

确认后，按下列结构施工。

```text
tikz-funfig/
├── AGENTS.md
├── README.md
├── CHANGELOG.md
│
├── src/                         # canonical runtime
├── schemas/                     # FigureSpec / metadata schemas
├── recipes/                     # stable/experimental semantic recipes
├── themes/                      # appearance tokens
├── profiles/                    # publication/output constraints
│
├── knowledge/                   # normalized, searchable, runtime-capable knowledge
│   ├── aliases.json
│   ├── cards/                   # project-authored knowledge cards
│   ├── examples/                # small project-authored verified snippets
│   ├── manual-index/            # normalized official manual text index
│   └── corpus/                  # NEW: source-example retrieval corpus
│       ├── index.json
│       ├── examples.jsonl
│       ├── sources.json
│       └── code/                # only normalized snippets allowed for runtime
│
├── examples/
│   ├── demos/                   # NEW: user-facing quick examples
│   ├── templates/               # NEW: editable paper-grade figure templates
│   │   ├── plots/
│   │   ├── flowcharts/
│   │   ├── frameworks/
│   │   ├── relations/
│   │   ├── schematics/
│   │   └── architectures/
│   └── golden/                  # deterministic regression/acceptance cases
│
├── sources/                     # NEW: raw upstream/reference source material; dev only
│   ├── README.md
│   ├── registry.json
│   ├── official/
│   │   ├── pgf/
│   │   │   ├── source.json
│   │   │   └── upstream/
│   │   │       └── doc/generic/pgf/...
│   │   └── pgfplots/
│   │       ├── source.json
│   │       └── upstream/...
│   └── community/
│       ├── opentikz/
│       ├── janosh-diagrams/
│       └── petarv-tikz/
│
├── references/                  # project/historical provenance only
│   ├── README.md
│   ├── legacy/
│   └── methods/
│
├── scripts/                     # import/extract/index/verify/sync/release
├── tests/
├── docs/
│   ├── architecture.md
│   ├── recipes/
│   └── specs/
│
└── packages/
    ├── skill/                   # canonical general Skill
    ├── skills/                  # canonical specialized Skills
    └── plugin/tikz-funfig/      # GENERATED portable Plugin; no manual edits
```

### 3.1 目录职责硬规则

| 目录 | 是否 canonical | 是否进入 Plugin | 允许 Agent 运行时依赖 |
| --- | --- | --- | --- |
| `src/` | 是 | 是 | 是 |
| `schemas/` | 是 | 是 | 是 |
| `recipes/` | 是 | 是 | 是 |
| `themes/` | 是 | 是 | 是 |
| `profiles/` | 是 | 是 | 是 |
| `knowledge/` | 是 | 精简后是 | 是 |
| `examples/templates/` | 是 | 精选后是 | 是 |
| `examples/golden/` | 是 | 默认否 | 测试使用 |
| `sources/` | 是（来源记录） | **否** | **否** |
| `references/` | 是（历史溯源） | **否** | **否** |
| `packages/plugin/tikz-funfig/` | 否，生成物 | 自身就是分发物 | 是 |

### 3.2 当前目录迁移映射

确认施工后：

| 当前路径 | 目标路径 | 说明 |
| --- | --- | --- |
| `doc/generic/pgf/` | `sources/official/pgf/upstream/doc/generic/pgf/` | 保留上游相对结构，便于使用官方 extractor |
| `references/manuals/pgfmanual-3.1.11a/` | `sources/official/pgf/derived/pdf-index/` 或合并进 source manifest | 不再让 `references` 同时承担官方 source 层 |
| `knowledge/manual-index/` | 保持 | 已是 runtime normalized index |
| `knowledge/examples/` | 保持 | 明确定义为“最小验证 snippet”，不是模板 |
| `examples/golden/` | 保持 | 继续作为 regression |
| 顶层普通示例目录 | `examples/demos/` | 统一 quickstart |

迁移必须使用 `git mv`，并在一个独立 commit 中完成，避免和 runtime 行为改动混合。

---

## 4. 四层知识模型

以后不再笼统称“知识库”，而明确为四层。

### K0 — Source / Provenance

位置：`sources/`、`references/`

内容：

- 官方 PGF/TikZ 文档源码；
- PGFPlots 文档源码；
- 第三方开源图例仓库；
- 历史论文图、旧代码；
- source URL、commit/tag、license、hash。

职责：提供证据、来源和长尾技巧。

限制：

- runtime 不直接搜索整棵 raw tree；
- raw source 永远不能成为某项 stable capability 的唯一依赖；
- 不允许直接把外部仓库 checkout 打进 Plugin。

### K1 — Search Corpus

位置：`knowledge/manual-index/`、`knowledge/corpus/`

内容：

- manual sections；
- 从 `codeexample` 抽取的真实示例；
- example metadata；
- 技术关键词、library、command、figure family、layout/style traits；
- 编译结果与 source locator。

职责：让 Agent 快速找到“类似问题是如何实现的”。

### K2 — Curated Knowledge / Template

位置：`knowledge/cards/`、`knowledge/examples/`、`examples/templates/`

内容：

- 项目维护的知识卡；
- 最小可编译 snippet；
- 可编辑、可复用、具有明确参数边界的论文级模板。

职责：成为日常生成的首选参考。

### K3 — Product Capability

位置：`recipes/`、`schemas/`、`src/`、`examples/golden/`

内容：

- stable/experimental Recipe；
- FigureSpec schema；
- renderer/method；
- regression golden；
- tests。

职责：提供可重复、可验收的产品能力。

### 4.1 Promotion Pipeline

```text
external/raw source
      ↓ extract
normalized corpus example
      ↓ compile + classify
verified corpus example
      ↓ repeated usefulness / quality review
curated template or knowledge card
      ↓ stable semantics + regression demand
Recipe / Method + Golden
```

**一个外部例子可以被检索，不等于它已经成为 TIKZ-FunFig 的产品能力。**

---

## 5. Source Registry

`sources/registry.json` 统一记录外部来源。

建议字段：

```json
{
  "schema_version": "1.0",
  "sources": [
    {
      "id": "pgf-manual-source",
      "kind": "official",
      "project": "PGF/TikZ",
      "upstream": "https://github.com/pgf-tikz/pgf",
      "revision": "<pinned tag or commit>",
      "local_root": "sources/official/pgf/upstream",
      "license_ids": ["LPPL-1.3c", "GFDL-1.2"],
      "ingest": "development",
      "plugin_policy": "normalized-only",
      "verified": "2026-09-24"
    }
  ]
}
```

每个 source 必须固定 revision；禁止只写 `main` 然后静默更新。

### 5.1 第一优先级来源

#### A. PGF/TikZ official

- 当前已放入仓库。
- 上游：`https://github.com/pgf-tikz/pgf`
- 价值：TikZ 核心语法、node/path/matrix/graph drawing/decorations/libraries 等。
- 当前源码内自带 `extract.lua`，可以提取 `codeexample`。
- 文档源码按上游许可证管理；保留 source manifest 和 license 文件。

#### B. PGFPlots official

- 上游：`https://github.com/pgf-tikz/pgfplots`
- 第二阶段接入。
- 重点：line/scatter/errorbar/bar/area/mesh/surface/contour/quiver/histogram/groupplot/polar/ternary 等。
- 不用 PGF manual 的 Data Visualization 章节替代 PGFPlots 官方手册。

### 5.2 第二优先级来源

以下来源只在完成 source/licensing gate 后接入：

| source | 主要价值 | 初始策略 |
| --- | --- | --- |
| OpenTikZ | 学术概念图、AI/ML architecture、pipeline、template edit contract | 优先学习 metadata/edit-contract 设计；内容按 source policy 导入 |
| janosh/diagrams | physics / chemistry / ML 科学图 | 只导入可独立编译且风格/许可证合格项 |
| PetarV-/TikZ | GNN/CNN/attention/RL/graph 等论文图 | 作为 architecture/relation 候选 corpus |

第三方内容默认不自动晋升 Template，更不直接晋升 Recipe。

---

## 6. Source Example Corpus

### 6.1 Corpus 的目标

让下面的自然语言可以检索到真实 TikZ 方法：

- “三个层级、组框、反馈箭头”
- “贝塞尔曲线绕开中间节点”
- “双栏论文里的 confidence band”
- “节点下面放小字说明”
- “箭头穿过背景组框但不要遮标签”
- “Transformer encoder decoder”
- “实验装置光路”
- “黑白期刊风格”

Agent 不应该需要猜用户会不会说 `arrows.meta`、`fit`、`positioning`。

### 6.2 Example metadata schema

每个 corpus item 必须有稳定 metadata。

```json
{
  "id": "pgf-positioning-00042",
  "source_id": "pgf-manual-source",
  "source_kind": "official",
  "source_locator": {
    "path": "doc/generic/pgf/pgfmanual-en-tikz-shapes.tex",
    "section": "Positioning Nodes",
    "ordinal": 42
  },
  "title": "Relative node positioning",
  "summary": "Place nodes relative to named anchors with the positioning library.",
  "figure_families": ["framework", "flowchart"],
  "intents": ["relative positioning", "node layout"],
  "domains": [],
  "tags": ["layout", "nodes"],
  "libraries": ["positioning"],
  "packages": ["tikz"],
  "commands": ["\\node"],
  "style_traits": ["minimal"],
  "layout_traits": ["relative", "left-to-right"],
  "engine": "pdflatex",
  "requires_shell_escape": false,
  "standalone": true,
  "compile_status": "passed",
  "verification": "source-compiled",
  "license_id": "LPPL-1.3c",
  "source_hash": "...",
  "code_hash": "..."
}
```

### 6.3 额外分类字段

Corpus 应支持：

- `figure_families`
  - plot
  - flowchart
  - framework
  - relation
  - schematic
  - architecture
  - geometry
  - tree
  - graph
  - state
- `layout_traits`
  - layered
  - grid
  - radial
  - tree
  - left-to-right
  - top-down
  - grouped
  - nested
  - freeform
- `style_traits`
  - monochrome
  - minimal
  - technical
  - publication
  - color-safe
  - dense
  - annotated
- `interaction_traits`
  - directed
  - bidirectional
  - feedback
  - branching
  - merge
  - containment
  - sequence

这些字段用于自然语言检索，不用于擅自推断科学含义。

### 6.4 Corpus code policy

Corpus code 分三种：

1. `source-only`：只记录 locator，不进入 runtime bundle；
2. `normalized`：经过解析/清理后可以进入 runtime corpus；
3. `project-authored`：TIKZ-FunFig 自己重写的最小语法/模板，可作为稳定输入。

外部代码不得因为“能编译”就自动成为 `project-authored`。

---

## 7. PGF 官方源码抽取方案

### 7.1 不从 PDF 重新 OCR 代码

PGF 已有原始 LaTeX 文档源和官方 `extract.lua`。

第一阶段直接以：

`sources/official/pgf/upstream/doc/generic/pgf/*.tex`

作为 source of truth。

PDF 只用于：

- 页码/视觉溯源；
- 检查某些代码与最终渲染的上下文；
- 人工核对。

### 7.2 Extract pipeline

```text
PGF manual .tex
    ↓
parse codeexample + section context
    ↓
reconstruct standalone example
    ↓
static safety scan
    ↓
compile
    ↓
extract command/library/package metadata
    ↓
classify figure/layout/style traits
    ↓
write examples.jsonl + normalized code
    ↓
FTS index at runtime
```

### 7.3 官方 `extract.lua` 的定位

官方 script 应作为 **行为参考和验证 oracle**，不直接成为 TIKZ-FunFig runtime 依赖。

原因：

- 它依赖 Lua modules；
- 它解决的是 PGF 自身 manual regression，不包含我们的 metadata；
- 我们还需要 section path、source hash、tags、libraries、figure family；
- Plugin runtime 应保持轻量。

施工时优先：

1. 先用官方 extractor 对一批文件验证抽取数量；
2. 再实现项目自己的 deterministic importer；
3. 对同一 source file 做 count/hash regression。

### 7.4 第一批 PGF 重点主题

不需要一开始给 2870 个例子全部打高精标签。

先处理：

- nodes / anchors；
- positioning；
- matrix；
- fit / backgrounds；
- arrows.meta；
- paths / to paths；
- calc；
- chains；
- shapes；
- graphs / trees；
- graph drawing layered / force / circular；
- decorations；
- patterns / shadings；
- pics；
- intersections；
- datavisualization（仅作为 PGF 能力，不替代 PGFPlots）。

---

## 8. Template Library

Corpus 是“参考”，Template 是“可直接修改的成熟起点”。

### 8.1 Template 目录

```text
examples/templates/<family>/<template-id>/
├── template.tex
├── template.meta.json
├── preview.svg             # 可选，repo 中是否保留由体积策略决定
└── README.md               # 只有复杂模板需要
```

### 8.2 Template metadata

```json
{
  "id": "framework-layered-feedback",
  "version": "1.0",
  "family": "framework",
  "title": "Layered framework with feedback",
  "description": "Three-level grouped academic framework with one return path.",
  "recipe_hint": "framework-diagram",
  "supported_profiles": [
    "journal-single-column",
    "journal-double-column"
  ],
  "supported_themes": [
    "journal-monochrome",
    "journal-muted"
  ],
  "requires": {
    "packages": ["tikz"],
    "libraries": ["positioning", "fit", "arrows.meta"]
  },
  "edit_contract": {
    "editable": ["labels", "groups", "node_count", "edge_labels"],
    "structural_limits": {
      "layers": [2, 5]
    },
    "locked": ["semantic_direction_is_user_supplied"]
  },
  "verification": "compiled-and-visual-reviewed"
}
```

### 8.3 Edit Contract

每个成熟 Template 必须明确：

- 哪些文本可替换；
- 哪些节点可以增删；
- 哪些数量变化仍适用当前布局；
- 哪些位置由 renderer/constraint 决定；
- 哪些语义必须由用户提供；
- 何时必须退出模板，改走 Recipe/Expert Mode。

Template 不能只是“一个看起来很好看的 `.tex` 文件”。

### 8.4 首批 Template 家族

#### Plots

- single-series function；
- two/multi-series comparison；
- scatter + regression/fit annotation；
- error bar；
- confidence band；
- grouped multi-panel；
- threshold/regime；
- heatmap；
- contour；
- surface；
- quiver/vector field。

#### Flowcharts

- linear process；
- decision branch；
- branch + merge；
- feedback loop；
- swimlane-like grouped process（非正式 BPMN）。

#### Frameworks

- layered framework；
- grouped framework；
- input–mechanism–outcome；
- context–process–outcome；
- multi-level ecological framework；
- mediation/moderation-like visual skeleton（只有用户明确语义时使用）。

#### Relations

- labelled directed relation；
- bidirectional relation；
- grouped relation network；
- small concept network；
- simple DAG-like relation（不自动推断因果）。

#### Schematics

- experimental pipeline；
- measurement setup；
- coordinate/mechanism diagram；
- annotated component chain；
- scientific process schematic。

#### Architectures

- encoder–decoder；
- multi-stage ML pipeline；
- neural network block architecture；
- multimodal/fusion architecture；
- training/inference split。

Architectures 初期仍由 framework/schematic Skill 处理；只有数据证明工作流明显独立时才新增 Skill。

---

## 9. Golden 与 Template 的区别

| 对象 | 目的 | 是否面向用户修改 | 是否 regression |
| --- | --- | --- | --- |
| corpus example | 检索技术方法 | 否 | 抽取/编译检查 |
| knowledge example | 解释最小语法 | 很少 | 是 |
| template | 成熟设计起点 | 是 | 应有 compile test |
| golden | 锁定产品行为 | 否 | **是，核心用途** |
| recipe | 稳定生成能力 | 间接通过 FigureSpec | **是** |

一个 Template 可以对应一个 Golden，但两者不是同一个概念。

---

## 10. 搜索与检索

### 10.1 继续使用 SQLite FTS5/BM25

第一阶段 **不引入 embedding/vector DB**。

TikZ 查询有大量高价值精确词：

- library；
- command；
- package；
- Recipe；
- shape；
- axis；
- edge routing；
- layout；
- graph drawing；
- figure family。

当前 FTS5 路线足够成为第一版可靠检索器。

只有建立真实 query benchmark 后，若 Top-5 recall 对自然语言长尾明显不足，才增加可选语义 reranker。

### 10.2 统一可检索对象

`tff kb search` 应覆盖：

- `card`
- `manual`
- `example`
- `template`
- `golden` metadata
- `recipe`

但必须显示不同类型和 verification level。

### 10.3 建议检索优先级

对生成任务：

1. compatible stable Recipe；
2. compiled + reviewed Template；
3. Golden metadata；
4. compiled project knowledge example；
5. compiled official source example；
6. reviewed community example；
7. official manual section；
8. raw/reference-only content。

不是简单按 BM25 一次排序到底。

### 10.4 搜索字段权重

建议初始权重：

| 字段 | 权重倾向 |
| --- | ---: |
| recipe/template exact id | 12 |
| figure family / intent | 10 |
| libraries | 9 |
| commands | 9 |
| layout traits | 8 |
| title | 8 |
| tags / aliases | 7 |
| style traits | 6 |
| summary | 4 |
| body/code | 2 |
| source | 1 |

权重必须用 benchmark 调整，不写死成产品事实。

### 10.5 结果去重与多样化

同一个 manual section 中 20 个只差一个参数的示例不能占满 Top-8。

结果应按：

- source；
- family；
- library；
- structural fingerprint

做轻量 diversify。

---

## 11. Figure taxonomy 与 Skills

现有 6 Skill 架构保持，不机械新增 Skill。

| Skill | 首要任务 |
| --- | --- |
| `TIKZ-FunFig` | 模糊请求、混合请求、修订、迁移、统一入口 |
| `funfig-plots` | 数据/函数/统计/PGFPlots |
| `funfig-flowcharts` | 步骤、判断、分支、合流、反馈 |
| `funfig-frameworks` | 研究框架、概念模型、系统模块、ML architecture 中的块结构 |
| `funfig-relations` | 概念网络、标签边、关系图、小型 DAG-like 表达 |
| `funfig-schematics` | 实验、机制、几何、装置、科学过程 |

### 11.1 暂不新增独立 Skill 的类型

- mindmap；
- tree；
- state machine；
- Petri net；
- formal ER；
- mathematical geometry；
- AI/ML architecture；
- causal DAG。

先作为 Recipe/template/capability 发展。

满足以下条件后才晋升独立 Skill：

1. 用户意图长期明显独立；
2. 有独立知识和 QA；
3. 有至少数个稳定 Recipe/template；
4. 与现有 Skill 路由冲突明显；
5. 独立 Skill 能减少而不是增加上下文负担。

---

## 12. 自然语言到成图的标准工作流

```text
1. Parse request
   ├── figure family
   ├── scientific/semantic content
   ├── data
   ├── requested style
   ├── output size/profile
   └── existing figure/image?

2. Preserve semantics
   └── do not invent data/causal relation/scientific mechanism

3. Route
   └── Skill → Recipe/Template candidates

4. Retrieve
   ├── cards
   ├── templates
   ├── golden metadata
   └── 2–5 relevant corpus examples

5. Plan layout
   ├── semantic structure
   ├── final-size constraints
   └── theme/profile

6. Produce or update FigureSpec

7. Render deterministic TeX

8. Compile in controlled build directory

9. Inspect final-size output
   ├── overlap
   ├── clipping
   ├── label readability
   ├── line/arrow scale
   ├── hierarchy/spacing
   └── grayscale/accessibility if applicable

10. Repair until acceptance

11. Deliver FigureSpec + TeX + PDF (+ SVG if requested)
```

---

## 13. Publication Profiles

现有 Profile 思路继续扩展，而不是为每个期刊写一整套 renderer。

### 13.1 基础 Profile

至少保留：

- `journal-single-column`
- `journal-double-column`
- `presentation`

可新增：

- `journal-wide-single`
- `preprint-full-width`
- `poster-panel`

期刊/会议专有 profile 只有在尺寸规则明确、长期稳定时才添加。

### 13.2 Profile 管什么

- target width/height envelope；
- minimum text size；
- default gaps；
- minimum line/marker/arrow sizes；
- max label density；
- final-size QA flags；
- vector/raster policy。

### 13.3 Theme 管什么

- color；
- fill；
- stroke；
- line weight tokens；
- rounded corners；
- role appearance；
- grayscale-safe palette。

**Profile 决定“多大、能不能读”；Theme 决定“长什么样”。**

---

## 14. 视觉风格原则

论文图默认不追求 UI/marketing 风格。

### 14.1 默认学术风格

- 低装饰；
- 线条克制；
- 清晰的视觉层次；
- 尽量少用阴影、渐变、大圆角；
- 颜色用于编码，不用于装饰；
- 无必要不引入图标；
- 保持足够 whitespace；
- 长文本优先换行/分组，不缩到不可读；
- 箭头统一；
- 组框弱于主节点；
- 辅助说明弱于核心关系。

### 14.2 黑白论文风格

需要同时考虑：

- stroke pattern；
- fill tone；
- node shape/role；
- label；
- line style；

不能只把彩色图整体转灰度。

### 14.3 CJK

- 默认允许 xelatex/lualatex profile；
- 字体不打包进 Plugin；
- 字体选择由用户环境/项目约束决定；
- 缺少指定字体时使用明确 fallback；
- 不允许依赖开发机绝对字体路径。

---

## 15. QA Pipeline

### 15.1 技术 QA

必须检查：

- FigureSpec schema；
- Recipe capability；
- dependency；
- TeX compile；
- undefined references；
- missing library/package；
- shell escape；
- output existence；
- output page count；
- bounding box；
- requested physical size；
- manifest hash。

### 15.2 Source safety

外部 corpus item 在执行前至少检查：

- 禁止任意 `\\write18`；
- shell escape 默认关闭；
- 禁止访问 figure workdir 之外的任意文件；
- 禁止绝对路径；
- `\\input` / `\\include` 必须解析到允许的资源；
- 外部脚本/gnuplot 只允许明确 Recipe；
- 不执行未知社区样例附带的 shell/Python。

原始第三方 example **先 scan，再 compile**。

### 15.3 视觉 QA

编译成功不是完成。

至少检查：

- clipped content；
- text collision；
- edge crosses label；
- edge/arrow collision；
- group border collision；
- inconsistent alignment；
- poor whitespace；
- disproportionate arrowheads；
- text too small at target size；
- axis/tick/legend density；
- CJK line wrapping；
- unnecessary visual decoration。

### 15.4 Golden regression

Golden 不对 PDF binary 做脆弱 hash。

优先：

- generated TeX snapshot；
- FigureSpec hash；
- normalized manifest；
- compile success；
- rendered page geometry；
- optional perceptual/visual diff tolerance。

---

## 16. Plugin 分发

### 16.1 Canonical → generated

```text
packages/skill/
packages/skills/
src/
schemas/
recipes/
themes/
profiles/
knowledge/
examples/templates/ (selected)
        ↓
scripts/sync_plugin_package.sh
        ↓
packages/plugin/tikz-funfig/
```

### 16.2 Plugin 应包含

- general Skill；
- 5 specialized Skills；
- runtime；
- schema；
- recipes；
- themes；
- profiles；
- compiled cards；
- small verified examples；
- compact source-example corpus index；
- 允许分发且确实需要的 normalized example code；
- curated templates。

### 16.3 Plugin 不应包含

- `sources/` raw checkout；
- `references/legacy/`；
- 原始 manual PDF；
- 整个第三方 Git repo；
- 编译中间物；
- test output；
- font binary；
- 大量重复 preview；
- 开发机 cache；
- 未审计社区脚本。

### 16.4 Progressive loading

Skill 本身保持短。

专项 Skill 只负责：

- 任务识别；
- semantic extraction；
- Recipe/template selection；
- KB 查询；
- QA。

几千个 example 不写进 SKILL.md，而由 `tff kb search` 按需取回。

---

## 17. Source / License policy

本项目必须把 source provenance 当一等数据。

每个外部 item 至少保留：

- upstream URL；
- revision/tag；
- source path；
- source license；
- imported hash；
- transformation type；
- whether bundled in Plugin；
- attribution requirement。

### 17.1 PGF

当前本地 license 文件说明：

- PGF code：GPL-2.0 或 LPPL-1.3c；
- PGF documentation：GFDL-1.2 或 LPPL-1.3c。

因此：

- raw `doc/` 作为 upstream documentation 管理；
- 不删除 license；
- Plugin 是否携带具体抽取代码片段由 source policy 明确记录；
- 无法确认分发条件的内容宁可 `source-only`，不默认复制。

### 17.2 Community

社区仓库必须逐个 registry，不使用“GitHub 上公开 = 可以任意打包”的假设。

至少区分：

- source index only；
- code allowed in corpus；
- code allowed in distributed Plugin；
- attribution required；
- derivative allowed。

---

## 18. 评测集

没有 query benchmark，就不要引入 embedding。

建立 `tests/fixtures/kb-queries.json`，至少覆盖：

### 18.1 技术查询

- “matrix nodes”
- “fit background group”
- “curved arrow label”
- “confidence band”
- “fill between”
- “graph drawing layered”

### 18.2 中文自然语言

- “三层研究框架”
- “反馈箭头绕到外侧”
- “黑白期刊风格”
- “多个节点放进一个虚线组框”
- “双栏论文误差棒”
- “实验装置示意图”

### 18.3 目标指标

- expected family Top-3 recall；
- expected library/recipe Top-5 recall；
- source diversity；
- duplicate rate；
- average retrieved payload；
- retrieval latency；
- wrong-family rate。

只有数据证明 lexical retrieval 不够，才进入 hybrid/vector 阶段。

---

## 19. 施工阶段

本 Spec 确认后按以下顺序实施。

### M0 — Repository cleanup

目标：只整理职责，不改变绘图行为。

- 新增 `sources/`；
- 将 `doc/generic/pgf` 用 `git mv` 迁移到 official source；
- 建立 source registry；
- 整理 manual source manifest；
- 整理普通 demo；
- 更新 AGENTS/README/architecture；
- 确认 Plugin 不同步 raw sources。

验收：

- `git diff` 主要是 move + docs；
- 原测试全部通过；
- `packages/plugin` 内容无膨胀。

### M1 — PGF source importer

- 建立 corpus metadata schema；
- 解析 section/codeexample；
- 与官方 `extract.lua` 做抽取数量对照；
- 先覆盖重点主题；
- compile verification；
- 生成 `knowledge/corpus/examples.jsonl`。

验收：

- importer deterministic；
- source hash 可追踪；
- 代表性示例可独立编译；
- 无危险 shell behavior。

### M2 — Unified retrieval

- `tff kb search` 加入 example/template/recipe/golden metadata；
- alias normalization；
- weighted FTS；
- diversify；
- query benchmark。

验收：

- 中文/英文测试查询命中正确 family；
- 不需要加载 raw source；
- Plugin standalone search 可用。

### M3 — Template system

- 定义 template meta schema；
- edit contract；
- 从现有 Golden/高质量图提升第一批 template；
- template list/search/inspect；
- compile + visual review。

验收：

- 至少覆盖 plots/flowcharts/frameworks/relations/schematics；
- 每个 template 都有结构边界；
- 不是仅复制 `.tex`。

### M4 — PGFPlots Official Knowledge Stack

实施完成后的 PGFPlots 与 PGF/TikZ 使用相同四层知识模型，但 importer 针对 PGFPlots 文档结构优化，不机械复制 PGF 的 PDF 工作流。

#### M4a — Source provenance

- pinned PGFPlots 1.18.2 documentation source；
- source registry / revision / canonical tree hash / license；
- raw source 永不进入 portable Plugin。

#### M4b — Manual corpus

- 直接解析 `pgfplots.tex` 的 `include/input` 树；
- 建立 chapter / section / subsection / source-file / line provenance；
- 抽取 commands、`/pgfplots/` keys、libraries、topics；
- 生成 `knowledge/manual-index/pgfplots-1.18.2.jsonl`；
- 不经 PDF → text 反解析。

#### M4c — Source-example corpus

- 抽取官方 `codeexample`；
- safety classification；
- 恢复 PGFPlots library context；
- representative compile coverage；
- external-data / external-compute 样例保持 reference-only。

#### M4d — Curated knowledge

- 增加 PGFPlots cards + project-authored minimal compilable examples；
- Plot Recipes 通过 `knowledge_ids` 绑定稳定 card，而不是直接依赖 raw corpus example ID。

#### M4e — Paper-grade templates

- confidence band；
- asymmetric error bars；
- metadata scatter；
- grouped panels；
- 3D surface + colorbar；
- heatmap + colorbar。

模板必须来自 regression-backed FigureSpec/Golden，并带 edit contract。

#### M4f — Retrieval QA

- PGFPlots 中英文 aliases；
- benchmark 同时要求 card / template / recipe / official example / official manual 按任务合理出现；
- FTS5/BM25 继续作为默认检索器。

#### M4g — Distribution QA

- Plugin 只携带 normalized manual/example corpus、cards、templates；
- 不携带 raw PGFPlots source；
- standalone Plugin regression 必须在无 source checkout 时仍能检索 PGFPlots manual 并完成绘图。

### M5 — Community curated corpus

按顺序：

1. OpenTikZ；
2. janosh/diagrams；
3. PetarV-/TikZ。

每个 source 单独 license gate、import filter、quality gate。

### M6 — Visual QA hardening

- final-size preview；
- overlap/clipping heuristics；
- visual review checklist；
- Golden visual regression；
- CJK regression；
- single/double-column QA。

### M7 — Plugin hardening

- portable bundle size audit；
- standalone installation test；
- source checkout absent test；
- macOS clean-machine dependency test；
- release/version docs；
- Codex marketplace regression。

### M8 — Semantic retrieval only if justified

只有 M2 benchmark 证明 FTS 长尾不够才考虑：

- embeddings；
- hybrid retrieval；
- semantic reranker。

向量层永远不能替代：

- source provenance；
- exact command/library match；
- verification status；
- license metadata。

---

## 20. Definition of Done

整个重构完成的最低标准：

### Repository

- [ ] 顶层不再存在含义模糊的 raw `doc/`。
- [ ] external source 全部在 `sources/` 登记。
- [ ] runtime 不依赖 `sources/` / `references/`。
- [ ] generated Plugin 不手工维护。

### Knowledge

- [ ] PGF examples 可按 source/section/library/intent 检索。
- [ ] PGFPlots official corpus 可检索。
- [ ] corpus item 保留 source + license + hash。
- [ ] search 能区分 card/manual/example/template/golden/recipe。
- [ ] 有真实中英文 benchmark。

### Templates

- [ ] 每类核心论文图有成熟 template。
- [ ] template 有 edit contract。
- [ ] template 可在至少一个 publication profile 下编译和视觉通过。

### Product capability

- [ ] stable capability 都有 Recipe/Method/Golden/test。
- [ ] corpus 不能绕过 capability status。
- [ ] Expert TikZ 是受控 fallback，不是默认生成方式。

### QA

- [ ] compile success。
- [ ] final-size visual review。
- [ ] no clipping。
- [ ] no obvious overlap。
- [ ] CJK regression。
- [ ] monochrome regression。

### Plugin

- [ ] 单次安装获得全部 Skills。
- [ ] source checkout 不存在时仍可正常生成。
- [ ] Plugin 不携带 raw upstream repos。
- [ ] Plugin 可本地更新、验证、回滚。

---

## 21. 明确不做

本轮不做：

- 把模型“训练”在 TikZ 上；
- 建独立云服务；
- 建 MCP server；
- 为每种图新增一个 Skill；
- 一开始就上向量数据库；
- 把所有 GitHub TikZ 仓库全部 clone 进项目；
- 自动推断论文科学结论；
- 自动推断因果方向；
- 把 TikZ 当 CAD/EDA；
- 将 screenshot tracing 视为语义可靠来源；
- 用“编译成功”代替视觉 QA；
- 为了漂亮引入大量 icon、阴影、渐变、UI 风格。

---

## 22. 本轮确认项

开始施工前只需要确认下面 6 个架构决策：

1. **Raw source 统一迁移到 `sources/`**，当前 `doc/generic/pgf` 不保留顶层位置。
2. **四层知识模型**：Source → Corpus → Curated Template/Knowledge → Recipe/Golden。
3. **先做 PGF，再做 PGFPlots，再做社区库**。
4. **继续 FTS5，不预先引入向量库**。
5. **新增 `examples/templates/`，Template 使用 metadata + edit contract**。
6. **Plugin 只携带 normalized/curated 内容，不携带 raw upstream source**。

若这 6 项确认，施工从 M0 开始；每个阶段单独 commit，并在进入下一阶段前保持 `main` 可构建、可测试。

---

## 23. 推荐的最终产品定位

TIKZ-FunFig 的定位应写成：

> **A source-grounded, schema-driven academic figure system for TikZ and PGFPlots.**
>
> 用户用自然语言表达图形意图；系统结合官方源码知识、可检索实例、论文级模板、结构化 FigureSpec、稳定 Recipe 和最终尺寸视觉 QA，生成可复现、可编辑、可出版的矢量学术图。

这比“TikZ 代码生成 Skill”更准确，也更能指导未来的目录、知识、模板、测试和 Plugin 分发设计。
