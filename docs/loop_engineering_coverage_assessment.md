# Loop Engineering 架構覆蓋度評估報告

> **評估日期**: 2026-06-11
> **參考框架**: [Google 工程師教你什麼是 Loop Engineering](../reports/Website_2026_06_11/share.google_Google_工程师教你什么是_Loop_Engineering.md)
> **評估對象**: [<data-repo>](../) 專案

---

## 總覽

Loop Engineering（迴圈工程）定義了六個核心維度，用以衡量一個 AI Agent 系統是否具備「自動迭代迴圈」的能力。本報告逐一對照 `<data-repo>` 專案的現狀，以量化證據進行成熟度評估。

### 成熟度定義

| 等級 | 名稱 | 描述 |
|:---:|:---:|:---|
| L0 | 缺失 | 該維度未被實現，也無任何規劃 |
| L1 | 規劃中 | 有 RFC / Backlog 條目，但尚未落地 |
| L2 | 基礎實現 | 核心功能已上線，但尚有明確缺口 |
| L3 | 成熟運作 | 功能完整運作且經過生產驗證 |
| L4 | 進階優化 | 具備自我改進、度量與回饋閉環 |

---

## 維度評估總表

| # | 維度 | 成熟度 | 分數 | 關鍵證據 |
|:-:|:---|:---:|:---:|:---|
| 1 | **Automations（自動化心跳）** | L3 | ★★★☆ | `daily-workflow` 鏈式編排 + `/goal` run-until-done |
| 2 | **Worktrees（工作區隔離）** | L1 | ★☆☆☆ | 平台原生支援 `branch`/`share`，但專案未主動使用 |
| 3 | **Skills（專案知識）** | L4 | ★★★★ | 19 個 SKILL.md + 共享 reference 庫 + 版本化演進 |
| 4 | **Plugins / Connectors（工具連接）** | L3 | ★★★☆ | 3 個 MCP Server + gws CLI + agent-browser + Jina |
| 5 | **Sub-agents（做檢分離）** | L2 | ★★☆☆ | `research` / `self` 子代理可用，但未實現獨立驗證器 |
| 6 | **State / Memory（外部狀態）** | L4 | ★★★★ | 多層 Markdown 狀態檔 + 偏好學習 + RCA 沉澱 |

**整體 Loop Engineering 覆蓋度**: **70%**（24 / 24 滿分中取得 17 分）

---

## 1. Automations（自動化心跳）— L3 ★★★☆

> **定義**: 通過定時任務或 `/goal` 指令驅動的自動化迴圈，讓系統持續運行直到目標完成。

### 現狀證據

