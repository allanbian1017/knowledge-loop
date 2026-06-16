# RCA: Ingest YouTube - Unprocessed Completed Transcription Task

## 1. Observed Problem
在執行 `daily-workflow` 後，YouTube 任務 `"Building a Life - Howard H. Stevenson (2013)"`（任務 ID：`eTV3Q2dlang3dnNmSkFKTQ`，影片 ID：`wLn28DrSF68`）雖然成功完成了後台 Whisper 轉譯，並產生了 53KB 的原始逐字稿 `reports/YouTube_2026_06_03/wLn28DrSF68.md`，但工作流並未對其進行後續的摘要生成、撰寫正式報告、追加建議至 `data/suggestions_pending.md` 以及將任務標記為已完成，且原始逐字稿未被清理。

## 2. Alternative Hypotheses & Reject Evidence

我們檢驗並排除了以下假說：

*   **假說 A: `yt2doc` 後台轉譯任務失敗或記憶體不足（OOM）。**
    *   *驗證 / 駁回證據*: 檢視 `.system_generated/tasks/task-62.log` 以及對話歷史中的系統通知 `sender=39f1a03f-12f4-43bc-b723-1461ed21f69a/task-62 finished`，確認指令執行成功且 exit code 為 0。此外，`reports/YouTube_2026_06_03/wLn28DrSF68.md` 檔案大小為 53,660 bytes，內容完整包含 verbatim chapters，故排除此假說。
*   **假說 B: 該任務未被 Step 1 的任務列表抓取到。**
    *   *驗證 / 駁回證據*: 讀取本專案暫存的任務列表 `.tmp/tasks.json`，在第 94-111 行明確包含 ID 為 `eTV3Q2dlang3dnNmSkFKTQ` 的任務，其連結為 `https://youtube.com/watch?v=wLn28DrSF68&si=orYgl0pbVYwIwTJf`，故排除此假說。
*   **假說 C: 該任務已被處理並標記完成，但檔案遺失。**
    *   *驗證 / 駁回證據*: 透過 gws 指令查詢任務狀態，該任務的 status 仍為 `needsAction`（未完成），且 `data/suggestions_pending.md` 沒有任何與 `wLn28DrSF68` 相關的紀錄，故排除此假說。

## 3. Root Cause (Primary + Contributing)

### 3.1 Primary Root Cause
*   **非同步任務監聽遺漏與狀態丟失（Asynchronous Task Callback Loss）**:
    在之前的執行中，YouTube 後台轉譯任務 `task-62` 運行時間較長（約 10 分鐘）。在此期間，Agent 轉入處理大量 generic websites 佇列及 newsletter 的同步與非同步任務（包括對 Lilian Weng 論文的處理）。當 `task-62` 最終完成並發送 high-priority system message 通知時，Agent 的注意力上下文已被大量網站報告生成所佔滿，並未按照 `daily-workflow` 技能的 `Step 5 — Complete YouTube tasks` 返回處理 YouTube 佇列，而是直接進入了 `Step 6 — Distill` 和 `Step 7 — Review suggestions`。

### 3.2 Contributing Root Cause
*   **缺乏任務處理的剛性防禦檢查（Lack of Pipeline Completion Assertion）**:
    `daily-workflow` 缺乏對所有已啟動 background jobs 處理狀態的強校驗。在執行 `daily-distiller` 與生成建議前，沒有檢驗 `background_jobs` 列表是否均已完成並被妥善處理，導致完成的後台任務被遺忘在背景中。

## 4. Fix Applied & Status Checklist

### 4.1 Fix Applied
1.  **手動執行遺漏的 YouTube 處理步驟**：
    - 讀取 raw transcript `reports/YouTube_2026_06_03/wLn28DrSF68.md`。
    - 依據 `summarise.md` 與 `output_template.md` 生成 Traditional Chinese 的 7 Layers 學習報告，存為 `reports/YouTube_2026_06_03/Building_a_Life_Howard_H_Stevenson_2013.md`。
    - 依據 `ai_analysis.md` 與 `suggestion_log.md`，產生一筆具體的心態/職涯建議，寫入 `data/suggestions_pending.md`。
    - 調用 `gws` 將任務 `eTV3Q2dlang3dnNmSkFKTQ` 標記為 completed。
    - 清理原始逐字稿 `reports/YouTube_2026_06_03/wLn28DrSF68.md`。
2.  **更新 Suggestion Review Artifact**：
    - 重新整理 Review List，確保 Howard Stevenson 的建議出現在 `ai_suggestion_review.md` 中。
3.  **編寫自動化驗證腳本**：
    - 在 `.tmp/verify_youtube_fix.py` 中編寫斷言，校驗報告存在性、建議內容以及任務完成狀態。

### 4.2 Status Checklist
- [x] 讀取並分析 `wLn28DrSF68.md` 內容
- [x] 撰寫正式報告 `Building_a_Life_Howard_H_Stevenson_2013.md`
- [x] 追加分析建議至 `suggestions_pending.md`
- [x] 調用 Tasks API 將 `eTV3Q2dlang3dnNmSkFKTQ` 標記為 completed
- [x] 刪除 raw transcript `wLn28DrSF68.md`
- [x] 更新 `ai_suggestion_review.md` artifact
- [x] 執行 `.tmp/verify_youtube_fix.py` 驗證修復

## 5. References
- 影響技能: [daily-workflow/SKILL.md](.agents/skills/daily-workflow/SKILL.md)
- 影響技能: [ingest-youtube/SKILL.md](.agents/skills/ingest-youtube/SKILL.md)
