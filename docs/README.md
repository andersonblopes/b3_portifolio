# B3 Portfolio Master — Documentation Index

This `docs/` folder holds Software Design Documents (SDDs) for the project.
Each file is self-contained and scoped so you (or an AI agent) can load only
the one relevant to the task at hand instead of the whole codebase.

Source of truth is always the code in `src/`; these documents describe *why*
and *how it fits together*, with `path:line` references you can jump to for
the exact implementation. If a doc and the code disagree, the code wins —
update the doc.

## Map

| Doc | Load when you need to... |
|---|---|
| [01-overview-and-architecture.md](01-overview-and-architecture.md) | Get oriented: what the app does, module map, data flow, tech stack |
| [02-domain-financial-rules.md](02-domain-financial-rules.md) | Touch cost-basis math, corporate events, COST_RESET/BROKER_TRANSFER/AMORTIZATION logic |
| [03-data-ingestion-and-parsing.md](03-data-ingestion-and-parsing.md) | Touch `load_and_process_files`, NEG/MOV column mapping, dedup, ticker cleaning |
| [04-market-data-integration.md](04-market-data-integration.md) | Touch yfinance/brapi calls: prices, FX, splits, historical price, logos |
| [05-position-analysis-engine.md](05-position-analysis-engine.md) | Touch `analyze_position` recommendation/DCA/trailing-stop logic |
| [06-ui-frontend.md](06-ui-frontend.md) | Touch `app.py`, `tables.py`, `charts.py`, i18n (`langs.py`), session state |
| [07-testing-and-quality.md](07-testing-and-quality.md) | Add/run tests, understand coverage gate, lint/format, CI-equivalent commands |
| [08-glossary-b3-terms.md](08-glossary-b3-terms.md) | Decode B3/CVM Portuguese terms and internal `type` enum values |
| [09-known-limitations-and-roadmap.md](09-known-limitations-and-roadmap.md) | Check known gaps before "fixing" something that's a documented tradeoff |

## Related Hermes skill

The `fintech/b3-portfolio-analysis` skill (loaded automatically for B3/FII
work) encodes the same cost-basis and corporate-event rules as
`02-domain-financial-rules.md`, generalized across projects. This `docs/`
folder is the project-specific, code-grounded version with exact file/line
references; the skill is the portable, cross-project version. Keep both in
sync when the rules change here.

## Conventions used across these docs

- Code refs use `path:line` (e.g. `src/utils.py:468`) — open the file at that
  line rather than trusting inline snippets to stay current.
- "Main flow" = rows that reach `main_df` and affect portfolio qty/cost.
  "Audit flow" = rows that reach `audit_df` for transparency only (fees,
  ignored rows, settlement-only transfers).
- Financial correctness bar: every number shown to the user is treated as
  decision-critical (see `.github/copilot-instructions.md` "Agent Roles").
