# TIKZ-FunFig 官方知识库与多 Skill Codex 插件 Spec

| 项目 | 内容 |
| --- | --- |
| 文档编号 | TFF-SPEC-001 |
| 文档版本 | 0.1 |
| 日期 | 2026-09-22 |
| 状态 | 待评审的实施规格；本文件不代表功能已经实现 |
| 产品 | TIKZ-FunFig，插件标识 `tikz-funfig` |
| 当前基线 | 仓库版本 0.8.4；HEAD `cd4fe7a`，另有既存未提交的 Schema/renderer 修改 |
| 首期目标 | 官方知识库、多个可发现 Skill、流程图/框架图/文本关系图稳定生成 |
| 后续目标 | 树与思维导图、状态模型、几何示意、自动布局 |

## 1. 产品决策

最终交付是一个可安装、更新的 **Codex 插件**。插件内部包含统一入口和多个专项 Skill，面向不同绘图需求；所有 Skill 共享同一套 FigureSpec、Recipe、运行时和编译产物契约。

用户安装一次插件，用自然语言描述需求，例如“画一张研究框架图，包含三个层次和两条反馈关系”。Codex 根据 Skill 描述选择相关工作流，读取必要知识，创建结构化图形，编译并检查结果。用户也可以显式选择某个专项 Skill。

这是一套按需读取的知识与工具系统，不涉及模型训练。增加 PDF 或 Skill 数量本身不等于增加稳定绘图能力；新增能力必须落实为可验证的语义、代码和案例。

### 1.1 职责分工

| 层次 | 职责 | 不承担的职责 |
| --- | --- | --- |
| Plugin | 安装、版本、分发、聚合全部 Skill 和运行时 | 不为每种图形另建一个插件 |
| 统一入口 Skill | 识别类型、处理模糊/混合需求、查能力边界、维护旧入口兼容 | 不强制拦截所有专项调用 |
| 专项 Skill | 解释领域语义、选择布局和 Recipe、读取知识、完成视觉检查 | 不复制维护一份渲染器 |
| 知识库 | 提供来源、语法、限制、最小示例和错误修复方法 | 不把未验证语法标成稳定支持 |
| FigureSpec | 保存图形内容、关系、布局约束与样式意图 | 不以生成的 TeX 作为长期编辑入口 |
| Recipe/Method | 定义图形类别及可复用语义 | 不为每次绘图创建一次性生成器 |
| Theme | 统一颜色、字体、线宽、间距、节点外观 | 不决定业务关系与箭头含义 |
| Runtime | 校验、依赖解析、确定性生成、编译和产物管理 | 不依赖开发机上的手册绝对路径 |

### 1.2 产品边界

- 首要宿主为具备文件和命令执行能力的本地 Codex；沿用现有 Git marketplace 分发身份。
- 初期使用 Skill + 本地 CLI 即可，不新增 MCP 服务、云端 API、向量数据库或账号体系。
- 输出以可编辑 FigureSpec、TeX、PDF 为主；预览图片按需生成。
- 流程图、框架图、关系图均为视觉表达，不从排版自动推断科学因果、统计结论或模型有效性。
- 动画、系统层开发、电路专用能力、交互式编辑器不属于首期。
- PGF/TikZ 的 Data Visualization 与 PGFPlots 分开索引；本手册不能替代 PGFPlots 官方手册。
- 不承诺所有 TikZ 语法都可由 FigureSpec 表达；已知但未实现的能力明确标记。

## 2. 基线与差距

以下来自本次仓库检查，而非新功能声明：

| 对象 | 当前行为 | 本项目需补充 |
| --- | --- | --- |
| `packages/skill/` | 单一 canonical Skill | 保留入口，新增专项 canonical 源 |
| `scripts/sync_plugin_package.sh` | 同步一个 Skill、runtime、schemas、recipes | 多 Skill 清单和受控共享资源同步 |
| `diagram.nodes` | `id/label/at/right_of/below_of/style` | 节点语义、四向定位、文本度量和统一布局 |
| `diagram.edges` | 端点、标签、style；renderer 主要使用 `--` | 锚点、折线、曲线、自环、标签位置 |
| `render_diagram` | 基础节点与箭头，固定加载一组库 | 分组、主题、按能力解析库依赖 |
| `engine.latex` | Schema 与 build 已允许 `lualatex` | Graph Drawing 的能力检测、自动引擎选择及对应 doctor 检查 |
| `src/funfig/schema.py` | 手写运行时校验，版本固定为 `1.0` | 与 JSON Schema 同步的新版本和语义校验 |
| Plugin | 根 `plugin.json` 与 `extensions.com.openai` | 沿用 portable 格式，验证多 Skill 可发现性 |

工作区在本次编写前已有 `schemas/figure-spec.schema.json` 和 `src/funfig/render.py` 修改。后续实现开始时重新检查并保留这些变更，不能将其当作本 Spec 已实现的能力，也不能覆盖或回退。

## 3. 用户场景与路由

### 3.1 专项技能清单

