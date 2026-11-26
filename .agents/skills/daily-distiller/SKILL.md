---
name: daily-distiller
description: Reviews today's reports in $DATA_REPO/reports/ and generates a synthesized Knowledge Distillation document in $DATA_REPO/reports/distillations/. Use this skill whenever the user asks to "summarize today's reports", "distill today's knowledge", "run daily distillation", or "update the knowledge distillation document". It ensures technical insights about AI Agents and Context Engineering are preserved and systematized.
---

# Daily Distiller

Synthesizes today's intelligence reports into a low-cognitive-load **Answer-First Pyramid** Knowledge Distillation document — leading with a 1-sentence conclusion and 1 concrete action, followed by 3–5 numbered takeaways, a 1-glance cross-source table, and modular per-pillar `<details>` accordions.

## Workflow

### Step 1: Discover Today's Reports
Find all `.md` files created today in the `$DATA_REPO/reports/` directory, **excluding** `$DATA_REPO/reports/distillations/`. Use today's local date.

```bash
find reports -not -path "$DATA_REPO/reports/distillations/*" -type f -name "*.md" -newermt "YYYY-MM-DD" ! -newermt "YYYY-MM-DD+1"
```

If no reports are found, notify the user and stop.

### Step 2: Read All Reports
Read every report file in full (including inside `<details>` blocks). Note:
- **Source / Author**: newsletter name, Threads handle, website domain, etc.
- **Core engineering problems & insights**: Especially AI Agents, Context Engineering, Workflow Optimization, and System Architecture.
- **Cross-cutting themes**: Patterns appearing across multiple sources become Pillars (2–4 max; never 1:1 per report).

### Step 3: Load the Output Template
Read `assets/output_template.md` — it defines the file path, Answer-First Pyramid layout, and low-cognitive-load formatting rules.

### Step 4: Synthesize (Answer First, Explain Later)
Check `$DATA_REPO/data/lang_preferences.md` for the `Preferred Report Language` configuration, and produce the distillation document in that language (defaulting to **English** if not configured):

1. **Top Callout (`🎯 今日一句話結論` + `⚡ 本週唯一行動`)** — State the single overarching answer in plain everyday words (≤45 chars) on line 1, plus one concrete action with explicit minutes.
2. **`## 💡 今日核心重點` (Numbered 1–4, 1 short sentence each)** — Cross-source takeaways in plain language with zero paragraph walls or undefined buzzwords.
3. **`## 📊 跨來源主題速覽` (Compact Table, 2–4 rows)** — Map each Pillar to `卡在哪裡（痛點） | 怎麼解決（白話直覺） | 系統連結與來源` (`≤18 chars/cell`).
4. **`## 🔍 主題深入解構（點擊展開細節）`** — 2–4 individual `<details>` accordions (one per Pillar, plus 1 final synthesis accordion if needed), each opening **only 3 short bullets** (`痛點與脈絡 / 關鍵機制與證據 / 如何串聯進系統`), with just-in-time inline analogies and blank lines after `</summary>` and before `</details>`.

### Step 5: Save Output
Save to:
```
$DATA_REPO/reports/distillations/Knowledge_Distillation_YYYY_MM_DD.md
```
Use today's local date in the filename.

---

## Principles (from docs/workflow/synthesis.md)
- **System over Model**: Prioritize insights that improve the *system* (context, workflows, rules), not just the model output.
- **Explicit vs. Implicit**: Actively identify "Explicit Knowledge" that can be codified into AI Skills vs. "Implicit Knowledge" that remains a human edge.
- **Compounding Experience**: High-quality outputs become templates. Treat this document as a long-term asset.
