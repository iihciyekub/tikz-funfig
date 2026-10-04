"use strict";

const state = { entries: [], all: [], query: "", kind: "", language: "zh", error: "" };
const grid = document.querySelector("#grid");
const search = document.querySelector("#search");
const kind = document.querySelector("#kind");
const count = document.querySelector("#count");
const empty = document.querySelector("#empty");
const template = document.querySelector("#card-template");
const i18n = FunFigGalleryI18n;
const text = key => i18n.text(key, state.language);
const promptFor = item => FunFigGalleryPrompts.promptFor(item, state.language);

function haystack(item) {
  const zh = i18n.entry(item, "zh");
  const tags = item.tags || [];
  return [item.id, item.title, item.family, item.kind, item.description, zh.title, zh.description,
    i18n.tag(item.family, "zh"), ...tags, ...tags.map(t => i18n.tag(t, "zh")),
    ...tags.map(t => i18n.tag(t, "en")), ...(item.aliases || [])].join(" ").toLowerCase();
}

function copy(value, button) {
  const old = button.textContent;
  navigator.clipboard.writeText(value).then(() => {
    button.textContent = text("copied");
    setTimeout(() => { button.textContent = old; }, 900);
  }).catch(() => { button.textContent = text("copyFailed"); });
}

function card(item) {
  const node = template.content.firstElementChild.cloneNode(true);
  const local = i18n.entry(item, state.language);
  node.id = item.id;
  node.dataset.kind = item.kind;
  const image = node.querySelector(".preview");
  image.src = item.preview;
  image.alt = local.title + " " + text("preview");
  node.querySelector(".preview-link").href = item.preview;
  node.querySelector(".tff-id").textContent = item.id;
  node.querySelector(".kind").textContent = text(item.kind) + (item.family ? " · " + i18n.tag(item.family, state.language) : "");
  node.querySelector(".title").textContent = local.title;
  node.querySelector(".description").textContent = local.description;
  const tags = node.querySelector(".tags");
  [...new Set((item.tags || []).map(value => i18n.tag(value, state.language)))].slice(0, 7).forEach(value => {
    const span = document.createElement("span");
    span.className = "tag";
    span.textContent = value;
    tags.appendChild(span);
  });
  const copyId = node.querySelector(".copy-id");
  copyId.textContent = text("copyId");
  copyId.addEventListener("click", e => copy(item.id, e.currentTarget));
  node.querySelector(".prompt-example summary").textContent = text("prompt");
  node.querySelector(".prompt-text").textContent = promptFor(item);
  const copyPrompt = node.querySelector(".copy-prompt");
  copyPrompt.textContent = text("copyPrompt");
  copyPrompt.addEventListener("click", e => copy(promptFor(item), e.currentTarget));
  const source = node.querySelector(".source");
  source.href = item.source_url;
  source.textContent = text("source");
  const origin = node.querySelector(".origin");
  origin.textContent = text("origin");
  if (item.origin_url) {
    origin.href = item.origin_url;
    origin.hidden = false;
    origin.title = [item.attribution, item.license].filter(Boolean).join(" · ");
  }
  return node;
}

function render(scrollToTarget = false) {
  const q = state.query.trim().toLowerCase();
  const rows = state.entries.filter(item => (!state.kind || item.kind === state.kind) && (!q || haystack(item).includes(q)));
  grid.replaceChildren(...rows.map(card));
  count.textContent = rows.length + " / " + state.entries.length;
  empty.hidden = rows.length !== 0 && !state.error;
  empty.textContent = state.error ? text("failed") + state.error : text("empty");
  const target = document.getElementById(location.hash.slice(1).toUpperCase());
  if (target && grid.contains(target)) {
    target.classList.add("target");
    if (scrollToTarget) target.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

function setLanguage(language, persist = false) {
  state.language = language === "en" ? "en" : "zh";
  if (persist) {
    try { localStorage.setItem("funfig-gallery-language", state.language); } catch (_) { /* Storage may be unavailable. */ }
  }
  document.documentElement.lang = state.language === "zh" ? "zh-CN" : "en";
  document.title = text("pageTitle");
  document.querySelectorAll("[data-i18n]").forEach(node => { node.textContent = text(node.dataset.i18n); });
  document.querySelector(".language-switch").setAttribute("aria-label", text("language"));
  document.querySelector(".usage").setAttribute("aria-label", text("usageTitle"));
  document.querySelector(".controls").setAttribute("aria-label", text("controls"));
  search.placeholder = text("search");
  search.setAttribute("aria-label", text("search"));
  kind.setAttribute("aria-label", text("filter"));
  [...kind.options].forEach(option => { option.textContent = text(option.value || "all"); });
  document.querySelectorAll("[data-language]").forEach(button => {
    button.setAttribute("aria-pressed", String(button.dataset.language === state.language));
  });
  render();
}

function applyHashFilter() {
  const hash = location.hash.slice(1).toUpperCase();
  const alias = state.all.find(item => item.id === hash && item.canonical_id);
  if (alias) {
    location.replace("#" + alias.canonical_id);
    search.value = alias.canonical_id;
  } else if (/^TFF-\d+$/.test(hash)) {
    search.value = hash;
  }
  state.query = search.value;
  render(true);
}

search.addEventListener("input", () => { state.query = search.value; render(); });
kind.addEventListener("change", () => { state.kind = kind.value; render(); });
document.querySelectorAll("[data-language]").forEach(button => {
  button.addEventListener("click", () => setLanguage(button.dataset.language, true));
});
window.addEventListener("hashchange", applyHashFilter);
let preferred = "zh";
try { preferred = localStorage.getItem("funfig-gallery-language") || "zh"; } catch (_) { /* Use Chinese by default. */ }
setLanguage(preferred);

fetch("registry.json").then(response => {
  if (!response.ok) throw new Error("registry load failed");
  return response.json();
}).then(data => {
  state.all = data.entries || [];
  state.entries = state.all.filter(item => item.gallery_visibility !== "hidden");
  [...new Set(state.entries.map(item => item.kind))].sort().forEach(value => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = text(value);
    kind.appendChild(option);
  });
  applyHashFilter();
}).catch(error => {
  state.error = error.message;
  render();
});