| Skill 标识 | 主要职责 | 边界 | 阶段 |
| --- | --- | --- | --- |
| `TIKZ-FunFig` | 现有入口兼容、需求分类、混合需求、修订与迁移入口 | 已明确类型可直接进入专项 Skill | 首期保留并收敛 |
| `funfig-plots` | 函数、数据、误差、曲面、阈值、多面板图 | 沿用 PGFPlots 家族，不接管概念网络 | 首期提取现有能力 |
| `funfig-flowcharts` | 步骤、判断、分支、合流、反馈流程 | 不宣称完整 BPMN/UML 标准支持 | 首期 |
| `funfig-frameworks` | 研究框架、机制模型、系统模块、分层与嵌套分组 | 用户提供含义；不自动添加科学因果关系 | 首期 |
| `funfig-relations` | 文本概念关系、标签网络、基础实体关系表达 | 精确 ER 记法待专项 Recipe 完成后开放 | 首期基础能力 |
| `funfig-trees-mindmaps` | 分类树、组织结构、思维导图 | 优先树/径向结构，不默认力导向 | 第二期 |
| `funfig-state-models` | 状态机、初始/终止状态、Petri 网 | 画图与模型验证明确区分 | 第二期 |
| `funfig-geometry` | 几何关系、角度、投影、交点、3D 示意 | 不替代 CAD 或科学求解器 | 第三期 |

首期插件应包含 **5 个实际可用 Skill**：1 个统一入口、1 个现有科学绘图专项、3 个新增专项。长期规划为 8 个 Skill；不得提前分发空壳 Skill 或宣称后续能力可用。现有大写入口名称作为兼容例外保留，新 Skill 使用小写连字符名称。

### 3.2 路由规则

1. 已有 `figure.funfig.json` 时，优先依据既有 Recipe 修订，保留 ID、数据及输出目录。
2. 用户显式选择专项 Skill 时优先使用；若请求超出其能力，简要指出并选择合适工作流。
3. 新图且类型明确时由匹配的专项 Skill 处理，无需先经过统一入口。
4. 只有“帮我画模型图”等确有歧义时，统一入口根据内容或一个必要问题区分图形类型。
5. “改成黑白”“字体放大”等仅涉及外观的需求，沿用原类型并修改主题/样式。
6. 混合请求按内容拆为可独立维护的图；首期不承诺把 PGFPlots 与 TikZ 框架自动组合进一个新画布。
7. 不为路由自动创建 Codex 任务或子代理；多个 Skill 是工作流组织方式，不是多代理架构。
8. 明确的文本、节点、连线和布局足够时直接绘制；只对影响语义的缺失信息提问。

### 3.3 路由验收样例

| 用户输入 | 预期工作流 | 核心行为 |
| --- | --- | --- |
| 画需求函数并标出两条曲线交点 | plots | 保持现有 Recipe/Method |
| 数据采集后判断质量，不通过则返回采集 | flowcharts | 判断节点、是/否标签、反馈路径 |
| 画输入层、机制层、结果层的研究框架 | frameworks | 分层模块、分组标题、明确方向 |
| A 与 B 相互关联，A 支持 C，用文字标在边上 | relations | 双向/有向边与关系标签 |
| 把当前图改成灰度期刊风格 | 当前专项 | 关系和数据不变，只改主题 |
| 画一个模型图 | 统一入口 | 根据上下文消歧，不盲选函数图 |
| 请写一份研究框架说明，不需要图 | 不激活绘图流程 | 不创建图形文件 |

### 3.4 Skill 文件契约

- 每个专项目录必须有 `SKILL.md`，frontmatter 包含与目录匹配的 `name` 和简洁、可区分的 `description`。
- `description` 说明适用任务与容易混淆的边界，不能全部写成“绘制任意科学图”。正文说明语义提取、Recipe 选择、资源入口和输出验证。
- 共享内容由第 6 节规则生成；专业领域说明留在本专项源目录。UI metadata 仅在有明确用途时增加 `agents/openai.yaml`。
- 默认允许自然语言匹配；不将专项 Skill 全部设为只能显式调用。宿主匹配是模型选择行为，路由表用于指导和评测，不宣称是确定性调度器。
- 每个 Skill 必须列出当前稳定 Recipe 与尚未支持的相关能力；新增 ER Recipe 后仍归 `funfig-relations`，无需增加第九个 Skill。
- 主入口保留生成、迁移、修复所需的共同约束，但将具体科学绘图细节移到 plots，避免同时维护两份完整教程。

## 4. 官方手册处理规范

### 4.1 固定来源

| 字段 | 值 |
| --- | --- |
| 本地输入 | `references/pgfmanual.pdf` |
| 来源 ID | `pgfmanual-3.1.11a` |
| 版本 | PGF/TikZ 3.1.11a |
| 页数 | 1323 |
| SHA-256 | `794c088249c4b3414b564b850a556c93787dff803e01af045bca7709919c9847` |
| 原始文档地位 | 不改写、不覆盖；本地溯源资料，不进入普通 Plugin 包 |

本节页码均为从 1 开始的 PDF 物理页序。已抽查页面的印刷页码与其一致；脚本仍需保存原 `page_label`，不能假定未来版本也相同。

### 4.2 一级分册

| ID | 输出文件名 | 原页码（含首尾） |
| --- | --- | --- |
| 00 | `00-frontmatter-introduction.pdf` | 1–29 |
| 01 | `01-tutorials-guidelines.pdf` | 30–101 |
| 02 | `02-installation-licenses-formats.pdf` | 102–122 |
| 03 | `03-core-syntax-paths-arrows.pdf` | 123–222 |
| 04 | `04-nodes-edges-pics.pdf` | 223–267 |
| 05 | `05-graphs-matrices-trees.pdf` | 268–341 |
| 06 | `06-plots-effects-transforms.pdf` | 342–380 |
| 07 | `07-animations.pdf` | 381–415 |
| 08 | `08-algorithmic-graph-drawing.pdf` | 416–563 |
| 09 | `09-libraries.pdf` | 564–852 |
| 10 | `10-data-visualization.pdf` | 853–974 |
| 11 | `11-utilities-math-engines.pdf` | 975–1071 |
| 12 | `12-pgf-basic-layer.pdf` | 1072–1232 |
| 13 | `13-pgf-system-layer.pdf` | 1233–1272 |
| 14 | `14-index.pdf` | 1273–1323 |

