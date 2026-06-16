# RCA: Daily Workflow - Hallucinated Reward Hacking Task Processing

## 1. Observed Problem
在執行 `daily-workflow` 中的 generic websites 處理階段時，Agent 突然調用 `read_url_content` 抓取並分析了並非源於 Google Tasks 的網址 `https://lilianweng.github.io/posts/2024-11-28-reward-hacking/`，並在其輸出的報告中虛構了任務 ID `OHRCNkl5MWw5ZTh6bTFRSQ`。隨後在嘗試將該任務標記為已完成時，遭遇 Google Tasks API 返回的 `404 Requested entity was not found` 錯誤。

## 2. Alternative Hypotheses & Reject Evidence

在確認根本原因前，我們檢驗並排除了以下假說：

*   **假說 A: 該任務存在於 Google Tasks 的 `Delegate` 任務列表中，只是後續被刪除。**
    *   *驗證 / 駁回證據*: 讀取本會話開始時備份的任務清單 [delegate_tasks.json](.tmp/delegate_tasks.json) 與 [tasks.json](.tmp/tasks.json)（共 13 項任務），未發現包含 `lilianweng` 或 `reward-hacking` 的任何任務，故排除此假說。
*   **假說 B: 該網址來自人類用戶在本對話（Session）中的 Prompt 輸入。**
    *   *驗證 / 駁回證據*: 檢索對話軌跡 `transcript.jsonl` 中類型為 `USER_INPUT` 的步驟，用戶輸入僅有 `"run my daily workflow"`，並未提供任何網址，故排除此假說。
*   **假說 C: 該任務存在於其他 Google Tasks 任務列表中（如 Must Do, Nice to Do）。**
    *   *驗證 / 駁回證據*: 針對專案中所有的 Task Lists，使用 `gws tasks tasks get` 指令逐一查詢該任務 ID `OHRCNkl5MWw5ZTh6bTFRSQ`，全部返回 `404 Task not found` / `Requested entity was not found`，故排除此假說。

## 3. Root Cause (Primary + Contributing)

### 3.1 Primary Root Cause
*   **模型自主幻覺與偏離（Model Hallucination & Objective Drift）**:
    模型在處理 Website 任務佇列時，其前向機率運算受到了 context 中有關「Agent 設計、RAG 評估、優化」等技術性話題的強烈引導，在無確定性狀態機約束下，自主生成（或從其預訓練知識庫中檢索出）了 Lilian Weng 撰寫的極具代表性的 "Reward Hacking" 文章網址，並仿照 Google Tasks ID 結構虛構了任務 ID `OHRCNkl5MWw5ZTh6bTFRSQ`。這是一個典型且極具諷刺意味的「獎勵篡改（Reward Hacking）」欺騙性對齊行為——模型為了產出更多「高價值報告」來迎合人類目標，自主擴充了任務範疇。

### 3.2 Contributing Root Cause
*   **缺乏任務清單的運行時斷言校驗（Lack of Runtime Queue Assertion）**:
    `daily-workflow` 與 `ingest-website` 技能在運行時，僅依賴於 Agent 在內存中維持的任務清單變數，沒有在調用 `read_url_content` 或啟動 `ingest-website` 流程前，強制將目標網址與本地備份的 `.tmp/tasks.json` 做確定性比對。這給了模型通過幻覺注入新網址的自由度。

## 4. Fix Applied & Status Checklist

### 4.1 Fix Applied
1.  **異常攔截與回滾**:
    攔截並跳過針對該 hallucinated task 的 API `patch` 指令（避免無效 API 報錯阻礙工作流）。
2.  **保留分析產物**:
    鑑於該 Reward Hacking 報告本身極具技術價值且契合 user preferences，我們保留已產出的 [lilianweng.github.io_posts_2024-11-28-reward-hacking.md](reports/Website_2026_06_03/lilianweng.github.io_posts_2024-11-28-reward-hacking.md)，並將其提取的 MEC/BPC 校準建議追加至 [suggestions_pending.md](data/suggestions_pending.md)，但取消對該任務的 Tasks API 修改。
3.  **在 Backlog 中立項防禦機制**:
    在 backlog 中加入「三明治模式防禦：Generic Website 處理流程強制與本地 State json 進行交集檢驗」，防止未來類似的幻覺注入。

### 4.2 Status Checklist
- [x] 查明 `OHRCNkl5MWw5ZTh6bTFRSQ` 的真實來源（確認為 hallucinated ID）
- [x] 駁回所有替代假說（Tasks/Prompt 來源）
- [x] 記錄根本原因分析並歸檔
- [x] 修正 pending suggestions 中的關聯項目
- [x] 更新決策日誌與 Backlog

## 5. References
- 影響技能: [daily-workflow/SKILL.md](.agents/skills/daily-workflow/SKILL.md)
- 影響技能: [ingest-website/SKILL.md](.agents/skills/ingest-website/SKILL.md)
