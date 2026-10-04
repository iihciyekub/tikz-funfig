(function (root) {
  "use strict";
  const messages = {
    zh: {
      pageTitle: "TIKZ-FunFig 示例图库", gallery: "示例图库", github: "GitHub ↗",
      lede: "按永久 TFF 编号浏览示例。在提示词中引用编号，即可复用相应的布局与风格。",
      usageTitle: "怎么使用", usage: "选择一个示例，点击「复制提示词」，填写你的内容后发给 TIKZ-FunFig。自然语言即可，示例用于布局与风格，科研内容以你提供的材料为准。",
      meaning: "分层、分组和模块组织可参考框架图；变量路径、中介与调节假设可参考关系图。只有明确的步骤顺序、判断和分支才按流程图表达。",
      search: "搜索 TFF-0042、标题、类型、标签…", filter: "按示例类别筛选", controls: "图库筛选",
      all: "全部类别", example: "示例", generative: "生成式", golden: "回归用例", template: "模板",
      prompt: "示例提示词", copyId: "复制编号", copyPrompt: "复制提示词", copied: "已复制",
      copyFailed: "复制失败，请选择文字复制", source: "源码 ↗", origin: "原始来源 ↗",
      preview: "预览", empty: "没有匹配的示例。", failed: "图库加载失败：", language: "网站语言"
    },
    en: {
      pageTitle: "TIKZ-FunFig Gallery", gallery: "Example Gallery", github: "GitHub ↗",
      lede: "Browse examples by permanent TFF ID. Reference an ID in your prompt to reuse its layout and style.",
      usageTitle: "How to start", usage: "Choose an example, click Copy prompt, fill in your content, and send it to TIKZ-FunFig. Natural language is enough. Examples supply layout and style; your material supplies the scientific content.",
      meaning: "Use frameworks for layers, groups, and module organization; relations for variable paths, mediation, and moderation. Flowcharts represent explicit process order, decisions, and branch outcomes.",
      search: "Search TFF-0042, title, family, tags…", filter: "Filter by kind", controls: "Gallery controls",
      all: "All kinds", example: "Example", generative: "Generative", golden: "Golden", template: "Template",
      prompt: "Example prompt", copyId: "Copy ID", copyPrompt: "Copy prompt", copied: "Copied",
      copyFailed: "Copy failed; select the text to copy", source: "Source ↗", origin: "Origin ↗",
      preview: "preview", empty: "No examples match this search.", failed: "Gallery failed to load: ", language: "Website language"
    }
  };
  const pairs = {
    "3d":"三维", "antecedents":"前因", "bidirectional":"双向", "branch":"分支",
    "business":"商学", "business research":"商学研究", "capability":"能力", "chain mediation":"链式中介",
    "colorbar":"色标", "components":"组件", "concept network":"概念网络", "conceptual framework":"概念框架",
    "conceptual model":"概念模型", "confidence band":"置信带", "containment":"包含关系", "contour-plot":"等高线图",
    "converge":"汇聚", "converging outcome":"汇聚结果", "curved-edges":"曲线连接", "decision":"判断",
    "decorative":"装饰图", "direct effects":"直接效应", "directed-network":"有向网络", "edge-labels":"连线标签",
    "epc":"EPC", "error bars":"误差棒", "example":"示例", "experimental apparatus":"实验装置",
    "feedback":"反馈", "feedback-loop":"反馈回路", "flowchart":"流程图", "framework":"框架图",
    "framework-diagram":"框架图", "function-plot":"函数图", "generative":"生成式", "golden":"回归用例",
    "graph":"图网络", "grid":"网格", "grouped":"分组", "grouped framework":"分组框架",
    "groupplot":"多面板图", "heatmap":"热力图", "hypotheses":"假设模型", "implicit-function":"隐函数图",
    "input mechanism outcome":"输入—机制—结果", "interaction":"交互效应", "labelled edges":"带标签连线",
    "layered":"分层", "management":"管理学", "matrix":"矩阵", "maze":"迷宫", "mean curve":"均值曲线",
    "measurement":"测量", "mechanism":"机制", "mechanism-diagram":"机制示意图", "mediation":"中介效应",
    "mediator":"中介变量", "merge":"汇合", "mesh":"网格曲面", "moderation":"调节效应", "moderator":"调节变量",
    "multi panel":"多面板", "multiple predictors":"多自变量", "orthogonal routing":"正交连线",
    "orthogonal-routing":"正交连线", "outcome":"结果", "parallel inputs":"并行输入", "parallel modules":"并行模块",
    "path":"路径", "performance":"绩效", "petri-net":"Petri 网", "plot":"数据与函数图", "point meta":"点元数据",
    "process":"过程", "publication plot":"论文图", "publication-threshold":"论文阈值图", "quality control":"质量控制",
    "quiver-field":"向量场", "regression model":"回归模型", "relation":"关系图", "research framework":"研究框架",
    "resources":"资源", "retry":"重试", "retry-loop":"重试回路", "return loop":"返回回路", "routing":"连线路径",
    "scatter":"散点图", "schematic":"示意图", "scientific schematic":"科学示意图", "scientific-schematic":"科学示意图",
    "self loop":"自环", "serial mediation":"序列中介", "small multiples":"小多图", "social science":"社会科学",
    "split":"分流", "state-machine":"状态机", "strategy":"策略", "surface":"曲面", "template":"模板",
    "textbook":"教材图", "theory mechanism outcome":"理论—机制—结果", "threshold-region":"阈值区域",
    "uncertainty":"不确定性", "weighted-network":"加权网络", "weights":"权重", "yes no":"是／否",
    "surface-plot":"三维曲面图", "scatter-plot":"散点图", "error-bar":"误差棒", "confidence-band":"置信带"
  };
  const reverse = Object.fromEntries(Object.entries(pairs).map(([en, zh]) => [zh, en]));
  Object.assign(reverse, {"中介模型":"mediation model", "企业绩效":"business performance", "假设模型":"hypothesis model",
    "多前因":"multiple antecedents", "机制模型":"mechanism model", "理论框架":"theoretical framework",
    "研究模型":"research model", "组织能力":"organizational capabilities", "结果变量":"outcome variable", "路径模型":"path model"});

  const entriesZh = {
    "TFF-0001":["基础函数图", "二维函数曲线与论文坐标轴。"],
    "TFF-0003":["等高线图", "以等高线表达二维场的数值分布。"],
    "TFF-0004":["中文长标签框架图", "框架图中的中文长标签与自动换行。"],
    "TFF-0006":["可持续性阈值图：图 1", "带阈值标注的论文函数图。"],
    "TFF-0007":["可持续性阈值图：图 11", "带区域与阈值标注的论文函数图。"],
    "TFF-0008":["可持续性阈值图：图 4", "带阈值与交点标注的论文函数图。"],
    "TFF-0011":["斜向标签流程图", "流程连线上的倾斜标签与文字间距。"],
    "TFF-0014":["相交立方体的遮挡", "正交投影中，跨立方体边线的自动遮挡。"],
    "TFF-0015":["循环图拓扑", "用于参考图拓扑比较的循环图。"],
    "TFF-0016":["L 系统龙曲线", "由确定性 L 系统生成的龙曲线几何。"],
    "TFF-0017":["表达式参数曲线", "由参数表达式生成的曲线几何。"],
    "TFF-0018":["正六棱柱投影", "正六棱柱的正交投影与自动隐边分类。"],
    "TFF-0019":["立方体隐边", "立方体投影中的隐边几何。"],
    "TFF-0020":["点集与对偶结构", "由点集生成的对偶几何结构。"],
    "TFF-0021":["Truchet 弧线铺砌", "单一仿射网格上的确定性四分之一圆弧铺砌。"],
    "TFF-0024":["隐函数图", "隐函数的二维几何与坐标轴。"],
    "TFF-0025":["资源循环 Petri 网", "库所、变迁、有向弧与资源循环。"],
    "TFF-0026":["向量场", "二维向量场与箭头方向。"],
    "TFF-0029":["科学组件示意图", "组件布局、连接与科学标注。"],
    "TFF-0031":["机制示意图", "用组件和空间关系表达机制。"],
    "TFF-0032":["论文阈值图", "函数曲线、阈值与论文标注。"],
    "TFF-0033":["判断分支流程图", "紧凑流程中的单个判断、是／否分支与规则网格布局。"],
    "TFF-0034":["带外侧反馈的判断流程", "判断失败后沿外侧曲线返回前面的采集步骤。"],
    "TFF-0035":["多输入汇合后分流", "三个输入汇合到整合步骤，再分流到两个输出。"],
    "TFF-0036":["企业能力与绩效框架", "连接资源／环境、组织能力和绩效结果的三阶段框架。"],
    "TFF-0037":["输入与机制分组汇聚到结果", "两组模块连接共享结果，包含关系表达概念角色，不额外添加因果含义。"],
    "TFF-0038":["分层分组研究框架", "含背景节点与嵌套分组的输入—机制—结果框架。"],
    "TFF-0039":["多前因、机制与结果", "多个前因连接中心机制与结果的社会科学概念框架。"],
    "TFF-0040":["理论、机制与结果框架", "理论／背景驱动因素、机制与多个结果的三阶段框架。"],
    "TFF-0041":["均值曲线与置信带", "上下边界、填充不确定性区域与中心均值序列。"],
    "TFF-0042":["非对称误差棒", "将非对称横纵轴误差明确绑定到数据表列。"],
    "TFF-0043":["对齐的多面板图", "共享分组布局与边缘感知坐标轴标签的多面板论文图。"],
    "TFF-0044":["矩阵热力图与色标", "明确单元格元数据与定量色标的矩阵式热力图。"],
    "TFF-0045":["元数据驱动的散点图", "点元数据控制标记颜色，并显示定量色标。"],
    "TFF-0046":["三维曲面与色标", "函数或数据表驱动的三维曲面，包含视角与定量色标。"],
    "TFF-0047":["链式中介模型", "前因、中介一、中介二、结果的四阶段路径，可选择直接效应。"],
    "TFF-0048":["多个预测变量与一个结果", "多个用户提供的预测变量汇聚到同一结果的紧凑路径模型。"],
    "TFF-0049":["带标签的概念关系", "有向、双向、曲线、无向与自环关系组成的小型概念网络。"],
    "TFF-0050":["中介研究模型", "自变量—中介—结果模型，可选择直接路径。"],
    "TFF-0051":["调节研究模型", "调节变量指向 X 到 Y 的假设路径，而非构念节点。"],
    "TFF-0052":["实验组件管线", "组件、分组装置、注释与有方向的测量流程。"],
    "TFF-0053":["阈值区域图", "函数与阈值划分的区域。"],
    "TFF-0054":["加权曲线网络", "非规则加权图，曲线连接与独立连线标签清晰可读。"],
    "TFF-0055":["教材式有向图", "紧凑有向图，使用非对称加权连线并分开弯曲路径。"],
    "TFF-0056":["高亮解路径的迷宫", "迷宫墙线与起点到目标的解路径清晰分离。"],
    "TFF-0057":["EPC 查询与确认回路", "四状态 EPC 流程，条件明确、间距充足且反馈路径不重叠。"],
    "TFF-0058":["EPC 查询、收集与确认循环", "EPC 处理链，顶部重试路径与过程注释分离。"]
  };
  function text(key, language) { return (messages[language] || messages.zh)[key] || key; }
  function tag(value, language) { return (language === "en" ? reverse[value] : pairs[value]) || value; }
  function entry(item, language) {
    const local = language === "zh" && entriesZh[item.id];
    return { title: local ? local[0] : item.title, description: local ? local[1] : item.description || item.path };
  }
  const api = { text, tag, entry, entriesZh };
  root.FunFigGalleryI18n = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
