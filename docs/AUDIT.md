# ERL-RMA Comprehensive System Audit & Baseline Report

**Document Date:** 2026-11-01  
**Auditor:** Principal Engineer & Senior Product Designer  
**Scope:** ERL-RMA (YottaFlex) reverse logistics platform, data generator, core domain package, API server, React dashboard, schemas, and tests.

---

## 1. Executive Summary & Baseline Metrics

Prior to applying any source code modifications, a full forensic audit was executed against the repository. Baseline tests and deterministic benchmark generation runs were performed and verified.

### 1.1 Baseline Test Suite Execution
- **Command:** `python3 -m unittest discover -s tests -p 'test_*.py'`
- **Result:** 19 tests executed, 0 failures, 0 errors in 0.355s (Pass).
- **Coverage:** Adjudication priorities 1–5, basic financial refund, condition disposition matrix, and basic audit scan.

### 1.2 Baseline Benchmark Generator Execution (Scale 0.1)
- **Command:** `python3 erl_rma_benchmark.py --seed 20261022 --scale 0.1 --out /tmp/baseline_starter`
- **Determinism Check:** Run 1 SHA-256 (`6040d24d96415536acba23b53c2f1834d17edd1123b73732a9a014e81df4516e`) == Run 2 SHA-256 (Pass).
- **Generated Row Counts:**
  - `customers`: 1,000
  - `orders`: 3,000
  - `order_lines`: 5,633
  - `return_requests`: 500
  - `return_lines`: 800
  - `return_authorizations`: 440
  - `return_shipments`: 440
  - `inspections`: 660
  - `refunds`: 665
  - `inventory_dispositions`: 660
  - `entity_state_events`: 2,545
  - `ground_truth`: 25 (5 per anomaly type)
- **Baseline KPIs Claimed:**
  - `return_authorization_rate_pct`: 85.16%
  - `net_recovery_rate_pct`: 67.95%
  - `discount_clawback_accuracy_pct`: 100.0%
  - `f1_score`: 1.000 (Tautological conformance check)

---

## 2. Findings Register

