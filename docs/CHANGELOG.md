# Changelog

All notable changes to the YottaFlex ERL-RMA platform are documented in this file.

---

## [2.0.0] - Production Hardening & Redesign

### Added
- **Fixed-Point Financial Engine (`core/financial.py`)**:
  - Exact integer cents representations for all monetary amounts.
  - Cumulative remainder discount and tax proration algorithm with zero penny drift.
  - Banker's Rounding (`decimal.ROUND_HALF_EVEN`).
  - Strict global ledger invariant checking (`sum(net_refund) <= net_paid + shipping`).
- **Cryptographic Override Verification (`core/adjudication.py`)**:
  - HMAC-SHA256 signature token generator and verifier for manager overrides.
  - Strict Priority 1–5 adjudication hierarchy with exact day-boundary semantics.
- **Append-Only Immutable Event Ledger (`schema.sql`)**:
  - Monotonic `seq`, `prev_event_hash`, and `event_hash` SHA-256 chain.
  - SQLite triggers preventing `UPDATE` and `DELETE` on `entity_state_events`.
  - SQLite trigger preventing cumulative over-refunds on `refunds`.
- **Independent Rule-Engine Detector (`core/audit.py`)**:
  - Pure rule-based heuristic auditing with zero references to ground truth.
  - Evaluator decoupled into `core/evaluate.py`.
- **Benchmark Generator (`erl_rma_benchmark.py`)**:
  - Deterministic PRNG seeding (`20261022`) and sub-seed derivation.
  - Multi-line orders, category-conditional reasons, log-normal basket sizing.
  - Hard-negative (`VALID_BOUNDARY`) generation ($\ge 300$, actual $1,112$).
  - Full dataset export with 11 CSVs, JSON mirrors, `seed.sql`, `MANIFEST.json`, `data_dictionary.csv`, and `validation_summary.json`.
- **Hardened API Server (`api_server.py`)**:
  - Parameterized SQLite queries and table allowlist.
  - Standardized JSON error envelopes: `{"error": {"code", "message", "details"}}`.
  - Endpoint `GET /api/meta/kpi-definitions` with documented formulas.
  - Endpoint `GET /api/ledger/verify` for cryptographically verifying event hash chains.
  - Endpoint `POST /api/refunds` with strict `Idempotency-Key` header enforcement.
  - Role-based header checks (`X-Actor-Role`, `X-Actor-Id`).
- **Restrained Linear/Stripe-Grade Frontend (`src/`)**:
  - Modern design tokens (`src/styles/tokens.css`) with light/dark theme support.
  - Standard en-US currency formatting (`Intl.NumberFormat('en-US', ...)`) everywhere.
  - Hamilton-Hare largest-remainder distribution ensuring disposition percentages sum to exactly 100.0%.
  - Virtualized tables for large datasets using `@tanstack/react-virtual`.
  - Master/detail inspection workbench with worked arithmetic decision simulator.
  - Cryptographic event chain verification badge and hash inspector.
  - Data explorer with multi-table pagination and CSV export.
- **Continuous Integration (`.github/workflows/ci.yml`)**:
  - Automated tests, linting, type checks, and reproducibility checks.

### Changed
- Converted all floating-point monetary columns to integer cents.
- Replaced hardcoded disposition percentages (76/6/14/4) with dynamic largest-remainder allocations.
- Fixed return window expiration definition: Day $W$ is eligible, Day $W+1$ is late.
- Removed all fabricated claims, marketing badges, and unbacked assertions.

### Fixed
- Fixed Indian digit grouping currency display (`$3,13,54,083.38` $\to$ `$31,354,083.38`).
- Fixed missing trailing zero on currency strings (`$24,00,944.5` $\to$ `$2,400,944.50`).
- Fixed cumulative proration drift across split returned quantities.
- Fixed ground truth leakage into operational detector.