这 15 份必须连续覆盖原文全部页面，一级分册之间无遗漏、无重叠。第 11 册有意合并原 Part VII 与 VIII。

### 4.3 二级库分册与主题入口

一级目录保证完整性，二级目录服务查阅。为 Part V 建立全部库章节的标题、页范围、库名索引；首期实际输出以下重点节选：

| 库/主题 | 原页码 | 首要场景 |
| --- | --- | --- |
| automata | 572–576 | 状态转换储备 |
| backgrounds | 578–581 | 分组背景 |
| calc | 582 | 坐标计算入口；完整说明另链接 148–152 页 |
| chains | 601–607 | 流程链 |
| er | 668–669 | 实体关系储备 |
| fit | 685–687 | 模块分组 |
| matrix | 710–713 | 网格布局；基础说明另链接 319–331 页 |
| mindmap | 714–723 | 思维导图储备 |
| petri | 745–749 | Petri 网储备 |
| shapes | 786–832 | 几何形状与文本节点 |
| topaths | 840–844 | 连接路径 |
| trees | 846–848 | 树结构储备 |

`positioning`、`intersections` 等知识散布在核心章节，必须有跨章节主题索引，不能只遍历 Part V。二级节选与一级分册的重叠是预期行为，清单必须注明。

### 4.4 生成行为与产物

- 建议脚本：`scripts/build_manual_reference.py`；命令接口在实施时新增，本次尚不存在。
- 输入包括原 PDF 和版本化 `split-plan.json`。SHA、页数或预期章节标题不匹配时中止，不套用旧页码。
- 输出到 `output/pdf/pgfmanual-3.1.11a/`；PDF 保持仓库忽略状态。
- 原页面保持矢量、文本、页面框和图示；不以全页截图代替原 PDF。
- 分册内书签和内部跳转重映射。跨分册引用记录回原书/索引；无法重映射的链接应报告或移除失效目标，不声称全部超链接保持可用。
- 不在正文前插封面而改变源页映射；说明、版权来源及索引采用独立文件，原版权/许可页也有专门分册。
- 使用临时输出目录验证成功后发布生成结果；既有输出只在来源和配置匹配时可重建，原 PDF 永不作为输出目标。
- 同一输入及拆分计划应得到相同页面集合与清单内容；不要求含生成元数据的 PDF 字节完全相同。

### 4.5 来源清单契约

`references/manuals/pgfmanual-3.1.11a/` 保存可提交的 `source.json`、`split-plan.json`、`topics.json` 和简短来源说明。原 PDF 和渲染预览不提交。

| 字段 | 约束 |
| --- | --- |
| `source_id`, `version`, `sha256`, `page_count` | 固定标识并校验原文件 |
| `source_path` | 仓库相对路径，不记录用户机器绝对路径 |
| `parts[].id`, `filename` | 唯一、稳定，不以中文标题作为唯一 ID |
| `parts[].source_ranges` | 从 1 开始的闭区间；允许未来主题分册由多段组成 |
| `parts[].page_map` | 每一输出页对应原物理页、原页标签 |
| `parts[].outline` | 原标题、层级和新目标页 |
| `topics[]` | 中英文别名、库名、章节号、来源范围、知识卡片 ID |

包含输出校验和、实际生成时间、QA 状态的构建报告放在 `output/`，不混入稳定配置。

## 5. 可分发知识库

### 5.1 内容层级

1. **来源层**：原 PDF、书签、页码与章节记录，用于复核。
2. **任务知识层**：简明 Markdown 卡片，解释何时用、如何用、常见失败及适用边界。
3. **可执行示例层**：独立 `.tex`，有编译依赖和验证记录。
4. **稳定能力层**：FigureSpec + Recipe + runtime + golden 回归案例。

卡片来源引用可以指向原手册，但普通绘图不得要求打开该 PDF 才能运行。核心知识与例子应随插件提供。

### 5.2 卡片字段与内容

| 字段 | 含义 |
| --- | --- |
| `id`, `title`, `summary` | 稳定 ID、中文标题、用途 |
| `tags`, `aliases` | 中文任务词、英文术语、库名 |
| `sources` | source ID、章节号、原页范围；后补来源须独立登记 |
| `libraries`, `engines`, `external_tools` | 真实依赖与引擎限制 |
| `example_ids` | 指向包内示例，不能指向未分发的开发路径 |
| `capability_ids`, `recipe_ids` | 已接入能力的对应项；未接入则为空 |
| `verification` | 状态、验证引擎/版本、最近验证记录位置 |

正文必须包含使用条件、最小语法解释、可运行示例链接、可调整参数和已知限制。仅有 OCR/抽取文本不足以成为正式知识卡片。代码从 PDF 抽取后需人工/模型校对反斜杠、空格、括号及示例前置定义，并实际编译。

知识验证采用 `draft → reviewed → compiled`；能力支持另用 `reference-only / experimental / stable` 标记。`compiled` 只证明示例可编译，不能自动将对应能力标成 `stable`。稳定项必须满足第 11 节。

### 5.3 首期卡片范围

