# RCA: Newsletter Summaries Too Short

- **Date**: 2026-04-02
- **Report Affected**: `reports/Newsletter_2026_04_02_1129.md`
- **Workflow**: `.agents/workflows/newsletter_summary.md`

---

## Observed Problem

Many summaries in the report are truncated. Entries #9, #12, #14–#30 contain only the **Executive Summary** section, missing **Key Highlights** and **Action Items** entirely.

| Batch | Quality |
|---|---|
| Batch 1 (#1–10) | Mostly complete |
| Batch 2 (#11–20) | Degrading from #12 onward |
| Batch 3 (#21–30) | Almost all missing Key Highlights |

---

## Root Cause

### 🔴 Primary: Output Token Budget Exhaustion During Final Compilation

The workflow uses a **two-phase architecture**:
1. Summarize each batch of 10 emails fully (Step 2)
2. Compile all batches into one final file at the end (Step 3)

When reproducing 30 full newsletters in a single output pass during Step 3, the agent hits its **output token limit** mid-report. To accommodate all 30 entries, it implicitly drops sections (Key Highlights, Action Items) from later entries — especially in batches 2 and 3.

### 🟡 Contributing: No Incremental Write Strategy

Workflow Step 2 instructs to `暫存本批次的摘要結果` (hold in memory) and only write to file once at the very end (Step 3). This forces all 30 summaries to be regenerated in a single final output, maximizing compression pressure.

### 🟡 Contributing: Guard Instruction Is Insufficient

Step 3 (line 68) warns against "consciously compressing" content but does not handle the case where the model is **implicitly forced to compress** due to output length constraints at scale.

---

## Fix Applied

Two changes proposed to `newsletter_summary.md`:

1. **Write-as-you-go**: Append each batch's summaries to the report file immediately after summarization (end of Step 2), rather than holding everything in memory until Step 3.
2. **Strengthen Step 3 guard**: Explicitly state that each `<details>` block must be copied verbatim and that missing sections (Key Highlights, Action Items) are errors.

### Does Clearing Context Help?

**No — context clearing is not needed and is counterproductive.** Here's why:

- The bottleneck is **output tokens** (how much the model writes in one pass), not **input context** (how much it remembers).
- The write-as-you-go fix eliminates the problem entirely: each batch is written to disk immediately, so Step 3 only needs to write a header/summary — not reproduce all 30 summaries from scratch.
- Clearing context between batches would actually *break* the workflow, as the agent needs to remember prior batch counts and the accumulated file path to append correctly.

---

## Status

- [x] Root cause identified
- [x] Fix applied to `newsletter_summary.md` (2026-04-02)
