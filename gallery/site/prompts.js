(function (root) {
  "use strict";

  function contentHint(item, language) {
    const family = item.family || "";
    if (language === "en") {
      if (family === "flowchart") return "[Provide ordered steps, decision conditions, and branch destinations]";
      if (["framework", "framework-diagram"].includes(family)) return "[Provide layers, groups, modules, and explicit connections; describe any variable paths, mediation, or moderation hypotheses]";
      if (["relation", "relation-diagram"].includes(family)) return "[Provide variables or mathematical objects, relationship directions and labels; identify the path each moderator affects]";
      if (["schematic", "scientific-schematic", "mechanism-diagram"].includes(family)) return "[Provide components, interfaces, spatial relationships, and known dimensions]";
      if (family === "petri-net") return "[Provide places, transitions, directed arcs, weights, and initial marking]";
      if (["plot", "function-plot", "error-bar", "scatter-plot", "confidence-band", "groupplot", "publication-threshold", "threshold-region", "implicit-function", "surface-plot", "contour-plot", "heatmap", "quiver-field"].includes(family)) return "[Provide functions or data files, axes and units; define uncertainty without inferring data from the example]";
      return "[Provide the content, objects, relationships, and meaningful geometric constraints]";
    }
    if (family === "flowchart") return "[填写有顺序的步骤、判断条件和各分支去向]";
    if (["framework", "framework-diagram"].includes(family)) {
      return "[填写层级、分组、各组模块和明确的连接；变量路径、中介或调节模型请按实际假设说明]";
    }
    if (["relation", "relation-diagram"].includes(family)) {
      return "[填写变量或数学对象、关系方向和标签；若有调节变量，说明它调节哪条路径]";
    }
    if (["schematic", "scientific-schematic", "mechanism-diagram"].includes(family)) {
      return "[填写组件、接口、空间关系和已知尺寸；不要补出未提供的结构]";
    }
    if (family === "petri-net") return "[填写库所、变迁、有向弧、权重和初始标识]";
    if (["plot", "function-plot", "error-bar", "scatter-plot", "confidence-band",
      "groupplot", "publication-threshold", "threshold-region", "implicit-function",
      "surface-plot", "contour-plot", "heatmap", "quiver-field"].includes(family)) {
      return "[提供函数或数据文件、坐标轴与单位；误差范围请说明定义，不从示例推断数据]";
    }
    return "[填写要表达的内容、对象及关系；保留有意义的几何约束]";
  }

  function promptFor(item, language) {
    if (language === "en") {
      return "Use the layout and LaTeX style of " + item.id + " to create an editable paper figure with my content:\n"
        + contentHint(item, "en") + "\n"
        + "The example supplies layout and style only; use my facts, labels, data, and relationships.\n"
        + "Label language: [Chinese or English]; target width: [journal column width].\n"
        + "Complete the figure and checks, and deliver editable source and PDF. [Specify SVG here if needed]";
    }
    return "参考 " + item.id + " 的布局与 LaTeX 风格，用我的内容制作可编辑的论文图：\n"
      + contentHint(item) + "\n"
      + "示例只作布局和风格参考；使用我的事实、标签、数据和关系。\n"
      + "文字语言：[中文或英文]；目标宽度：[期刊栏宽]。\n"
      + "请完成绘图与检查，交付可编辑源码和 PDF。[需要 SVG 时在这里说明]";
  }

  const api = { promptFor: promptFor };
  root.FunFigGalleryPrompts = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(globalThis);
