# 08 — Glossary: B3/CVM Terms & Internal Type Enum

## Portuguese B3 statement terms → meaning

| Term (as seen in B3 exports) | Meaning | Maps to internal `type` |
|---|---|---|
| Data do Negócio | Trade date (NEG file discriminator column) | — (column, not a value) |
| Compra | Buy | `BUY` |
| Venda | Sell | `SELL` |
| Movimentação | Movement description (MOV file discriminator column) | — |
| Rendimento | FII/fund income distribution | `EARNINGS` (sub_type: Income) |
| Dividendo | Dividend | `EARNINGS` (sub_type: Dividend) |
| JCP / Juros sobre Capital Próprio | Interest on equity (a BR tax-advantaged dividend form) | `EARNINGS` (sub_type: JCP) |
| Empréstimo (de ativos) | Securities lending income | `EARNINGS` |
| Leilão de Fração | Fractional-share auction proceeds | `EARNINGS` |
| Reembolso | Reimbursement | `EARNINGS` |
| Amortização | Return of capital (fund pays back principal) | `AMORTIZATION` (reduces cost basis; sub_type: Amortization) |
| Taxa, Tarifa, IR, IOF | Fees / withheld taxes | `FEES` (audit only) |
| Transferência | Plain inter-broker custody transfer (no price) | `BROKER_TRANSFER` (triggers cost reset) |
| Transferência - Liquidação | Trade settlement confirmation (has a price) | `TRANSFER` (audit only, skipped for reset) |
| Grupamento | Reverse split (shares consolidated, fewer shares at higher price) | `REVERSE_SPLIT` |
| Desdobramento | Forward split (shares divided, more shares at lower price) | `SPLIT` |
| Bonificação | Bonus share issuance (free shares credited) | `SPLIT` |
| Fração em Ativos | Fractional shares removed by custodian | `SELL` |
| Atualização | Patrimonial restatement / NAV mark-up-or-down (mainly FIIs) | `COST_RESET` (triggers historical price fetch) |
| Entrada / Saída | Credit / Debit indicator column | — (sign multiplier: Débito → −1) |
| Instituição | Brokerage/institution name | — (`inst` column) |

## Asset type suffixes (B3 ticker convention, per `detect_asset_type`)

| Suffix | Asset type |
|---|---|
| `11` | FII/ETF (real estate fund / exchange-traded fund) |
| `34`, `31`, `33` | BDR (Brazilian Depositary Receipt) |
| `3`–`8` (excluding above) | Ação (common/preferred stock) |
| anything else | Outro (other) |

Note: this is a **suffix heuristic**, not a lookup against B3's actual
instrument registry — see doc 09 for known misclassification risk.

## Internal `type` enum (full set, across NEG + MOV)

```
BUY               NEG   qty += , cost +=
SELL              NEG/MOV  qty -=, cost rescaled at avg; also used for Fração em Ativos
EARNINGS          MOV   earnings += (Rendimento/Dividendo/JCP/Empréstimo/Leilão/Reembolso)
AMORTIZATION      MOV   cost -= (capped at 0); Amortização
COST_RESET        MOV   cost = qty * D-1 close; Atualização
BROKER_TRANSFER   MOV   cost = qty * D-1 close, only when val is empty/zero; plain Transferência
SPLIT             MOV/yfinance  qty += new_shares (MOV) or qty *= ratio (yfinance); Desdobramento/Bonificação
REVERSE_SPLIT     MOV/yfinance  qty = new_qty (MOV, absolute) or qty *= ratio (yfinance); Grupamento
FEES              MOV   audit only; Taxa/Tarifa/IR/IOF
TRANSFER          MOV   audit only; Transferência - Liquidação (settlement, not a reset)
IGNORE            NEG/MOV  audit only; anything unrecognized
```

## Other domain terms

- **NEG / MOV** — the two B3 export file families: Negociação (trades) and
  Movimentação (everything else that moves cash/positions).
- **FII** — Fundo de Investimento Imobiliário, a Brazilian real estate
  investment trust, traded on B3 like a stock but with monthly distribution
  obligations.
- **FI** — regular (non-real-estate) investment fund; CVM publishes daily
  NAV for these (`inf_diario_fi`) but not for FIIs.
- **CVM** — Comissão de Valores Mobiliários, Brazil's securities regulator
  and open-data publisher (`dados.cvm.gov.br`).
- **Preço teórico** — B3's proprietary theoretical/reference price used
  internally by banks for corporate-action cost-basis resets; not exposed
  via any free API, hence the documented residual gap in doc 04.
- **D-1 close** — the closing price on the last trading day *before* a given
  event date; B3's own convention for corporate-action reference pricing,
  replicated by `fetch_historical_price` (doc 02, doc 04).
