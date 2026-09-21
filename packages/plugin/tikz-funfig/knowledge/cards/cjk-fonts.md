# CJK text and fonts

For Chinese/Japanese/Korean text, use an engine and package configuration that actually supports CJK on the current machine. Prefer XeLaTeX for ordinary CJK diagrams; LuaLaTeX is required when Graph Drawing is used and its CJK configuration must be tested separately.

Never bundle local/proprietary font binaries. Resolve an available system font and record the engine decision.

Source: TIKZ-FunFig build experience. Example: `cjk-text`.