| 能力 | 狀態 | 證據 |
|:---|:---:|:---|
| 全流程鏈式編排 | ✅ | [daily-workflow](../.agents/skills/daily-workflow/SKILL.md) 以 7 步驟串接：Discover → YouTube bg → Newsletter → Threads → Website → YouTube collect → Distill → Review |
| `/goal` run-until-done | ✅ | 本次會話即使用 `/goal` 模式執行長時間任務 |
| 批次迴圈處理 | ✅ | [ingest-newsletter](../.agents/skills/ingest-newsletter/SKILL.md) 以「步驟1→步驟2→重複步驟1」的迴圈模式持續處理至無未讀信件 |
| 背景非同步任務 | ✅ | YouTube 轉錄使用 `WaitMsBeforeAsync=5000` 丟入背景，主流程繼續處理其他任務 |
| 定時觸發（Cron） | ⚠️ | 支援 `/schedule` 指令可設定 cron，但尚無已配置的 recurring schedule |
| 停止條件驗證 | ⚠️ | 以「無未讀信件」或「所有任務完成」為隱含停止條件，但缺少獨立的驗證代理 |
| 熔斷機制 | ❌ | [Backlog #5](../backlog.md) 已規劃 Circuit Breaker，但尚未實現 |

### 量化數據
- 連續產出報告天數（reports 目錄）：**2026-04-07 至 2026-06-11**，跨度 65 天，共 **119 個日期子目錄**、**761 篇 Markdown 報告**
- 知識蒸餾連續天數（distillations）：**31 份**，從 2026-04-29 起

### 差距分析
- **缺少 recurring cron schedule**：目前 `daily-workflow` 仍需手動觸發（「run my daily workflow」）。若能配置一個每日固定時間的 cron，即可達到 L4 的「無人值守心跳」。
- **缺少 Circuit Breaker**：長時間迴圈存在 API 超額的風險（已在 Backlog #5 規劃）。

### 升級路徑 → L4
1. 配置 `/schedule` cron 每日自動觸發 daily-workflow
2. 實作 Backlog #5 的 Circuit Breaker 機制

---

## 2. Worktrees（工作區隔離）— L1 ★☆☆☆

> **定義**: 使用 `git worktree` 為每個並行代理提供物理隔離的程式碼空間，防止衝突。

### 現狀證據

| 能力 | 狀態 | 證據 |
|:---|:---:|:---|
| 平台原生支援 | ✅ | Antigravity 的 `invoke_subagent` 支援 `Workspace: 'branch'` 和 `'share'`（類 Git Worktree） |
| 專案主動使用 Worktree | ❌ | `git worktree list` 顯示：`No worktrees configured` |
| 並行代理隔離 | ❌ | 目前所有子代理使用 `Workspace: 'inherit'`（共享工作空間） |
| 自動清理機制 | ❌ | 無 worktree 生命週期管理 |

### 量化數據
- 現存 worktree 數量：**0**
- Skills 中使用 worktree 的指令數量：**0**（所有 SKILL.md 中均無 `git worktree` 指令）
- 相關知識累積：**22+ 處** reports 和 suggestions_reviewed 中提及 worktree 的段落，表明概念已被充分認知

### 差距分析
- **認知完備，執行缺失**：專案已累積大量關於 Git Worktree 的知識（報告中出現 22+ 次相關討論），但從未在實際工作流中使用。
- **影響範圍有限**：由於 `<data-repo>` 以內容處理為主（非代碼修改型任務），並行寫入同一檔案的衝突風險本身較低。Worktree 的價值主要在「多 subagent 同時修改代碼」的場景中。
- **Backlog #9**（[Bubble Permission Gate](../backlog.md)）規劃了 subagent 安全機制，但未涉及 worktree。

### 升級路徑 → L2
1. 在 `study-github-repo` 等需要 clone 外部代碼的技能中，使用 `Workspace: 'branch'` 啟動 subagent
2. 在 daily-workflow 的並行 YouTube 轉錄步驟中，嘗試以 `Workspace: 'share'` 隔離

### 務實評估
> [!NOTE]
> 對於以「內容處理」為核心的工作流，Worktree 的急迫性低於其他維度。專案的主要並行場景（YouTube 背景轉錄 + Newsletter 前台處理）操作的是不同檔案目錄（`reports/YouTube_*` vs `reports/Newsletter_*`），天然隔離。Worktree 的真正價值將在專案引入「多代理同時修改代碼」（如自動 PR 修復）時才充分體現。

---

## 3. Skills（專案知識）— L4 ★★★★

> **定義**: 以 `SKILL.md` 格式將專案規則、構建步驟沉澱，避免 Agent 冷啟動時猜測。

### 現狀證據

| 能力 | 狀態 | 證據 |
|:---|:---:|:---|
| 模組化 Skill 體系 | ✅ | **19 個 skill 目錄**，每個均有 `SKILL.md` |
| 共享 reference 庫 | ✅ | [content-summary](../.agents/skills/content-summary/SKILL.md) 提供 5 個共享 reference 檔案，被 4+ ingest skill 引用 |
| 版本化演進（RFC） | ✅ | [docs/rfc/](../docs/rfc) 內有 **9 篇 RFC**，記錄每次 Skill 重大變更 |
| 結構化品質標準 | ✅ | [summarise.md](../.agents/skills/content-summary/references/summarise.md) 定義了 Two-Zone Rule + 7 Layers Framework |
| Skill 互引與組合 | ✅ | `daily-workflow` → `ingest-newsletter` → `content-summary/references/*` 形成三層引用鏈 |
| 全域約束文件 | ✅ | [AGENTS.md](../AGENTS.md)（64行）、[CONTEXT.md](../CONTEXT.md)（11行）精煉且聚焦 |
| 術語表 | ✅ | CONTEXT.md 定義了 Trace、Dreamer、Memory Injection 三個專案核心概念 |
| Troubleshooting 指南 | ✅ | 多個 SKILL.md 末尾包含常見問題排除段落 |

### 量化數據

| 指標 | 數值 |
|:---|:---:|
| 總 Skill 數 | 19 |
| 含 Troubleshooting 段落的 Skill | 4（ingest-youtube, ingest-threads, ingest-website, study-github-repo）|
| 共享 Reference 檔案 | 5（summarise, output_template, ai_analysis, suggestion_log, filename_rules）|
| RFC 文件數 | 9 |
| AGENTS.md 行數 | 64（精煉） |
| ADR 文件數 | 內嵌於 RFC 中（如 content-summary-key-insight.md 含 6 個 ADR）|

### 為何評為 L4
- 已超越「有 SKILL.md」的基礎階段，具備**共享 reference、RFC 演進、ADR 決策記錄、術語表**等高級治理機制
- AGENTS.md 遵循「保持精煉」的原則（用戶明確表示「the file is already thin and concise」）
- 具備 `skill-creator` meta-skill 用於建立和優化技能

### 可繼續深化的方向
1. 為每個 Skill 加入 `evals.json` 自動化評測（Backlog #6）
2. 實現 Dreamer 的 Memory Injection，自動向 SKILL.md 注入經驗規則（RFC 已完成：[agents-that-dream](../docs/rfc/agents-that-dream.md)）

---

## 4. Plugins / Connectors（工具連接）— L3 ★★★☆

> **定義**: 基於 MCP 將 filesystem 以外的系統接入迴圈，賦予代理「真正動手做事」的能力。

### 現狀證據

| 連接器 | 類型 | 用途 | 狀態 |
|:---|:---|:---|:---:|
| `n8n-mcp` | MCP Server | 工作流自動化引擎（含 25+ tools） | ✅ 已接入 |
| `ros-mcp-server` | MCP Server | ROS 機器人控制 | ✅ 已接入 |
| `mymikacloset-outfit-images` | MCP Server | 圖片資源服務 | ✅ 已接入 |
| `gws` CLI (Gmail) | CLI Tool | 讀取/發送/管理 Gmail | ✅ 生產使用 |
| `gws` CLI (Tasks) | CLI Tool | 管理 Google Tasks | ✅ 生產使用 |
| `agent-browser` | CLI Tool | 瀏覽器自動化（Threads 爬蟲等） | ✅ 生產使用 |
| `yt2doc` | CLI Tool | YouTube 影片轉錄 | ✅ 生產使用 |
| `gh` CLI | CLI Tool | GitHub API 互動 | ✅ 生產使用 |
| Jina Reader API | HTTP API | 網頁內容提取 (`r.jina.ai`) | ✅ 生產使用 |
| BeforeTool Hook | 安全機制 | 攔截危險指令（force push、rm -rf /） | ✅ 已啟用 |

### 量化數據
- MCP Server 數量：**3 個**
- CLI 工具數量：**4 個**（gws, agent-browser, yt2doc, gh）
- HTTP API 整合：**1 個**（Jina Reader）
- 安全 Hook：**1 個**（[prevent_dangerous_commands.sh](../scripts/hooks/prevent_dangerous_commands.sh)）

### 差距分析
- **MCP Server 已接入但使用深度不明**：`n8n-mcp` 有 25+ 工具但在 SKILL.md 中未被任何 skill 引用；`ros-mcp-server` 和 `mymikacloset-outfit-images` 同樣未在任何工作流中正式使用。
- **CLI 工具整合成熟**：`gws`、`agent-browser`、`yt2doc` 被多個 skill 在生產中大量使用，覆蓋 Gmail、Google Tasks、瀏覽器自動化、YouTube 轉錄四大場景。
- **缺少 Slack / Linear 等團隊協作連接器**：Loop Engineering 文章特別提及的 Slack 和 Linear 整合尚未接入。

### 升級路徑 → L4
1. 在至少一個 Skill 中正式使用 `n8n-mcp` 的工作流自動化能力
2. 評估接入 Slack 或 Notion connector 作為外部通知渠道

---

## 5. Sub-agents（做檢分離）— L2 ★★☆☆

> **定義**: 拆分「撰寫代碼的代理」與「進行驗證的只讀代理」，防止模型自己打分過於寬容。

### 現狀證據

| 能力 | 狀態 | 證據 |
|:---|:---:|:---|
| Subagent 基礎設施 | ✅ | 平台提供 `invoke_subagent`、`define_subagent`、`send_message` 完整 API |
| 預定義子代理類型 | ✅ | `research`（只讀研究）、`self`（完整能力複製） |
| 自定義子代理 | ✅ | `define_subagent` 可定義專用子代理（如 [content-summary-subagent RFC](../docs/rfc/content-summary-subagent.md)） |
| 做檢分離（核心要求） | ❌ | **無獨立驗證代理**。所有 ingest skill 由同一代理執行「生成 + 自我檢查」 |
| 並行子代理協作 | ⚠️ | 平台支援，但 daily-workflow 僅用背景 task（`run_command` async）而非 subagent 並行 |
| 權限升級機制 | ❌ | [Backlog #9](../backlog.md) 規劃了 Bubble Permission Gate，但未實現 |

### 量化數據
- SKILL.md 中引用 subagent 的數量：**0**（無任何 skill 在流程中使用 `invoke_subagent`）
- RFC 中討論 subagent 的文件數：**1**（[content-summary-subagent.md](../docs/rfc/content-summary-subagent.md)）
- Backlog 中涉及 subagent 的條目：**1**（#9 Bubble Permission Gate）

### 差距分析

> [!IMPORTANT]
> **做檢分離是 Loop Engineering 無人值守迴圈的安全保障**。目前所有工作流均為「同一代理生成 → 同一代理自我驗證」模式。在 [summarise.md](../.agents/skills/content-summary/references/summarise.md) 中已有 Self-Verification 步驟（「審稿專家」角色），但這是 prompt-level 的角色切換，而非物理上獨立的驗證代理。

- **缺少獨立 Verifier Agent**：Loop Engineering 強調「撰寫的代理」和「驗證的代理」必須是不同的代理（甚至使用不同的思考預算），以避免自我評分偏差。本專案的 Self-Verification 是 prompt 內的角色模擬，無法提供真正的隔離。
- **Backlog #1**（[LLM-as-a-Judge](../backlog.md)）已規劃了獨立的 Auditor Agent，但狀態為 Pending。

### 升級路徑 → L3
1. **最小化方案**：為 `daily-workflow` 的 Step 6（Distill）新增一個 `research` 子代理，以只讀模式驗證蒸餾報告的事實性
2. **中期方案**：實作 Backlog #1 的 LLM-as-a-Judge，為 ingest pipeline 加入獨立 Auditor Agent
3. **長期方案**：為所有 ingest skill 設計 `define_subagent` based verifier，使用高 thinking budget 進行格式 + 事實 + 幻覺檢測

---

## 6. State / Memory（外部狀態）— L4 ★★★★

> **定義**: 利用本機 Markdown 或看板儲存任務進度與專案慣例，突破 context 限制，讓 Agent 冷啟動時能接續前進。

### 現狀證據

| 狀態檔案 | 用途 | 更新頻率 | 證據 |
|:---|:---|:---|:---:|
| [AGENTS.md](../AGENTS.md) | 全域行為約束 | 低（穩定） | 64 行，精煉 |
| [CONTEXT.md](../CONTEXT.md) | 術語表 | 低 | 3 個定義 |
| [backlog.md](../backlog.md) | 統一待辦事項 | 中 | 12 個條目 |
| [goals.md](../data/goals.md) | 用戶優先級 | 低 | 5 個目標 |
| [user_preferences.md](../data/user_preferences.md) | AI 建議偏好 | 高（每次 review 更新） | 390 條 reviewed + 精算統計 |
| [suggestions_pending.md](../data/suggestions_pending.md) | 待審建議佇列 | 高（每次 ingest 追加） | 持續增長 |
| [suggestions_reviewed.md](../data/suggestions_reviewed.md) | 已審建議歷史 | 高 | 273KB，390+ 條目 |
| [prompts.md](../data/prompts.md) | Prompt 模板庫 | 中 | 45KB |
| [known_issues.md](../known_issues.md) | 運行教訓 | 低 | 環境問題登記 |
| `docs/rca/` | 根因分析 | 中 | 9 篇 RCA |
| `docs/rfc/` | 技術提案 | 中 | 9 篇 RFC |
| `reports/` | 執行產出 | 高（每日） | 761 篇報告 |
| `reports/distillations/` | 知識蒸餾 | 高（每日） | 31 篇 |
| `.tmp/` | 臨時暫存區 | 高 | gitignored，安全 |
| Google Tasks「Delegate」 | 外部任務看板 | 高 | 經 `gws tasks` 讀寫 |

### 量化數據

| 指標 | 數值 |
|:---|:---:|
| 磁碟上的持久化狀態檔案類別 | 15+ 種 |
| 總報告數 | 761 篇 |
| 已審建議數 | 390 條 |
| RCA 文件 | 9 篇 |
| RFC 文件 | 9 篇 |
| 知識蒸餾 | 31 篇 |
| 外部狀態源（Google Tasks） | 1 個 |

### 為何評為 L4
- **多層次的狀態設計**：從全域約束（AGENTS.md）→ 領域知識（SKILL.md references）→ 任務進度（task.md）→ 用戶偏好（user_preferences.md）→ 執行產出（reports/）→ 反思沉澱（RCA, RFC, distillations），形成完整的記憶階層。
- **自動化偏好學習**：[review-suggestions](../.agents/skills/review-suggestions/SKILL.md) 在每次用戶回饋後自動重新計算 user_preferences.md，包含 recency-weighted 主題偏好、衝突偵測（Shifting Interests）、顯性偏好覆蓋等機制。這是一個**自我完善的記憶系統**。
- **Known Issues Registry**：環境問題以結構化格式登記於 `known_issues.md`，每次冷啟動時載入。
- **Dreamer RFC 已通過**：[agents-that-dream](../docs/rfc/agents-that-dream.md) 設計了 Trace → Dreamer → Memory Injection 的三階段反思迴圈，將 SKILL.md 作為 local memory injection 的目標，避免全域 context 膨脹。

### 可繼續深化的方向
1. 實作 Dreamer RFC 的 Trace 收集與 Memory Injection，讓技能真正「睡覺時變聰明」

---

## 雷達圖總覽

```
                    Automations (L3)
                         ★★★☆
                          /\
                         /  \
            State (L4)  /    \  Worktrees (L1)
            ★★★★      /      \  ★☆☆☆
                      /   ⬡    \
                     /          \
                    /            \
        Skills (L4) ------------ Sub-agents (L2)
          ★★★★                    ★★☆☆
                  \              /
                   \            /
                    \          /
                  Connectors (L3)
                     ★★★☆
```

---

## 優先行動建議（按 ROI 排序）

| 優先級 | 行動 | 目標維度 | 預期升級 | 工作量 |
|:---:|:---|:---:|:---:|:---:|
| 🔴 P0 | 為 ingest pipeline 加入獨立 Verifier 子代理（Backlog #1） | Sub-agents | L2→L3 | 中 |
| 🟠 P1 | 實作 Dreamer 的 Trace + Memory Injection（RFC 已通過） | State + Skills | L4→L4+ | 中 |
| 🟡 P2 | 配置 daily-workflow 的 `/schedule` cron 觸發 | Automations | L3→L4 | 小 |
| 🟡 P2 | 實作 Circuit Breaker（Backlog #5） | Automations | L3→L4 | 小 |
| 🟢 P3 | 在 study-github-repo 中使用 `Workspace: 'branch'` 子代理 | Worktrees | L1→L2 | 小 |
| 🟢 P3 | 在至少一個 Skill 中使用 n8n-mcp 的工作流能力 | Connectors | L3→L4 | 小 |

---

## 結論

`<data-repo>` 專案在 Loop Engineering 六維度中展現了**不對稱的強勢**：

- **最強維度**：**Skills（L4）** 和 **State/Memory（L4）** 是專案的絕對優勢。19 個結構化技能 + 多層次記憶系統 + 自動化偏好學習構成了一個「每次冷啟動都能完美復位」的 Agent 系統。這正是 Loop Engineering 強調的「把進度與慣例沉澱在磁碟上」的標竿實踐。

- **紮實的中間層**：**Automations（L3）** 和 **Connectors（L3）** 已達生產等級，daily-workflow 每日穩定產出 761+ 篇報告。

- **最大缺口**：**Sub-agents（L2）** 缺少做檢分離的獨立驗證器，以及 **Worktrees（L1）** 未在生產中使用代碼隔離。

- **核心洞察**：專案的設計哲學已經是 Loop Engineering 的自然實踐者——它具備外部狀態驅動（State）、模組化知識沉澱（Skills）、自動化流水線（Automations）。唯一阻礙專案邁向「無人值守迴圈」的瓶頸是**做檢分離**：在生成與驗證之間引入物理隔離的獨立代理。一旦補上這塊，本專案將具備完整的 Loop Engineering 能力。