首期至少完成下列 24 个主题，避免以大量未经验证的全文切块替代可用内容：

| 分类 | 主题 ID |
| --- | --- |
| 语法基础 | `scopes-styles`, `coordinates-calc`, `paths-routing`, `arrows-meta`, `nodes-anchors`, `text-labels` |
| 布局与分组 | `relative-positioning`, `matrix-layout`, `chains-layout`, `fit-groups`, `background-layers`, `pics-components` |
| 图形与外观 | `flowchart-shapes`, `edge-labels-quotes`, `curved-edges`, `self-loops`, `themes-monochrome`, `themes-color` |
| 验证与复用 | `plain-text-escaping`, `cjk-fonts`, `library-dependencies`, `diagram-layout-repair`, `engine-selection`, `reusable-diagram-patterns` |

手册未完整覆盖的中文字体、转义策略、构建修复知识，应标记为项目经验或补充的官方来源，不能伪装成手册原文结论。

### 5.4 按需查阅

- Skill 先读取任务索引，再读取匹配的卡片和最近示例；不默认加载完整分册或全部知识库。
- 匹配优先使用稳定标签、中文别名、库名、能力 ID；首期采用文件与 JSON 索引即可。
- 常规任务目标为读取 1 个专项 Skill 和约 2–5 张卡片；复杂需求可增加，不能为了硬性数量限制遗漏必要知识。
- `references/legacy/` 和 root `references/manuals/` 均不进入运行时查找链。
- 暂不要求新的 `funfig search` 命令；只有文件检索确有不足时才新增 CLI。

## 6. Canonical 源与打包布局

### 6.1 源目录方案

```text
packages/
  skill/                         # 保留：现有统一入口 canonical 源
    SKILL.md
    scripts/                     # 现有通用 wrapper / 编译工具
    references/
      knowledge/                 # 新增：共享任务索引和知识卡片
      schema-contract.md
      style-guide.md
      ...
    templates/
    assets/knowledge-examples/   # 新增：可分发最小 TeX 示例
  skills/                        # 新增：专项 Skill canonical 源
    index.json                   # 显式打包清单及资源选择
    funfig-plots/SKILL.md
    funfig-flowcharts/SKILL.md
    funfig-frameworks/SKILL.md
    funfig-relations/SKILL.md
    ...                          # 仅在后续能力完成时加入
  plugin/tikz-funfig/             # 生成目标，禁止手工维护副本
references/manuals/              # 开发溯源清单；不分发
schemas/
recipes/
themes/                          # 新增：机器可读主题 canonical 源
src/funfig/
examples/golden/
```

此目录扩展正式实施时，先更新 `AGENTS.md`、开发文档和打包契约，声明 `packages/skills/`、`themes/` 的职责。共享知识仍位于现有 `packages/skill/` 源范围内。

### 6.2 插件分发布局

```text
tikz-funfig/
  plugin.json
  assets/
  skills/
    TIKZ-FunFig/
      SKILL.md
      references/
      scripts/
      assets/knowledge-examples/
    funfig-plots/
      SKILL.md
      references/shared/         # 自动物化所需共享资料
      scripts/funfig.sh           # 自动复制同一个 canonical wrapper
      assets/knowledge-examples/
    funfig-flowcharts/
    funfig-frameworks/
    funfig-relations/
  runtime/
    src/funfig/
    schemas/
    recipes/
    themes/
```

专项 Skill 自有的简短说明来自各自 canonical 目录；共享卡片、契约、wrapper 按清单生成到该 Skill 内，保持资源可发现和相对链接自包含。**分发副本允许重复，canonical 内容只维护一份。** 不使用依赖源码树的软链接，不要求另一个 Skill 先激活才能读取资源。

`packages/skills/index.json` 至少定义 `skill_id`、`source_dir`、`phase`、`recipe_ids`、`knowledge_ids`、`shared_files` 和 `example_ids`。目标路径由打包规则统一决定；引用不存在或目标重名时构建失败。

### 6.3 打包与兼容要求

- 扩展 `sync_plugin_package.sh`，保留现有主 Skill 同步，再从显式清单生成专项 Skill。
- 同步应移除清单中已撤销的生成 Skill，但只能删除本项目管理的生成目录。
- `sync_workspace_skill.sh` 需支持完整 Skill 集安装，并保留旧的单入口使用方式或清晰迁移选项。
- wrapper 必须在各个 Skill 相同目录深度下解析同一个 `runtime`；需在临时独立插件目录验证。
- runtime 路径解析新增 `themes` 时，源码布局与 portable 布局均必须可用。
- 保留根 `plugin.json` 的 portable 格式和 `extensions.com.openai`。目前不因旧 scaffold 偏好兼容格式而强行迁移现有 manifest。
- `.codex-plugin/plugin.json` 只有真实兼容目标需要时才增加，不作为本次多 Skill 功能的前置条件。
- 不新增空的 MCP/apps/hooks 配置；不改变 marketplace 或插件身份。
- 普通安装包不含原手册、分册 PDF、完整抽取文本、开发测试状态、字体文件或绝对用户路径。

## 7. FigureSpec 演进

### 7.1 版本与兼容策略

