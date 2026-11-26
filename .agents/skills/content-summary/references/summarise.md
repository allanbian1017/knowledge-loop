# Content Summarisation Rules (v5.0 — Answer-First Pyramid & Low-Cognitive-Load Hierarchy)

All reports follow the **Answer First, Explain Later (Pyramid / BLUF)** principle and **ADHD-friendly working-memory limits**: give the 1-sentence conclusion on line 1, keep the visible top screen to ~20–30 scannable lines, and tuck explanations, formulas, and benchmarks into modular per-topic `<details>` accordions.

## Language

Check `$DATA_REPO/data/lang_preferences.md` for the `Preferred Report Language` configuration:
- Write all report headers, section titles, summaries, and contents in the configured preferred report language.
- If the configuration is missing, empty, or invalid, default to **English**.

---

## Information Hierarchy (Inverted Pyramid: 3s → 15s → 2m)

| Reading Horizon | Section | Cognitive Budget & Purpose |
|---|---|---|
| **3 Seconds (Answer First)** | Hero `🎯 一句話結論` Quote + 3 Vertical Bullets (`⭐ 推薦度` / `⚡ 下一步` / `🔗 來源`) | **Line 1 IS the final answer** in plain words (≤45 chars), followed by 3 left-aligned vertical bullets for instant visual scanning (never crammed onto one `·`-separated line). |
| **15 Seconds (Core Skim)** | `## 💡 核心重點` + conditional `## 📊 一張表看懂` | **3–5 numbered 1-line takeaways** (merging old `TL;DR` + `What Can I Learn` to eliminate duplicate summaries) + 1 compact comparison table (`≤5 rows`). |
| **2 Minutes (Explain Later)** | `## 🔍 深入解構` (Per-Topic `<details>` Accordions) + `🧭 對我的意義與來源資訊` | **1 accordion per module/argument/news item (max 5)**. Each `<summary>` states `N. Topic — 1-line conclusion`; expanding opens **only 2–3 short bullets** with exact mechanisms, formulas, and benchmarks. |

---

## Epistemic Integrity (Three-Zone Rule)

| Zone | Scope | Rule |
|---|---|---|
| **Zone A: Source Extraction** | `🎯 一句話結論`, `💡 核心重點`, `📊 一張表看懂`, `🔍 深入解構` | **100% Claim & Metric Fidelity**: Every attributed claim, mechanism, and benchmark must come strictly from the source. Never invent statistics or unstated author conclusions. |
| **Zone A+: Just-in-Time Context Bridge** | Inline parenthetical analogies (`≤10–12 chars` right where a term appears) | **Foundational Definitions Allowed**: When the source assumes domain prerequisites (`SRAM vs. HBM`, `Prefill vs. Decode`, `KV Cache`, `Lean Kernel`), inject an everyday analogy *inline at point of use* (e.g., `SRAM（晶片內超快小桌面）`). Never ask the reader to memorize a front-loaded glossary, and never present analogies as novel author findings. |
| **Zone B: Grounded Judgement** | `⭐ 推薦度`, `⚡ 下一步`, `🧭 對我的意義` | **Grounded Inference**: Score relevance and propose concrete time-bounded actions anchored to `$DATA_REPO/data/goals.md`. |

---

## 6 Hard Cognitive-Load Guardrails

1. **Answer First, Zero Preamble**:
   - Line 1 after `# {title}` MUST be `> **🎯 一句話結論**` stating the actual takeaway—never `"本文介紹了…"`, `"這篇筆記探討…"`, or `"總結來說…"`.
2. **One Summary List, Not Three**:
   - Do **not** repeat the summary across separate `TL;DR`, `What Can I Learn`, and `Core Thesis` sections. `🎯 一句話結論` gives the 1-sentence bottom line; `💡 核心重點` gives the 3–5 numbered 1-line takeaways; `🔍 深入解構` explains *how and why*.
3. **Hard Cap of ≤5 Items & Short 1-Line Bullets**:
   - Every list, table, and accordion group is capped at **≤5 items**.
   - Above the fold, every bullet is **1 short sentence (≤45 Chinese chars / ≤25 English words)** with zero raw formulas.
   - Inside `<details>`, every bullet is **1–2 short sentences**—never write 150-character paragraph walls.
4. **Tables Over Prose for Comparisons**:
   - Whenever ≥2 methods, stages, or trade-offs are compared, render **1 compact table** (`≤5 rows`, `≤18 chars/cell`) under `📊 一張表看懂`. Omit `📊 一張表看懂` completely on single-point or short social posts (<500 words).
5. **Per-Topic Accordions & Single-Home Benchmarks**:
   - Under `🔍 深入解構`, give each module/argument/news story its **own** `<details>` block (`≤5 total`) containing at most **3 micro-bullets** (`為什麼卡住 / 怎麼解決 / 數據與代價`). Exact formulas and numbers appear **once** here.
   - **GFM Blank-Line Rule**: Always leave **one blank line immediately after `</summary>` and one blank line before `</details>`** so Markdown and `$...$` math render properly.
   - For ultra-short posts (<300 words) fully captured by `💡 核心重點`, omit `🔍 深入解構` entirely!
6. **Specific Time Estimates on Next Actions**:
   - `⚡ 下一步` must specify concrete minutes (`花 15 分鐘將 X 寫入 ADR`) or state `"純觀念吸收，無需待辦"`—never vague phrases (`"研究看看"`, `"花點時間了解"`).

---

## Internal Reasoning Order vs Visual Output Order (Two-Step CoT)

1. **Internal CoT Step**: Internally extract Zone A facts/metrics, identify the content pattern (System/Tutorial modules vs. Argument steps vs. Multi-news signals), note terms needing inline analogies, and evaluate relevance against `$DATA_REPO/data/goals.md` using the 5-star scale (`★★★★★` must-read breakthrough → `★☆☆☆☆` skip).
2. **Visual Output Rendering**: Render strictly in **Inverted Pyramid (Answer First → Explain Later)** order following `output_template.md`.

### Teaser Detection
If the source is a truncated preview with no full article body, note `- **⚠️ 免責聲明**：此內容為精簡預告版，摘要僅反映可見資訊。` inside the `🧭 對我的意義與來源資訊` accordion without fabricating missing details.

---

## Self-Verification (5 Pre-Send Checks)

1. **3-Second Test**: If the reader reads *only* the top `> 🎯 一句話結論` callout box, do they immediately get (a) the plain-language core answer, (b) star rating, and (c) one concrete minute-bounded next step?
2. **Zero Redundancy & ≤30-Line Top Screen**: Is everything above `## 🔍 深入解構` ≤30 lines, with zero duplicate summary sections, zero paragraph walls, and zero raw math formulas?
3. **Per-Topic Accordion Granularity**: Does clicking any single `<details>` under `🔍 深入解構` open **at most 3 short bullets (~5–6 lines)** rather than a giant wall of text, with blank lines after `</summary>` and before `</details>`?
4. **Just-in-Time Context & ≤5 Cap**: Are niche terms explained inline (`≤10–12 chars`) right where they appear, and is every list/table/accordion group capped at ≤5 items?
5. **Factual Fidelity**: Are all attributed claims and numbers 100% faithful to the source, stated once inside the relevant accordion?
