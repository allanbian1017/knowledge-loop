# AI Analysis (Suggestion Generation)

This analysis scores the content's relevance to the user's goals and generates a calibrated suggestion to be added to the pending backlog or routed appropriately.
It is **no longer** appended to the content report directly.

*Note: The fields here overlap with Layers 4-5 in the report template. Report layers are learning artefacts for human reading; this suggestion log is an action queue for programmatic review by `review-suggestions`.*

## Prerequisites — Read Before Generating

> ⚠️ 產生分析建議前，必須：
> 1. 讀取 `$DATA_REPO/data/goals.md` 取得使用者當前目標
> 2. 若 `$DATA_REPO/data/user_preferences.md` 存在，讀取使用者偏好檔案，用其校準：
>    - **建議下一步**：優先使用者偏好的行動類型，避免使用者常拒絕的類型
>    - 依據內容本質嚴格匹配【5 大行動原型（Action Archetypes）】，嚴禁為非提示詞主題強制包裝提示詞

## 5 大行動原型（Action Archetypes）

每一條建議必須明確歸屬於以下 5 大原型之一，並在建議開頭標註原型標籤：

1. `JIRA_BACKLOG`：
   - **適用情境**：複雜系統架構設計、分散式資料副本、狀態機併發控制、模型分級路由等需要結構化跟進的工程設計。
   - **格式範例**：`[JIRA_BACKLOG] 本週花 15 分鐘，將 [X 架構原則] 整理為 Jira 待辦項目提案（目標 Epic: PROJ-3），包含具體驗收條件與架構設計邊界，不另建自動化代碼。`
   - **生命週期**：在 `$DATA_REPO/data/suggestions_pending.md` 呈現為待審提案，使用者審查通過後，由代理人調用 Atlassian MCP (`createJiraIssue`) 建立正式 Jira issue。

2. `ADR_DOC`：
   - **適用情境**：架構權衡（Trade-offs）、設計反模式（Anti-patterns）、系統選型邊界（如 MCP vs Local Function Calling）。
   - **格式範例**：`[ADR_DOC] 本週花 15 分鐘，將 [X 架構權衡] 整理為 1 篇技術決策紀錄存入 docs/adr/，明確定義選型邊界，不另建自動化工具。`

3. `PROMPT_TEMPLATE`：
   - **適用情境**：**嚴格僅限於具備人機互動或裁判特性的提示詞工具**（例如：模擬面試評分器、薪資談判教練、LLM-as-a-Judge 裁判、代碼風格去機器人化糾錯）。
   - **❌ 絕對禁止**：嚴禁將一般產業新聞、政策法規、政治事件或後端架構理論包裝為 `$DATA_REPO/data/prompts/` 模板（違者觸發 Forced Prompt Wrapping 硬否決）。
   - **格式範例**：`[PROMPT_TEMPLATE] 本週花 15 分鐘，將 [X 互動評估框架] 整理為 1 個提示詞模板，存入 $DATA_REPO/data/prompts/...；明確定義輸入變數與輸出結構。`

4. `TEST_FIXTURE`：
   - **適用情境**：邊界漏洞、並發競爭案例、例外注入或特定輸入驗證。
   - **格式範例**：`[TEST_FIXTURE] 本週花 15 分鐘，針對 [X 異常行為邊界] 撰寫 1 組 pytest 邊界測試案例存入 tests/...，作為迴歸防護。`

5. `TAKEAWAY_ONLY`：
   - **適用情境**：高信號產業新聞、宏觀趨勢、政策法規調查或純理論性知識，**無需建立任何程式碼、提示詞或待辦項目**。
   - **格式範例**：`[TAKEAWAY_ONLY] 本期核心觀點為 [X 核心總結]，已完整沉澱於內容報告與每日知識提煉中，無須建立額外待辦。`
   - **分流機制**：標記為 `TAKEAWAY_ONLY` 之建議**直接捨棄**：不寫入 `$DATA_REPO/data/suggestions_pending.md`，也不寫入 `$DATA_REPO/data/suggestions_filtered.md`，不交給 `rubric-grader`。核心觀點已沉澱於內容報告與每日知識提煉，無須額外記錄。

### Archetype Priority（單一來源項目的原型優先序）

每個來源項目（單篇文章／影片／貼文）**只能產出一條建議**。若內容同時符合多個原型，必須依下列優先序**只選最高者**；較低優先序的候選建議直接捨棄，不寫入任何檔案：

| 優先序 | 原型 |
|---|---|
| 1（最高，同級擇最適者） | `JIRA_BACKLOG`、`PROMPT_TEMPLATE`、`TEST_FIXTURE` |
| 2 | `ADR_DOC` |
| 3（最低） | `TAKEAWAY_ONLY` |

- `ADR_DOC` 僅在該項目**不符合**任何優先序 1 原型時才允許，且必須點名「本專案（<data-repo>）中一個待決定的設計抉擇與其備選方案」。僅描述第三方系統內部架構、產業案例、使用者不營運的基礎設施 → 改用 `TAKEAWAY_ONLY`。
- `TAKEAWAY_ONLY` 僅在該項目不符合優先序 1 與 2 時使用。
- 此規則不改變各原型的適用條件（例如 `PROMPT_TEMPLATE` 仍禁止 Forced Prompt Wrapping）。

---

## Fields required for the backlog

Use these definitions to determine the values for the suggestion:

- **分類**（擇一）：技術 | 商業 | 心態 | 靈感 | 其他

- **建議下一步**（非常具體）：`[ARCHETYPE] [動作 + 對象 + 範圍]`
  > ⚠️ 禁止抽象描述（例如：研究看看、了解一下）
  > ⚠️ 嚴禁 Forced Prompt Wrapping（強制包裝為提示詞）

---

## Rubric Grading Delegation

After generating the properties above:
Use the `rubric-grader` skill (Grade mode) to score and filter the suggestion.
- If `TAKEAWAY_ONLY`: Discard. Do not stage a suggestion JSON, do not call `rubric-grader`, and write nothing to `$DATA_REPO/data/suggestions_pending.md` or `$DATA_REPO/data/suggestions_filtered.md`.
- If actionable archetype (`JIRA_BACKLOG`, `ADR_DOC`, `PROMPT_TEMPLATE`, `TEST_FIXTURE`):
  - If pass ($\ge 4/6$ without veto), appends to `$DATA_REPO/data/suggestions_pending.md`.
  - If fail ($< 4/6$ or vetoed), appends to `$DATA_REPO/data/suggestions_filtered.md`.
Do not write directly to the pending file yourself.