- 新结构化图能力目标使用 `schema_version: "1.1"`。这是计划中的版本，当前 runtime 尚不支持。
- 新 runtime 必须继续读取 `1.0`，保持现有 Recipe 的默认输出及 golden 快照，除非有单独说明的修复。
- `1.0` 的 `at/right_of/below_of/style` 与 TeX 标签语义保留；新字段不得悄悄改变旧图解释。
- `1.1` 新建图使用结构化字段；迁移工具不得凭空解释含任意 TeX 的旧 style。
- 未知字段、未知主题/Recipe、版本不支持和相互冲突的定位必须报具体字段错误，禁止静默忽略。
- 同时更新 JSON Schema 和 `src/funfig/schema.py`；不能只改 Schema 文件。
- Schema 版本与插件发布版本分开管理，不在本 Spec 中提前承诺某个发行版本号。

### 7.2 首期字段草案

以下是实施目标契约，落地时需通过 Schema 和示例收敛；禁止将本节 JSON 当作当前 0.8.4 已支持输入。

| 对象 | 字段 | 行为 |
| --- | --- | --- |
| 根 | `theme.id`, `theme.overrides` | 选择主题并做有限 token 覆盖 |
| `diagram.layout` | `type: manual/relative/grid` | 选择明确的布局策略 |
| `diagram.layout` | `row_gap`, `column_gap` | 正长度，如 `8mm`、`12mm` |
| `diagram.nodes[]` | `id`, `label`, `label_format` | 1.1 默认 `plain`；显式 `tex` 才按 TeX 解释 |
| 节点 | `role` | `process/decision/terminal/data/concept/module` 等 Recipe 允许的角色 |
| 节点 | `shape` | 首期 `rectangle/rounded-rectangle/diamond/ellipse/circle/parallelogram` |
| 节点 | `position` | 绝对坐标、相对位置、网格位置三选一 |
| 节点 | `text_width`, `min_width`, `min_height`, `align` | 正尺寸与 `left/center/right` 对齐 |
| 节点 | `appearance` | 结构化 fill/draw/text color/line width；不包含关系语义 |
| `diagram.edges[]` | `id`, `from`, `to` | ID 唯一，端点为真实节点 ID |
| 连线 | `from_anchor`, `to_anchor` | 首期 center/north/south/east/west 及四角 |
| 连线 | `route` | `straight/orthogonal/curve/loop` |
| 连线 | `arrows` | `none/forward/backward/both` |
| 连线 | `label`, `label_format`, `label_position`, `label_side` | 边标签、0–1 位置和左右侧/上下面向规则 |
| 连线 | `routing` | 正交方向顺序、曲线 bend、loop 方向，按 route 分支校验 |
| `diagram.groups[]` | `id`, `members`, `label`, `padding`, `appearance` | 成员为节点或子组；框与标题分开渲染 |

位置结构规则：

- `manual`：节点使用 `position: {type: "absolute", x: 0, y: 0}`，x/y 单位统一为 cm。
- `relative`：至少一个绝对定位根节点；其他节点使用 `{type: "relative", of: "node-id", direction: "right", gap: "12mm"}`，direction 支持四向及四个对角方向。
- `grid`：节点使用 `{type: "grid", row: 0, column: 0}`；行列是从 0 开始的非负整数，首期每格一个节点，不做跨格。
- 绝对坐标和相对定位可在 relative 模式组合；网格布局不混用其它定位模式。
- 首期不承诺自动避障。正交路线提供明确方向顺序，复杂回绕可通过用户指定布局或后续 waypoint 能力解决。

首期默认值与分支约定：

| 项目 | 1.1 新建图默认/约定 |
| --- | --- |
| 主题 | `academic-muted` |
| 节点角色与形状 | process/module 为 rounded-rectangle，decision 为 diamond，terminal 为 ellipse，data 为 parallelogram，concept 为 rectangle |
| 标签 | 节点及边默认 plain；align 默认为 center；换行符表示显式分行 |
| 连线 | route 默认为 straight；arrows 由 Recipe 定义：flowchart/framework 为 forward，relation 为 none |
| 标签位置 | `label_position` 默认 0.5；`label_side` 为 `above/below/left/right`，相对页面方向，不随箭头方向翻转；默认 above |
| 锚点 | 省略时由节点外边界求交；显式锚点覆盖自动选择 |
| 正交路由 | `routing.order` 为 `horizontal-first/vertical-first`，默认 horizontal-first，分别先水平/先垂直 |
| 曲线路由 | `routing.bend` 为带符号角度，正值对应 TikZ bend left，负值 bend right；curve 默认 25 度；0 使用 straight |
| 自环路由 | `routing.side` 为 `above/below/left/right`，默认 above |
| 分组 | 首期边端点仍只引用节点；组只管理视觉包含与标题，padding 由主题提供 |

必须将这些默认值写入 Recipe/主题/Schema 文档并保持运行时一致。这里的默认仅适用于 1.1 新图，不回溯改变 1.0 行为。

### 7.3 完整示意输入

下面示例用于说明目标契约，**尚不能用当前 runtime 直接构建**：

```json
{
  "schema_version": "1.1",
  "id": "data-quality-flow",
  "recipe": "flowchart",
  "kind": "tikz",
  "theme": {"id": "academic-muted"},
  "diagram": {
    "layout": {"type": "relative"},
    "nodes": [
      {
        "id": "collect",
        "label": "采集数据",
        "label_format": "plain",
        "role": "process",
        "position": {"type": "absolute", "x": 0, "y": 0}
      },
      {
        "id": "check",
        "label": "质量合格？",
        "role": "decision",
        "text_width": "22mm",
        "position": {"type": "relative", "of": "collect", "direction": "right", "gap": "16mm"}
      },
      {
        "id": "analyze",
        "label": "分析数据",
        "role": "process",
        "position": {"type": "relative", "of": "check", "direction": "right", "gap": "16mm"}
      }
    ],
    "edges": [
      {"id": "e1", "from": "collect", "to": "check", "route": "straight", "arrows": "forward"},
      {"id": "e2", "from": "check", "to": "analyze", "route": "straight", "arrows": "forward", "label": "是"},
      {
        "id": "e3",
        "from": "check",
        "to": "collect",
        "from_anchor": "south",
        "to_anchor": "south",
        "route": "curve",
        "routing": {"bend": 35},
        "arrows": "forward",
        "label": "否"
      }
    ]
  },
  "outputs": {"basename": "figure", "keep_build": false}
}
```

