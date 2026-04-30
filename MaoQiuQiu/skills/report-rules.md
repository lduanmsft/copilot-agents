# Report Rules — Shared Report Generation Standards

This skill defines the universal report generation rules for all agents that produce reports.
Agents that generate reports MUST read this file and follow its rules.

**Used by:** `callstack-research`, `errorcode-research`, `lduan-agent` (Mode A)

---

## 1. Output Formats

Every report generates **3 files**:

| # | Format | Language | File naming | Description |
|---|--------|----------|-------------|-------------|
| 1 | Markdown | 中文 (Chinese) | `{name}.md` | Pure Chinese only. NOT bilingual. |
| 2 | Markdown | English | `{name}_en.md` | Pure English only. |
| 3 | HTML | English | `{name}.html` | Dark theme, auto-open in browser via `Start-Process` |

**Output directory:** `C:\Users\lduan\.copilot\agents\outcome\`

---

## 2. Report Header

Every report MUST start with these fields (when available):

```
# {Report Title}

**ICM**: {ICM link or ID, if provided}
**Date**: YYYY-MM-DD
**Type**: {report type — e.g., Callstack Analysis / Error Code Research / Research Report}
**SQL Version**: {version, if applicable}
```

If user provided an ICM link, case ID, or support ticket number — it MUST appear in the header.

---

## 3. HTML Theme

HTML reports use dark theme with these CSS variables:

```css
--bg: #1e1e2e;
--surface: #282840;
--surface2: #313150;
--text: #cdd6f4;
--subtext: #a6adc8;
--blue: #89b4fa;
--green: #a6e3a1;
--red: #f38ba8;
--yellow: #f9e2af;
--mauve: #cba6f7;
--teal: #94e2d5;
--peach: #fab387;
--border: #45475a;
```

Features: syntax highlighting, collapsible sections (`<details>`), monospace code (`Cascadia Code`/`Consolas`), ADO/URL links.

---

## 4. Consistency Review Rule

**MANDATORY before generating any report.**

When the analysis conclusion differs from the initial hypothesis (e.g., initially assumed spinlock contention but confirmed as self-deadlock), review ALL sections for content based on the old hypothesis. Remove or update:

- **Customer Checks** that no longer apply (e.g., don't ask for row group counts if the bug is a code defect, not a workload issue)
- **Workarounds** that don't address the actual root cause
- **Root cause descriptions** that still reference the old hypothesis

---

## 5. Customer Checks Format

Every Customer Check query MUST have a clear purpose. Use this table format:

| Check | Query | What to look for | What it means |
|-------|-------|-------------------|---------------|

If the root cause is a confirmed code bug with a known PR fix, the only check needed is typically:

```sql
SELECT @@VERSION;
-- What to look for: build number
-- What it means: confirms whether the fix is available in the customer's version
```

Do NOT include exploratory queries that were relevant during diagnosis but not after root cause is confirmed.

---

## 6. Research Methodology Section

Every report MUST include a "Research Methodology & Tools Used" section that lists:
- Every tool call with parameters
- Failed searches (for transparency)
- Successful searches with result counts

---

## 7. Report Types

### Callstack Analysis Report
Sections: Problem Summary, Research Methodology, Full Callstack(s), Callstack Narration, Callstack Analysis, Source Code Analysis, Related Bugs, Root Cause, PR Fix Analysis (if found), Fix Availability (branch table), Resolution, Customer Checks, Escalation, References

### Error Code Research Report
Sections: Error Definition, Research Methodology, Source Code Analysis, XEvent Diagnostics, Related Docs/TSGs, Related Bugs, Workarounds, References

### Research Report (Mode A — multi-source search)
Sections: Problem Description, Search Scope, Search Findings (per source: title/URL/summary), Cross-Reference Analysis, Recommended Next Steps, References
