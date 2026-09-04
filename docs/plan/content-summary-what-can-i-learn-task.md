# Task — Add "🧠 What Can I Learn From It" Report Section

**RFC**: [content-summary-what-can-i-learn](../rfc/content-summary-what-can-i-learn.md)
**Plan**: [content-summary-what-can-i-learn-plan](content-summary-what-can-i-learn-plan.md)

---

## Tasks

- [ ] **[MODIFY] `output_template.md`**: Insert `## 🧠 What Can I Learn From It` section between `## 📝 TL;DR` and `## 🎯 Core Thesis`
- [ ] **[MODIFY] `summarise.md`**: Update Two-Zone table to include new section in Zone A
- [ ] **[MODIFY] `summarise.md`**: Add guidance section with quality rules (2–5 bullets, Zone A, reader perspective, ❌/✅ examples)
- [ ] **[MODIFY] `summarise.md`**: Add 6th self-verification check
- [ ] **[MODIFY] `summarise.md`**: Renumber subsequent guidance sections

## Verification

- [ ] `awk` check: section exists between TL;DR and Core Thesis in `output_template.md`
- [ ] `grep -c`: ≥ 3 occurrences in `summarise.md`
- [ ] Zone A classification confirmed via grep
- [ ] `python3 scripts/validate_skill.py` passes