### 7.4 语义校验

- 节点、组、边使用可稳定引用的 ID；节点与组的命名空间不得冲突。
- 边端点、相对定位目标、分组成员必须存在；错误报告包含 JSON 字段路径。
- 相对定位依赖和组包含关系不能成环，renderer 先排序再输出，不依赖输入数组碰巧正确。
- 图的业务连线允许循环；不能把反馈边误判为定位依赖循环。
- 一个节点/子组至多有一个直接父组，嵌套组允许；首期不实现交叠式多重归属。
- `loop` 要求 from=to；其它自连接须显式选择 loop。
- 正交路由、bend、loop 参数分别适用；无效组合不能传到 TeX 才失败。
- 稳定 Recipe 只接受有意义的 role，显式 shape 可覆盖 role 默认形状而不改变 role。
- `plain` 模式转义 TeX 特殊字符并定义换行处理；`tex` 保留用户数学表达式。旧版本标签不自动转义。

## 8. Recipe、主题和引擎

### 8.1 Recipe 计划

| 阶段 | Recipe | 主能力 |
| --- | --- | --- |
| 现有保留 | 所有现有 plots Recipe、`mechanism-diagram` | 兼容旧图 |
| 首期 | `flowchart` | 步骤/判断/分支/反馈 |
| 首期 | `framework-diagram` | 层次模块、分组、带标签关系 |
| 首期 | `relation-diagram` | 概念节点、多种连线与标签 |
| 第二期 | `tree-diagram`, `mindmap` | 树与径向层级 |
| 第二期 | `state-machine`, `petri-net`, `entity-relationship` | 专项记法与角色 |
| 第三期 | 几何类及自动布局 Recipe | 经案例验证后确定粒度 |

多个 Recipe 可共用 diagram renderer 和 Method，不为每个 Skill 创建独立渲染实现。Recipe 能力注册应支持查询布局、库、引擎需求和稳定状态，供 Skill 路由使用。

### 8.2 主题

首期提供 `journal-monochrome`、`academic-muted`、`presentation-color` 三个主题。紧凑排版作为后续 density 选项，不先扩展为独立 Skill。

优先级为：显式元素 appearance > 显式主题 token 覆盖 > 主题 role 样式 > Recipe 默认 > 系统默认。切换主题不得增删节点、修改数据、改变箭头方向或关系标签。

主题采用有限 token，如字体大小、节点内边距、基础线宽、边色、节点填充色和文本色。字体使用可用字体选择规则，不写死开发机绝对路径，不分发字体二进制。首期主题只覆盖新 diagram Recipe；现有 PGFPlots 风格保持，后续单独统一。

### 8.3 库依赖与引擎

- 从实际功能计算 `usetikzlibrary` 集合，稳定排序和去重。
- 普通基础图可使用 pdfLaTeX；中文默认按现有规则使用 XeLaTeX，并增加真正可用的 CJK 字体配置。
- 启用 Graph Drawing 的图要求 LuaLaTeX；中文 Graph Drawing 需要另行验证 LuaTeX 下的 CJK 配置，不能复用 XeLaTeX 专属配置。
- 用户显式选择不兼容引擎时给出准确错误与可行选项，不悄悄换引擎。
- `doctor(spec)` 检查实际所需引擎及工具；不因为只画流程图就新增 gnuplot 要求。
- Graph Drawing 本身不等于需要 shell escape；维持既有按已检查源码及计算能力决定 shell escape 的策略。
- 所有布局带随机因素时，必须记录并固定 seed；即便如此，也不承诺跨 TeX/库版本 PDF 字节一致。

## 9. 交付与失败处理

继续采用已有图形目录契约：

```text
<project>/figures/<figure-id>/
  figure.funfig.json
  figure.tex
  figure.pdf
  data/                  # 如有
  .funfig/
    manifest.json
    build/               # 成功后按既有策略清理
```

用户指定目录优先，其次原图目录，最后项目默认目录。不得输出到插件安装缓存。预览图片按需生成，开发回归预览不得提交 Git。

Manifest 在既有字段基础上记录解析后的库集合、引擎、主题 ID/版本与内容哈希、布局 seed（如有）。知识来源以 recipe/card ID 可追溯；不要求把模型读取过的全部资料塞入用户 FigureSpec。

错误分为输入语义错误、能力未支持、依赖缺失、TeX 编译错误和视觉质量问题。校验失败不覆盖上一次成功的 TeX/PDF；编译失败保留可诊断日志，明确新 PDF 未成功生成，不能把旧 PDF 当作本次成功结果。

普通终端用户提出未支持能力时，可以查找现有可用表达方式或明确边界；不自动修改已安装插件代码。在本仓库开发任务中，才按能力开发流程扩展 Schema/Recipe/runtime。

## 10. 分期实施与任务依赖

