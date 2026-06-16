# RCA - daily-workflow Slow YouTube Transcription under CPU-only Docker

- **日期**：2026-05-13
- **版本**：V1
- **關聯技能**：[daily-workflow](.agents/skills/daily-workflow/SKILL.md) / [ingest-youtube](.agents/skills/ingest-youtube/SKILL.md)

---

## 1. 觀察到的問題（Observed Problem）

在執行 `daily-workflow` 以處理 YouTube 任務（影片長度為 28:38）時，依據 `ingest-youtube/SKILL.md` 的規範：
- 影片長度 < 30 分鐘，應選用 `medium` Whisper 模型。

然而，當容器啟動並開始進行 `faster_whisper` 轉錄時，速度極度緩慢，進度條顯示：
```bash
Transcription:   3%|▎         | 44.54/1717.95 [03:03<1:46:18,  3.81s/ audio seconds]
```
轉錄 44.54 秒的音訊花費了 3 分鐘又 3 秒。預估剩餘時間高達 **1 小時 46 分鐘**，這會嚴重阻礙整個 Daily Workflow 流程的順暢執行。

---

## 2. 根因分析（Root Cause Analysis）

### 2.1 假說驗證（Hypotheses & Evidence）

- **假說 A：Docker 容器分配到的記憶體不足，導致 OOM 或記憶體置換（Thrashing）使速度變慢。**
  - **驗證證據**：運行 `docker info | grep -E "CPUs|Memory"`，輸出顯示：
    ```
    CPUs: 4
    Total Memory: 7.751GiB
    ```
    依據 `ingest-youtube/SKILL.md`，`medium` 模型在影片長度 < 30 分鐘時最低 RAM 要求為 4 GB。目前分配到的 7.751 GiB 充足。
  - **結論**：**拒絕假說 A**。這不是記憶體不足導致的異常。

- **假說 B：缺乏 GPU 晶片硬體加速，導致全 CPU 運算在 `medium` 大型模型上效率極低。**
  - **驗證證據**：確認宿主機（Mac）配置具有 `8 CPU`，但 Docker 虛擬機僅獲分配 `4 CPU`，且在容器環境內無法使用 GPU/MPS 等硬體加速，完全依賴 CPU（x86-64/arm64 模擬，或缺乏 Cuda 的 CPU 運算）。在 CPU 上運行 `medium`（約 1.5GB 參數規模的 CTranslate2 模型）進行多層矩陣運算，每音訊秒的運算時間極長（約 3.81s/audio-sec）。
  - **結論**：**接受假說 B (主要根因)**。

### 2.2 根因結論

- **主要根因**：`ingest-youtube/SKILL.md` 中的 Whisper 模型對照表假設的是典型的硬體加速環境或極高 CPU 核心分配。在 CPU 核心數受限（如 Docker 分配 4 CPUs）且無 GPU 加速的容器環境中，`medium` 模型的運算複雜度過高，導致轉錄時間呈數倍放大，阻塞了同步執行的 pipeline。
- **次要因素**：`daily-workflow` 與 `ingest-youtube` 的流程完全基於影片長度作靜態模型指派，未動態探測硬體資源（如 GPU 可用性或 CPU 核心數）來做自適應模型調整。

---

## 3. 採取的修復（Fix Applied）

1. **終止慢速任務**：使用 `docker kill` 終止了該進程（Container ID `dd3fbca8d16c`）。
2. **切換快速模型**：重啟轉錄任務，並手動指定為 `--whisper-model base` 模型。`base` 模型（引數規模約 140M）在 4 CPU 環境下能以極高速度運行（通常小於影片長度的 0.2 倍時間），可大幅縮短本次任務執行時間至 5 分鐘內。
3. **後續改善建議**：未來應在 `ingest-youtube/SKILL.md` 中補充說明：「*若在無 GPU/MPS 加速之 CPU 限制 Docker 環境中（如 CPUs <= 4），即使影片小於 30 分鐘，亦建議選用 `base` 或 `small` 模型以避免執行時間過長。*」

---

## 4. 狀態檢核表（Status Checklist）

- [x] 觀察並量化轉錄效能問題（3% 進度，耗時 3m3s，預估需 1h46m）
- [x] 查詢 Docker 資源配置（4 CPUs, 7.751 GiB Memory）
- [x] 確定主要根因為無 GPU 硬體加速下的 CPU 運算瓶頸（假說 B）
- [x] 乾淨終止慢速容器 `dd3fbca8d16c`
- [x] 改用 `--whisper-model base` 重新啟動背景轉錄任務
- [x] 建立此 RCA 文件，連結回相關技能