| Finding ID | Severity | File & Location | Description / Verified Flaw | Remediation Plan |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | High | `src/components/ExecutiveControlTower.tsx:109, 150, 154, 162` | Currency rendered using unparameterized `toLocaleString()`. In Indian locale environments (`en-IN`), formats with Lakh/Crore groupings (e.g. `$3,13,54,083.38`, `$24,00,944.5`) and drops trailing zero on `.5`. | Create shared formatter `formatCurrency()` using `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })` with strict 2 decimals. Centralize all number/date/percent formatters in `src/utils/formatters.ts`. |
| **F2** | Critical | `core/financial.py:57, 63` | Line-level discount and tax proration computed independently per partial refund: `round((discount / q_purch) * q_insp, 2)`. Multi-part returns drift by pennies and fail exact penny reconciliation against original paid amounts. | Implement cumulative remainder proration (`amount_k = round_half_even(total * cum_qty_k / q_purch) - sum(previous)`). Add tests splitting lines into 2, 3, and 7 parts asserting exact reconciliation. |
| **F3** | High | `core/financial.py:91`, `schema.sql:99` | Invariant $\sum R_{net} \le \text{OrderLine.net\_paid\_amount}$ is evaluated only in memory per single calculation; not enforced in database or at write time. Cumulative refunds can breach net paid. | Enforce check in `RefundCalculator` requiring cumulative refund context; add SQLite triggers blocking cumulative refund overflow on write. |
| **F4** | Medium | `schema.sql:17, 99`, `core/models.py:129, 203` | Shipping and handling fees are completely unmodeled in orders and refunds, despite spec stating refunds based on "paid price, discounts and fees". | Add `shipping_fee_paid_cents` on `orders`, `shipping_refund_cents` on `refunds`. Refund shipping only on merchant/carrier fault (`DEFECTIVE`, `DAMAGED_IN_TRANSIT`, `WRONG_ITEM`) and on full order return or final line. |
| **F5** | Medium | `core/financial.py:63` | Floating point arithmetic is used throughout `core/` and generator (`float` types). Rounding rules are implicit Python `round()` instead of documented Banker's rounding (`ROUND_HALF_EVEN`). | Transition internal representation to integer cents and `decimal.Decimal` with explicit `ROUND_HALF_EVEN`. Document rounding rule in `docs/DECISIONS.md` and `docs/REFUND_MATH.md`. |
| **F6** | Medium | `core/adjudication.py:63-65` | Boundary comparison `(request_date - delivery_date).days > return_window_days` allows return on day `W`, rejects on day `W+1`. Correct logic, but lacks explicit unit tests and boundary test records in dataset. | Add explicit unit tests verifying days $W-1$, $W$, and $W+1$. Inject explicit `VALID_BOUNDARY` records for day $W$ returns. |
| **D1** | Critical | `core/audit.py:47-50, 147`, `erl_rma_benchmark.py:477-557` | `run_validation_suite` and `AuditReconciliationEngine.scan` directly import and iterate over `ground_truth` (`gt_map`). Suppresses violations not in ground truth and computes an artificial F1 = 1.000. | Decouple detector from evaluation. Create `core/audit.py` as an independent detector producing `detections.json` with zero knowledge of ground truth. Create `core/evaluate.py` as the sole evaluator reading `ground_truth.json`. |
| **D2** | High | `erl_rma_benchmark.py:173-180` | Benchmark injects only anomalies; zero hard negatives or edge cases exist in ground truth, making detector precision artificially high. | Generate $\ge 300$ `VALID_BOUNDARY` records (day $W$ returns, quantity equal to purchased, exact net refunds, manager override approvals, partial splits, legitimate multi-line refunds). |
| **D3** | Medium | `schema.sql`, `erl_rma_benchmark.py:263-270` | `ground_truth` lacks distinction between anomalies, standard scenarios, and boundary test cases. | Add `label_class` column to `ground_truth` (`ANOMALY`, `SCENARIO`, `VALID_BOUNDARY`). Update CSV/JSON outputs. |
| **G1** | High | `core/adjudication.py:68`, `README.md:18` | Manager override claimed as "cryptographically authenticated zero-trust", but code only checks `override_approved_by.startswith("MGR-")`. | Implement HMAC-SHA256 override tokens (`override_token = HMAC(secret, request_id|manager_id|reason|issued_at)`). Document demo secret in `.env.example`. |
| **G2** | Critical | `schema.sql:125-134`, `core/audit.py` | `entity_state_events` lacks sequence numbers, previous event hashes, and event hashes. Update/delete are not blocked at database level. Segregation of Duties (SoD) is not enforced. | Add `seq`, `prev_event_hash`, `event_hash` (SHA-256). Add SQLite triggers preventing UPDATE/DELETE. Add `/api/ledger/verify` endpoint. Enforce SoD (approver actor cannot issue refund). |
| **G3** | Medium | `src/App.tsx:24, 82-90`, `api_server.py:38-46` | Persona switcher in UI is cosmetic only. Backend API has no concept of actor role or permissions. | Have frontend send `X-Actor-Role` and `X-Actor-Id` headers. Enforce RBAC in API endpoints (e.g. only `MANAGER` can override, only `OPERATOR` can inspect/disposition, only `SYSTEM`/`FINANCE` can disburse refund). Return machine-readable 403 errors. Label UI as "Demo identity". |
| **G4** | Low | `README.md:3, 123, 237`, `src/App.tsx:67` | Claims "Compliance: ISO/IEC/IEEE 29148:2018" with vanity badge. ISO 29148 is a requirements engineering process standard, not an executable compliance certification. | Remove badge. Reword to "Requirements documented following ISO/IEC/IEEE 29148 practice". Document requirements architecture in `docs/`. |
| **R1** | High | `erl_rma_benchmark.py:28, 212` | Return reasons are drawn uniformly (`rng.choice(REASONS)`), yielding ~20% across all reasons regardless of category (e.g. Apparel has same defect rate as Electronics, Size/Fit occurs equally in Home/Electronics). | Implement category-conditional return reason probability matrix in `DISTRIBUTIONS` config. |
| **R2** | High | `erl_rma_benchmark.py:66-140` | Uniform random numbers used for order amounts, dates, line counts. Lacks real-world skewness (log-normal order prices, geometric/Poisson lines per order, Q4 seasonality, gamma return latency, loyalty tier return rate variation). | Implement realistic statistical distributions driven strictly by seeded generator. |
| **R3** | Medium | `erl_rma_benchmark.py:38-43` | Benchmark uses heuristics to meet target counts. Scale 1.0 needs exact 30,000 orders, 5,000 requests, 8,000 return lines, 250 anomalies (50 each). | Use constrained sampling to hit exact counts at scale 1.0 and proportional counts at scale 0.1. |
| **R4** | Medium | `src/components/ExecutiveControlTower.tsx:199-208` | WMS disposition visual bar hardcodes percentages `76% / 6% / 14% / 4%`. Unit counts in table yield `77.1% / 5.4% / 14.0% / 3.5%`. | Dynamically calculate disposition percentages from API response using the largest-remainder method (Hamilton-Hare) summing to exactly 100.0%. |
| **H1** | High | `.gitignore` (missing) | `dist/`, `node_modules/`, and 26MB `erl_rma.sqlite` risk being committed to git repository. | Create `.gitignore` ignoring build artifacts, virtual environments, node modules, and large `.sqlite` databases. Only commit starter dataset (scale 0.1) and manifest. |
| **H2** | Medium | Root directory | Missing developer infrastructure: `.env.example`, `requirements.txt`, `Makefile`, `pyproject.toml`, `eslint.config.js`, etc. | Add full standard tooling files with ruff, mypy, strict TypeScript, and ESLint configuration. |
| **H3** | High | `erl_rma_benchmark.py:601-604` | SQLite binary file hashes are non-deterministic across platforms/SQLite versions due to B-tree page allocations. | Hash canonical CSV exports (LF `\n`, UTF-8, deterministic column order) and JSON manifests for reproducibility verification. |
| **SEC1**| High | `api_server.py:113, 312, 322` | Dynamic SQL queries built with string interpolation (`SELECT COUNT(*) FROM {t}`, `SELECT * FROM {table_name}{where_clause}`). | Whitelist allowed table and column names; parameterize all dynamic values with `?` placeholders. |
| **SEC2**| Medium | `api_server.py:302` | Pagination limit allows up to 100 but lacks strict upper bound guarding against large limits. | Enforce strict `limit <= 500` and validate `page >= 1`. |
| **API1**| Medium | `api_server.py:39-46` | Non-standard error responses (plain `{"error": "message"}`); missing response timing headers and request correlation IDs. | Standardize JSON error envelopes `{"error": {"code": "...", "message": "...", "details": {...}}}`; add `X-Request-ID` and `X-Response-Time-Ms` headers. |
| **UI1** | High | `src/index.css`, `src/App.tsx` | Excessive neon glows, gradient text, glowing pill badges, emojis, and marketing slogans ("Obsidian Slate & Neon Hologram", "Luxury web application"). | Redesign UI in restrained Linear/Stripe/Bloomberg-lite design system. Implement dark/light theme tokens in `src/styles/tokens.css` with WCAG 2.2 AA contrast. |