### M0：契约与目录基础

- [ ] 确认本 Spec，更新源目录责任文档，保留旧入口。
- [ ] 增加多 Skill 打包清单规范与共享资源映射。
- [ ] 定义 1.0/1.1 兼容策略和 capabilities 状态。
- 完成条件：目录与迁移责任明确，现有能力未被改写。

### M1：手册分册与溯源索引

- [ ] 固定原 PDF SHA、页数、目录与页标签。
- [ ] 实现拆分脚本、15 个一级分册、12 个重点库节选。
- [ ] 建立完整 Part V 库索引和跨章节主题索引。
- [ ] 校验每个分册首尾页、页数、书签和跨册链接报告。
- 完成条件：读者和后续代理均能从任务词定位到准确原文。

### M2：首期知识与独立示例

- [ ] 完成第 5.3 节的 24 张知识卡片。
- [ ] 每张语法卡片有可编译示例；综合修复类卡片可引用共享案例。
- [ ] 来源与验证状态分离，给出 card → source → example 映射。
- 完成条件：不存在只有转录文本、没有验证的“稳定知识”。

### M3：结构化图内核

- [ ] 实现 1.1 Schema 和运行时校验，保留 1.0 处理分支。
- [ ] 实现节点、相对/网格布局、连线路由与标签、分组、主题。
- [ ] 实现库解析、引擎依赖和中文文本构建。
- [ ] 新增三类首期 Recipe 和 golden 案例。
- 完成条件：脱离 Skill，自身 CLI 也能验证、生成并编译首期用例。

### M4：多 Skill 集成与首期可发布包

- [ ] 收敛统一入口，提取 plots Skill，新增三类专项 Skill。
- [ ] 同步 portable 包和 workspace 安装路径；检查共享资源闭包。
- [ ] 在不包含原仓库/手册的临时目录构建每个专项案例。
- [ ] 在 Codex 中验证显式选择、自然语言匹配与后续修订。
- [ ] 运行仓库全检查，更新 CHANGELOG，再走既有发布流程。
- 完成条件：一个插件安装后可发现 5 个可用 Skill；通过全部首期验收。

### M5：第二期图形家族

树、思维导图、状态机、Petri 网和正式 ER 记法逐项推进，每项独立补齐 Schema、Recipe、知识卡片和 golden。新增对应专项 Skill 时再加入安装包。

### M6：第三期高级能力

评估自动分层/力导向布局、几何与投影、复杂连接避障；只有真实用例证明需要时才引入更复杂的布局机制。补充 PGFPlots 官方手册属于独立来源接入，复用 M1/M2 流程。

依赖顺序：M0 → M1 → M2；M3 在相关知识示例验证后推进；M4 依赖 M2/M3。M5/M6 不阻塞首期交付。不在缺乏实际试点数据时承诺工期。

## 11. 验收矩阵

| ID | 验收项 | 可检查的通过条件 |
| --- | --- | --- |
| KB-01 | 来源固定 | SHA、版本、1323 页与源清单一致；错误源被拒绝 |
| KB-02 | 一级完整性 | 15 册页面集合恰好覆盖 1–1323，各页出现一次 |
| KB-03 | 分册保真 | 每册首尾页及代表性公式/图示渲染检查通过；页面框一致 |
| KB-04 | 二级节选 | 12 个重点节选范围准确，全部库有索引 |
| KB-05 | 可追溯 | 每张正式卡片的来源、示例和状态均可解析 |
| KB-06 | 小上下文使用 | 典型任务可只靠索引、相关卡片和示例完成，不加载整本手册 |
| SK-01 | Skill 发现 | 首期 5 个 Skill 出现在实际宿主发现结果中，无空壳后续 Skill |
| SK-02 | 路由 | 第 3.3 节每类至少 3 个表达变体；图形类正确匹配，纯文字请求不创建图 |
| SK-03 | 修订 | 修改文字/主题/关系时修订已有 FigureSpec，不复制出无关图目录 |
| RT-01 | 兼容 | 所有既有 golden 与既有测试通过，旧输入默认行为未意外改变 |
| RT-02 | 语义 | 缺失引用、重复 ID、定位环、组包含环、无效参数在编译前报错 |
| RT-03 | 确定性 | 固定输入、依赖版本和主题得到相同 TeX；依赖列表顺序稳定 |
| RT-04 | 能力真实 | 三个新 Recipe 均可用 CLI 独立构建，知识状态不越级 |
| RT-05 | 主题 | 三主题切换后，节点 ID、边端点、标签与业务内容保持一致 |
| QA-01 | 视觉 | 目标排版尺寸下无缺字、截断、意外覆盖、错误方向或不可读标签 |
| QA-02 | 长文本 | 中英文长标签、特殊字符、数学标签与多行文本正常 |
| PK-01 | 可移植 | 复制生成插件到临时目录，原仓库/原 PDF 不可用时各专项仍能绘图 |
| PK-02 | 副本一致 | 清单中 canonical 内容与生成副本一致；相对引用不存在越界或缺失 |
| PK-03 | 包内容 | 无手册 PDF、legacy、字体、构建缓存、开发机绝对路径 |
| PK-04 | 更新 | 更新后旧图仍可打开构建，被撤销的生成 Skill 不残留 |

### 11.1 首期 golden 场景

