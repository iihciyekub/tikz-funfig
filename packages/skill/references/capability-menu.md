# TIKZ-FunFig capability menu

Use this reference when the user asks what the Plugin can draw, asks how to start,
or invokes a FunFig Skill without a concrete figure request. Adapt the wording to
the user's language. The explicit Skill names below are optional: natural language
is sufficient, and the host can select the appropriate Skill.

**TIKZ-FunFig · 学术绘图助手**

欢迎使用 TIKZ-FunFig。

用文字描述、提供数据、附上草图或参考图片，或交给我现有的
TikZ/PGFPlots 源码。我可以制作可编辑的 LaTeX 矢量图和 PDF；需要时可输出 SVG。

## 核心能力

| 绘图类型 | 常见内容 | 可以这样说 | 可选的精确入口 |
| --- | --- | --- | --- |
| 社会科学与商学框架 | 理论框架、概念模型、中介/调节、分层研究模型、利益相关者/机制框架 | “把这些变量和假设关系整理成论文研究框架图” | `$funfig-frameworks` |
| 数学模型与关系图 | 变量关系、方程/对象关系、路径模型、概念关系 | “把这个数学模型和变量之间的关系画成论文图” | `$funfig-relations` |
| 数据与函数图 | 2D 函数曲线、数据序列、散点、误差棒、置信带、阈值与分区 | “根据这份数据画带单位和误差棒的图” | `$funfig-plots` |
| 学术多面板图 | 同类函数/数据图的 1×N、2×2 等对比排版 | “把四组结果排成 2×2 对比图” | `$funfig-plots` |
| 流程图 | 步骤、判断分支、汇合、反馈 | “把这些实验步骤画成流程图” | `$funfig-flowcharts` |
| 基础学术示意图 | 简单组件、机制、空间关系和说明标注 | “根据这张草图画成简洁的论文示意图” | `$funfig-schematics` |

直接描述你要画什么即可，不必先选择类型。也可以说“查看 TIKZ-FunFig
能力菜单”，随时再次查看这张表。

For an unclear or mixed figure, or to revise existing TikZ/PGFPlots source, the
user can describe the goal directly or invoke `$tikz-funfig`. An explicit Skill
invocation selects guidance; it is not a terminal command. Do not invent slash
commands. If a request goes beyond stable Recipe support, consult the relevant
knowledge and use sourced Expert Mode when warranted; do not promise formal
notation conformance or scientific facts absent from the user's material.

复杂生成几何、分形、铺砌、密集图网络和 3D 投影等已有实现属于**长尾/
实验性能力**，不作为默认产品边界，也不在普通请求中主动路由。只有用户
明确要求这类结构，或正在修改已经采用该管线的既有图时，才使用对应的
Expert/generative 路径。CAD/EDA、电路仿真、任意 3D 建模、动画、GIS 地图、
统计推断或数学证明不属于本插件的绘图能力边界。

Before giving a detailed or exhaustive capability answer, check the current
`capabilities` registry. Keep this overview focused on figure families, not a
static list of every Recipe. Ask for the content or source material needed to
draw only when the user's request has not already provided it.
