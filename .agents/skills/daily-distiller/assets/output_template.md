# Daily Distiller — Output Template (Answer-First Pyramid)

Defines the output path, filename convention, and Answer-First Pyramid structure for Knowledge Distillation reports.

---

## File Output Rules

- **Directory**: `$DATA_REPO/reports/distillations/`
- **Filename format**: `Knowledge_Distillation_YYYY_MM_DD.md` (use today's local date)
- Re-running on the same day overwrites the existing file

---

## Cognitive-Load & Quality Rules

- **Answer First (3-Second Top Block)**: Line 1 after `# Title` MUST be a standalone `> **🎯 今日一句話結論**` quote in plain everyday language (≤45 chars), followed immediately by a `- **⚡ 本週唯一行動**：` bullet with explicit minutes.
- **1-Screen Skim (~20–25 Lines Above `<details>`)**: Keep `💡 今日核心重點` to 3–4 numbered 1-line bullets and `📊 跨來源主題速覽` to a 2–4 row table (`≤18 chars/cell`). Zero prose walls!
- **Per-Pillar Accordions (`<details>`)**: Group insights across multiple sources (never 1:1 per report). Put each Pillar in its own `<details>` block (`2–4 max`), containing **at most 3 short bullets** with just-in-time inline analogies and blank lines after `</summary>` and before `</details>`.

---

## Markdown Template

```markdown
# Knowledge Distillation: [直白具體的主題標題] (YYYY-MM-DD)

> **🎯 今日一句話結論**：[≤45 字白話點破今日跨來源最核心的工程結論，零術語堆疊]

- **⚡ 本週唯一行動**：[1 個具體可動手的行動 + 明確分鐘數]

## 💡 今日核心重點
1. **[重點 1]**：[≤45 字白話因果短句]
2. **[重點 2]**：[≤45 字白話因果短句]
3. **[重點 3]**：[≤45 字白話因果短句]

## 📊 跨來源主題速覽
| 主題支柱 | 卡在哪裡（白話痛點） | 核心解法直覺 | 對應來源 |
|---|---|---|---|
| **1. [支柱名稱]** | [≤18 字] | [≤18 字] | [簡短來源名] |
| **2. [支柱名稱]** | [≤18 字] | [≤18 字] | [簡短來源名] |

---

## 🔍 主題深入解構（點擊展開細節）

<details>
<summary><b>1. [支柱 1 白話名稱]</b> — [≤25 字一句話結論]</summary>

- **痛點與脈絡**：[1 句白話說明真實痛點；專業詞彙當場括號補 ≤10 字類比]
- **關鍵機制與數據**：[1–2 句短句整合跨報告證據]
- **系統怎麼串聯**：[1 句說明此支柱如何與其他支柱協作]

</details>

<details>
<summary><b>2. [支柱 2 白話名稱]</b> — [≤25 字一句話結論]</summary>

- **痛點與脈絡**：[1 句白話說明真實痛點]
- **關鍵機制與數據**：[1–2 句短句整合跨報告證據]
- **系統怎麼串聯**：[1 句說明此支柱如何與其他支柱協作]

</details>

<details>
<summary>📚 <b>今日合成來源清單</b>（Sources）</summary>

- [Report Filename 1](../<SourceType>_YYYY_MM_DD/<filename>.md)

</details>
```
