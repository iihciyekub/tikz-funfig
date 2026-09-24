# Shared figure workflow

Use this workflow from any FunFig entrypoint. It is an agent workflow, not an
unimplemented automatic image-to-TikZ service. The runtime validates and renders
explicit specifications; the agent interprets context and makes design decisions.

## Understand the request

Extract the communication goal, supplied facts/data, figure family, task mode
(create/reproduce/redesign/revise/repair/migrate), reference roles, publication
width, language, and requested formats. Respect explicit instructions first, then
existing manuscript conventions, then suitable defaults. Keep content separate
from appearance; never infer missing data, causation, or a scientific mechanism.

For an image, read `reference-images.md`. For a new composition, read
`composition.md`. Infer ordinary aesthetic choices and proceed. Ask only when a
missing fact or conflicting reference would materially change the content or
requested fidelity. Do not require approval of every design record or layout.
A brief explanation of important assumptions is enough for routine choices.

Record the accepted intent and constraints in `figure.design.json` using
`design-contract.md`. Update this record alongside revisions. For existing figures,
read their source first and preserve IDs, data bindings, filenames, and location.
Older figures remain buildable without a design record; add one when adopting
this workflow, not by bulk-migrating unrelated work.

## Retrieve for the actual design problem

Check `capabilities` for stable support. Search/inspect relevant Templates, then
retrieve knowledge for missing layout or implementation details. Rewrite a long
user sentence into a few focused structural/technical queries; do not pass only
an unsegmented Chinese sentence to lexical search or interpret no hits as proof
TikZ cannot draw it. Example translations:

| User need | Useful separate queries |
| --- | --- |
| 三个输入汇合，再分成两个输出 | `flowchart branch merge`, `relative positioning` |
| 连线不要穿过文字 | `paths routing`, `edge labels quotes`, `diagram layout repair` |
| 像参考图一样有层次和分组 | `layered framework`, `fit groups`, `background layers` |
| 放大一个局部，同时保留全局 | `spy`, `coordinates calc` |
| 类似神经网络的模块图 | `encoder decoder architecture`, `pics components` |

Prefer a compatible stable Recipe/Template, compiled cards, then relevant official
source examples and manual sections. Inspect a small relevant set (often 2–5
examples); stop when the methods are sufficient. Reuse the technique and design
principle, not incidental coordinates or another figure's scientific claims.
Record useful knowledge IDs in the design. Source-extracted, source-compiled,
curated Template, and stable Recipe are different verification levels.

## Choose and implement

Use a supported Recipe when it preserves the requested meaning and composition.
Do not distort an apparatus or unusual diagram merely to fit rectangular nodes.
If a required feature is outside stable coverage, read `expert-mode.md`, ground
the implementation in shared knowledge, and use Expert TeX. Styling preference
alone does not require abandoning an adequate structured representation.

For a new structured figure, use `init --id <id> --recipe <recipe>` from the user
project or an explicit directory/project root. Replace starter content completely
with the user's real content; example numbers and labels are not evidence.
Create the design record, apply the chosen layout/theme/size in FigureSpec, then:

```text
validate-design <dir>/figure.design.json
validate <dir>/figure.funfig.json
build <dir>/figure.funfig.json
inspect <dir>/figure.funfig.json
```

These are arguments to the current Skill's `scripts/funfig.sh` wrapper. Design
fields describe intent and do not automatically change the renderer: implement
them in FigureSpec or TeX. Diagrams use 1.1 theme/profile fields. Existing 1.0 plot
Recipes have their own axis/style/canvas fields; do not add unsupported fields
or claim automatic Profile checking covers them.

## Review, repair, and deliver

Read `visual-review.md`, open the actual preview, compare it to the content and
reference requirements, and repair concrete defects. Rebuild and re-inspect after
changes; only mark QA after reviewing the current output. Use `qa <spec> pass
--note <observations>` or the Expert equivalent, then:

```text
validate-design <dir>/figure.design.json --delivery
```

This checks the design schema, expected files, structured ID/format agreement,
current build hashes, and recorded passing QA. It cannot judge image fidelity or
aesthetic quality on its own. Do not claim a pass unless both the checks and your
actual visual/content review succeed. If repair ceases to make progress, explain
the specific unresolved constraint instead of looping or declaring success.

Deliver the preview and links to editable source, design JSON, PDF, and requested
SVG. Briefly identify major design choices and any material limitation. Internal
Skill routing and compiler details need not burden the normal user interaction.
