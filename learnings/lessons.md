# 📝 Learnings & Lessons

This file tracks iterative improvements, error patterns, and general lessons learned during development and autonomous bug fixing to prevent recurring mistakes.

## Best Practices & Patterns

### 1. LLM Batch Summarization Detail Loss
**Context**: When feeding a batch of items (like 10 newsletters) to an LLM for summarization in a single prompt.
**Problem**: The LLM often compresses the output across the entire batch, grouping multiple items together into simple bullet points, thereby losing critical details.
**Solution**:
- Explicitly instruct the model to produce an independent, detailed summary for **each** item in the batch.
- Avoid using instructions like "concise" or "brief aggregation" in downstream reporting steps. Instead, instruct the agent to **preserve the full output** and keep the UI clean using collapsible tags (e.g. `<details>`).
- Date: 2026-04-01
- Related Workflow: `newsletter_summary`

### 2. Prompt Caching Optimisation for LLM Inference
**Context**: Designing system prompts and tool schemas for multi-step agent workflows.
**Problem**: High inference latency and API costs due to large, dynamically changing context inputs in multi-step runs.
**Solution**:
- Structure the system prompt and tool schemas to be static and place them at the very beginning of the API request payload.
- Keep dynamic inputs (like conversation history or variable task content) at the end of the request to maximize cache hits (e.g. Anthropic's Prompt Caching) and reduce token costs/latency.
- Date: 2026-06-12
- Related Workflow: `agent_prompt_design`