| 案例 | 主要验证内容 |
| --- | --- |
| `flowchart-decision` | 判断节点、是/否分支、合流 |
| `flowchart-feedback` | 反馈方向、曲线路径、标签可读 |
| `framework-grouped` | 分组框、标题、背景层、包含关系 |
| `framework-layered` | 三层模块、网格间距、跨层连接 |
| `relations-labelled` | 有向/无向/双向关系、边标签、不同路由 |
| `diagram-longtext-cjk` | 中文与英文长文本、多行、数学内容、特殊字符 |

每个案例保存自包含 FigureSpec 与确定性 `.tex` 快照；必要数据随例提供。至少对一个语义相同的案例构建全部三主题，验证主题切换不改变关系。PDF/PNG 作为本地 QA 产物，不提交。

### 11.2 检查分层

1. 单元/语义检查：真正可失败的输入不变量，避免仅断言文档措辞。
2. TeX 快照：校验生成行为与兼容性。
3. 编译检查：验证引擎、库、字体配置及产物。
4. 视觉检查：查看真实预览；编译成功不能替代布局质量。
5. Plugin 端到端检查：验证发现、按需读取、离线资源和修订流程。

自动几何检测可以辅助报告节点重叠/边穿框，但首期不宣称具有通用自动审美或避障能力。

## 12. 开发、版本与发布要求

- 每个能力遵守 `AGENTS.md`：Schema → renderer/Recipe/Method → golden → regression → canonical Skill/docs → 同步 portable 包。
- 新知识的 `.tex` 示例在纳入 golden 前区分“语法例子”和“产品输入输出”，不要把任意官方示例直接当作 Recipe 已支持。
- 修改生成目标必须由 `./scripts/sync_plugin_package.sh` 完成。
- 行为/打包变更完成后运行 `./scripts/check.sh` 与 `git diff --check`。
- 纯 Spec 编辑做文档和链接检查即可，不将其描述为实现验收通过。
- 插件发布沿用 `docs/RELEASE.md` 和 `scripts/release.sh`，要求干净树、CHANGELOG、检查通过和规定 tag/push 流程。
- Skill、runtime、主题及知识清单随一个 Plugin 版本整体发布；manifest、能力索引和实际内容保持一致。
- 本 Spec 编写任务不自动触发实现、安装、发布或对现有未提交改动的处理。

## 13. 主要风险与决策

| 问题 | 决策 |
| --- | --- |
| 分 PDF 后仍难查 | 增加任务索引与知识卡片，原 PDF 仅用于复核 |
| Skill 大量重叠 | 按图形任务划分；主题独立；统一入口只处理必要路由 |
| 知识与执行能力不一致 | 分开跟踪文档验证状态和 runtime 支持状态 |
| 通用 diagram Schema 过早膨胀 | 首期只实现六个案例证明需要的字段 |
| 任意 raw TeX 绕过结构化模型 | 保留旧兼容，不把 raw TeX 当作新能力默认方案 |
| 多 Skill 共享文件引用不可靠 | 分发时按清单物化共享资源，独立包端到端验证 |
| 手册升级页码漂移 | 版本与 SHA 固定，不覆盖旧清单；新版本重新生成映射 |
| 原文示例和解释转录失真 | 来源复核、编译和视觉检查；记录修改说明与原来源 |
| 中文图缺字/编译失败 | 根据实际引擎选择可用字体和 CJK 配置，加入回归 |
| 自动布局结果变化 | 后置引入，固定 seed 和依赖记录，明确可重复性的范围 |

首期已经确定：一个插件、多 Skill、共用运行时、轻量知识随包、PDF 留在本地、保留 1.0、新增 1.1、优先三类结构图。没有阻塞编写首期代码的产品问题；具体字段以本契约为起点，在 golden 实现时通过明确的文档修订收敛。

## 14. 依据与阅读入口

### 14.1 仓库依据

- [仓库规则](../../AGENTS.md)
- [当前架构](../architecture.md)
- [开发流程](../DEVELOPMENT.md)
- [Plugin 分发契约](../PLUGIN_DISTRIBUTION.md)
- [安装更新](../INSTALL_UPDATE.md)
- [发布规则](../RELEASE.md)
- [当前 FigureSpec Schema](../../schemas/figure-spec.schema.json)
- [当前 canonical Skill](../../packages/skill/SKILL.md)
- [当前 diagram renderer](../../src/funfig/render.py)
- [当前运行时校验](../../src/funfig/schema.py)
- [当前打包脚本](../../scripts/sync_plugin_package.sh)

### 14.2 官方文档核实

核实日期：2026-09-22。下面只约束宿主打包与 Skill 机制；本文的 Skill 名称、字段、阶段和目录扩展属于 TIKZ-FunFig 的产品设计。

- [OpenAI Plugin architecture](https://developers.openai.com/plugins/concepts/plugins)：支持在一个可安装插件内聚合多个相关 Skill；MCP 可选。
- [OpenAI Package your plugin](https://developers.openai.com/plugins/build/plugins)：portable 根 manifest、`skills/` 与 OpenAI 扩展元数据布局。
- [OpenAI Build skills](https://learn.chatgpt.com/docs/build-skills)：Skill 通过名称/描述发现，正文和资源按需读取，支持显式与隐式匹配。
- 本地 PGF/TikZ 3.1.11a：本文件第 4 节登记了完整来源和哈希；节点见第 17 章，图结构见第 19 章，自动布局引擎要求见第 28 章（421 页）。

官方文档支持现有 portable 格式。部分本地 scaffold 工具使用 `.codex-plugin/plugin.json` 兼容格式；本项目沿用已存在且获官方支持的根 manifest，不为统一脚手架外观而迁移。