---

## 3. UI Implied KPI Definitions & Discrepancies

1. **Return Authorization Rate (RAR):**
   - *Current formula:* `approved_qty / requested_qty * 100`
   - *Issue:* Measures approved unit volume percentage. UI labels this interchangeably with "request approval rate".
   - *Formal Definition:* $\text{RAR} = \frac{\sum \text{approved\_qty}}{\sum \text{requested\_qty}} \times 100$.

2. **Net Inventory Asset Recovery Rate (NRR):**
   - *Current formula:* `restocked_val / total_inspected_val * 100`
   - *Issue:* Values computed using original retail `unit_price`, not cost or salvage value.
   - *Formal Definition:* Net recovered inventory value (Restocked @ 100% + Refurbished @ 70%) divided by total refunded merchandise GMV.

3. **Discount Clawback Accuracy (DCA):**
   - *Current formula:* `1.0 - (actual_clawback - theoretical_clawback) / theoretical_clawback`
   - *Issue:* Currently always 100.0% because generator artificially constructed single discounts divisible by quantity.

4. **Protected Margin Leakage (Copy Defect):**
   - *Current UI label:* "Protected Margin Leakage" showing `+$191,645.25`.
   - *Defect:* It measures recovered discounts and retained restocking fees (money saved/kept, not lost).
   - *Correct Name:* "Discount & fee recovery" with explicit breakdown of clawback and fees.

5. **Anomaly Detection F1:**
   - *Current UI label:* "Anomaly Detection F1 = 1.000"
   - *Defect:* Misleading assertion derived by checking injector output against ground truth.
   - *Correct Name:* "Rule-engine conformance vs. ground truth", accompanied by hard-negative set evaluation.

---

## 4. Execution Readiness

With the audit complete and baseline metrics documented, implementation proceeds in strict sequence:
1. **Repo Hygiene & Tooling:** `.gitignore`, `.env.example`, `requirements.txt`, `pyproject.toml`, `Makefile`.
2. **Schema & Database Hardening:** Updated `schema.sql` with integer cents, HMAC token, event hashes, triggers, and CHECK constraints.
3. **Core Domain Hardening:** Decimal/cents math, cumulative proration, SoD, HMAC override verification in `core/`.
4. **Generator & Benchmark Overhaul:** Seeded PRNG, realistic distributions, hard negatives, isolated detections in `core/audit.py` and evaluation in `core/evaluate.py`.
5. **API Server Hardening:** Parameterized queries, RBAC headers, idempotency, `/api/meta/kpi-definitions`, `/api/ledger/verify`.
6. **Frontend Redesign:** Design tokens, Linear/Stripe aesthetic, react-router, react-query, virtualized tables, accessibility.
7. **Comprehensive Documentation & CI:** `docs/`, `README.md`, `.github/workflows/ci.yml`.
8. **Final Verification Gates:** All Section 8 acceptance criteria.
