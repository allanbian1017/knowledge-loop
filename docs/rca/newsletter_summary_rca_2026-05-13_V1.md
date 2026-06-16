# RCA - newsletter-summary Stale Validation Script

- **日期**：2026-05-13
- **版本**：V1
- **關聯技能**：[newsletter-summary](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/SKILL.md) / [content-summary](file:///workspaces/my-ai-workflow/.agents/skills/content-summary/SKILL.md)

---

## 1. 觀察到的問題（Observed Problem）

當執行品質檢驗指令 `python3 scripts/validate_individual_reports.py reports/Newsletter_2026_05_12/` 時，驗證腳本回傳失敗（Exit Code `1`），並且在所有 9 份電子報報告中標記 `AI Analysis: ❌`：

```bash
📊 Quality Validation for 9 Reports in Newsletter_2026_05_12
============================================================
File: henrychu_ChatGPT_Image_2_知識圖卡實戰手冊.md
  - Source Section: ✅
  - Exec Summary: ✅
  - Highlights Bullets: 7 ✅
  - Action Items: ✅
  - AI Analysis: ❌
  - AI Fields (Category, Value, Actionability, Next Step, Decision): ❌
...
❌ Some reports failed to meet quality standards.
```

然而，這些報告在格式上完全符合最新的產出規範，卻因此檢驗失敗。

---

## 2. 根因分析（Root Cause Analysis）

### 2.1 假說驗證（Hypotheses & Evidence）

- **假說 A：電子報報告生成有瑕疵，遺漏了 AI 分析區塊。**
  - **驗證證據**：研讀 [newsletter-summary/SKILL.md](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/SKILL.md) 第 78 行明確指出：「*雖然報表檔案中不再包含 AI 分析區塊，你仍需根據 content-summary/references/ai_analysis.md 的欄位定義為每封電子報獨立產生 AI 分析與建議，並追加至 data/suggestions_pending.md*」。此外，查閱格式模板 [output_template.md](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/assets/output_template.md) 亦不包含 `## 🏷️ AI 分析` 區塊。
  - **結論**：**拒絕假說 A**。報告中不包含 AI 分析是符合設計預期的。

- **假說 B：品質驗證腳本存在「設計漂移（Design Drift）」與過時規則。**
  - **驗證證據**：閱讀 [validate_individual_reports.py](file:///workspaces/my-ai-workflow/scripts/validate_individual_reports.py) 第 18-25 行，發現腳本仍寫死要求報告檔案內部必須包含 `## 🏷️ AI 分析` 以及 `**分類**`、`**價值評分**` 等舊欄位。腳本在轉移為「中心化 suggestions 儲存」時，未同步更新校驗邏輯。
  - **結論**：**接受假說 B (主要根因)**。

### 2.2 根因結論

- **主要根因**：驗證腳本 `scripts/validate_individual_reports.py` 已經過時（Stale）。在導入中心化 suggestions 架構後，該測試腳本未能與 [SKILL.md](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/SKILL.md) 同步演進，導致檢驗機制與實際正確輸出衝突。
- **次要因素**：在過往的架構調整中，缺乏 CI/CD 機制或對應的開發檢驗程序，去警示或同步修改這類品質 Guardrails 腳本。

---

## 3. 採取的修復（Fix Applied）

更新了 [`scripts/validate_individual_reports.py`](file:///workspaces/my-ai-workflow/scripts/validate_individual_reports.py) 的校驗核心邏輯：
1. **取消報告本體要求**：不再要求個別報告 Markdown 檔案內部包含 `## 🏷️ AI 分析` 區塊，使其與最新的 [`assets/output_template.md`](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/assets/output_template.md) 完美對齊。
2. **導入跨檔案中心化校驗**：
   - 提取報告的 `filename` 基礎名稱。
   - 自動讀取中心化待審清單 [`data/suggestions_pending.md`](file:///workspaces/my-ai-workflow/data/suggestions_pending.md)。
   - 使用正則表達式，驗證其中是否存在對應該報告的 suggestion 區塊。
   - 核對該 suggestion 區塊中是否完整具備必要的 5 個分析欄位：`🏷️ 分類`、`💎 價值評分`、`⚡ 可行動性`、`🎯 決策建議` 與 `📋 建議`。
3. **成果驗證**：修復後重跑測試，2026-05-12（9份報告）與 2026-05-13（4份報告）的所有檔案皆完美通過 100% 品質檢驗：
   - `reports/Newsletter_2026_05_12/`：`🎉 All reports passed modern quality standards!`
   - `reports/Newsletter_2026_05_13/`：`🎉 All reports passed modern quality standards!`

---

## 4. 狀態檢核表（Status Checklist）

- [x] 重現品質檢驗失敗問題 (Measured Exit Code 1)
- [x] 藉由規格書與模板，分析與拒絕假說 A
- [x] 確定主要根因為 Stale Validator (假說 B)
- [x] 修改 `scripts/validate_individual_reports.py` 以兼容最新中心化 suggestions 結構
- [x] 成功驗證 2026-05-12 與 2026-05-13 的全部 13 份報告，測試 100% 通過
- [x] 建立此 RCA 文件，連結回 [SKILL.md](file:///workspaces/my-ai-workflow/.agents/skills/newsletter-summary/SKILL.md)
