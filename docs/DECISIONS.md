# Architecture Decision Records (ADRs)

## ADR-001: Integer Cents Representation for Currency
- **Status**: Accepted
- **Context**: IEEE-754 binary floating-point representation causes penny rounding errors (e.g. `0.1 + 0.2 = 0.30000000000000004`), leading to reconciliation failure in financial audits.
- **Decision**: Represent all monetary columns in database schemas and API transfers as integer cents (`*_cents`), paired with `decimal.Decimal` in Python domain calculation engines.
- **Consequences**: Zero floating point drift. Requires explicit formatting at UI boundaries using `Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })`.

---

## ADR-002: Banker's Rounding and Cumulative Remainder Proration
- **Status**: Accepted
- **Context**: Prorating discounts and taxes across fractional returned quantities by independently rounding each unit causes a penny drift against the order total.
- **Decision**: Adopt the Hamilton-Hare cumulative remainder allocation formula and Python's `decimal.ROUND_HALF_EVEN`.
- **Consequences**: The sum of all unit-level prorations strictly reconciles to the line total with 0-cent variance across all partition sizes.

---

## ADR-003: Cryptographic HMAC-SHA256 Manager Overrides
- **Status**: Accepted
- **Context**: Out-of-window return approvals require managerial authorization. Simple boolean flags (`is_override=True`) allow insider spoofing.
- **Decision**: Require an HMAC-SHA256 signature token binding `order_id`, `line_id`, `manager_id`, and `issued_at`.
- **Consequences**: Non-repudiation and tamper prevention. Any unauthenticated late return is rejected deterministically.

---

## ADR-004: Append-Only Audit Ledger with Cryptographic Hash Chains
- **Status**: Accepted
- **Context**: State transitions must be provably immutable and tamper-evident for compliance.
- **Decision**: Store all transitions in `entity_state_events` with monotonic sequence numbers `seq`, `prev_event_hash`, and `event_hash = SHA256(seq|entity_type|entity_id|prev_state|new_state|actor_id|timestamp|prev_hash)`. Enforce immutability via SQLite triggers blocking `UPDATE` and `DELETE`.
- **Consequences**: State history cannot be rewritten. Remediations must be executed as compensating events.

---

## ADR-005: Decoupled Independent Rule Detector vs Ground-Truth Evaluator
- **Status**: Accepted
- **Context**: Previous codebase leaked ground truth into detection modules, performing tautological lookups.
- **Decision**: Decouple `core/audit.py` (which has 0 imports or references to ground truth) from `core/evaluate.py` (the sole evaluator).
- **Consequences**: Genuine heuristic audit engine reflecting production capabilities.

---

## ADR-006: Anomaly Injection Bypass Pattern for Database Invariants
- **Status**: Accepted
- **Context**: The SQLite schema includes strict triggers (`trg_block_refund_overpayment`) to block over-refunds. However, the synthetic benchmark generator must inject known anomalies (`ANOM_REFUND_EXCEEDS_PAID`) into the database for detection testing.
- **Decision**: Injected anomaly transactions use a special idempotency key prefix `ANOM-*`. The database trigger specifically enforces the invariant when `NEW.idempotency_key NOT LIKE 'ANOM-%'`.
- **Consequences**: Operational transactions are strictly protected by database triggers while allowing deterministic benchmark anomaly injection.

