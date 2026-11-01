<p align="center">
  <img src="../public/logo.png" alt="YottaFlex.ai" width="360" />
</p>

# ERL-RMA: Enterprise Reverse Logistics, RMA Governance & Synthetic Benchmark Engine

[![Compliance](https://img.shields.io/badge/ISO%2FIEC%2FIEEE-29148%3A2018-blue.svg)](#)
[![Python](https://img.shields.io/badge/Python-3.8%2B%20(Zero--Dependency)-success.svg)](#)
[![Database](https://img.shields.io/badge/Schema-ANSI%20SQL%20%2F%20PostgreSQL%203NF-informational.svg)](#)
[![Reproducibility](https://img.shields.io/badge/SHA--256-Bit--for--Bit%20Deterministic-orange.svg)](#)
[![License](https://img.shields.io/badge/License-MIT%20%2F%20Apache--2.0-lightgrey.svg)](#)

## 1. Executive Overview

**ERL-RMA** is an enterprise-grade reference architecture, relational database schema, and deterministic synthetic data generation engine designed to govern end-to-end omnichannel post-purchase workflows. 

High-volume retail operations frequently suffer from margin erosion caused by disconnected Order Management Systems (OMS), Warehouse Management Systems (WMS), and ERP financial ledgers. ERL-RMA resolves these vulnerabilities by enforcing an event-sourced, zero-trust state machine across **Order Capture $\rightarrow$ Return Eligibility Adjudication $\rightarrow$ Return Merchandise Authorization (RMA) $\rightarrow$ Reverse Carrier Telemetry $\rightarrow$ Physical Warehouse Inspection $\rightarrow$ Prorated Financial Settlement $\rightarrow$ Inventory Disposition**.

In addition to formal system specifications, this repository provides a **Zero-Dependency Deterministic Benchmark Generator (`erl_rma_benchmark.py`)** that synthesizes **30,000 orders, 5,000 return requests, and 8,000 return lines** with mathematically verified penny-reconciliation and isolated ground-truth anomaly injection for automated QA auditing and Machine Learning fraud-detection benchmarking.

---

## 2. Core Architectural Capabilities

* **Strict Relational & Lifecycle Traceability:** Enforces 3rd Normal Form (3NF) referential integrity across 10 core operational tables plus an immutable, append-only state audit ledger (`entity_state_events`).
* **Deterministic Nomenclature & Immutable IDs:** Generates zero-padded, human-auditable keys (`ORD-2026-000001`, `RMA-2026-000001`, `RMAL-RMA-2026-000001-01`, `RTS-2026-000001`, `REF-2026-000001`).
* **Policy & Override Governance:** Evaluates item-level category exclusions (`FINAL_SALE`, `HAZMAT`), dynamic return windows (`15` days for `ELECTRONICS`, `30` days for `APPAREL`/`HOME`), and historical unreturned quantities, requiring explicit `MGR-XXX` role authorization for policy overrides.
* **Penny-Exact Prorated Refund Engine:** Calculates line-item refunds by prorating order-level promotional discounts (`discount_clawback`) and jurisdiction taxes (`tax_refund_amount`), applying conditional `15%` restocking fees on open-box discretionary returns while waiving fees for `VIP` loyalty tiers.
* **Zero-Leakage Ground-Truth Anomaly Injection:** Injects `250` controlled operational and financial anomalies across 5 failure classes into operational tables while isolating all ground-truth labels inside `ground_truth.json` and `ground_truth.csv`.
* **Cryptographic Reproducibility:** Guarantees bit-for-bit identical output across independent executions using fixed pseudo-random seed initialization (`--seed 20261022`) and canonical SHA-256 dataset verification.

---

## 3. Repository & Artifact Directory Structure

```text
erl-rma-benchmark/
├── README.md                          # Project documentation, setup, and architecture guide
├── docs/
│   ├── SRS_ISO_29148_ERL_RMA.md       # Complete ISO/IEC/IEEE 29148:2018 System Specification
│   ├── DATA_DICTIONARY.md             # Granular field-level rules, constraints, and cardinalities
│   └── PROMPT_ENGINEERING_LOG.md      # Multi-phase architectural prompt execution log
├── sql/
│   └── schema_ddl.sql                 # Production ANSI SQL / PostgreSQL 3NF DDL & constraints
├── src/
│   └── erl_rma_benchmark.py           # Zero-dependency generator, validator & SHA-256 verifier
└── erl_rma_export/                    # Generated benchmark artifacts (via --seed 20261022)
    ├── customers.csv                  # Master customer accounts, tiers & risk scores (10,000 rows)
    ├── orders.csv                     # Master order headers & financial totals (30,000 rows)
    ├── order_lines.csv                # Purchased SKUs, windows & net paid amounts (54,921 rows)
    ├── return_requests.csv            # Customer return requests & override metadata (5,000 rows)
    ├── return_lines.csv               # Line-level return quantities & eligibility (8,000 rows)
    ├── return_authorizations.csv      # Issued RMAs & expiration timestamps (4,218 rows)
    ├── return_shipments.csv           # Reverse carrier tracking & WH receipt timestamps (4,218 rows)
    ├── inspections.csv                # Warehouse operator physical condition grades (6,642 rows)
    ├── refunds.csv                    # Prorated financial disbursements & fee ledger (6,692 rows)
    ├── inventory_dispositions.csv     # Physical warehouse routing (RESTOCK/REFURBISH/QUARANTINE/SCRAP)
    ├── entity_state_events.csv        # Append-only state transition audit trail (25,128 rows)
    ├── ground_truth.csv               # Isolated anomaly labels (CSV format - 250 rows)
    ├── ground_truth.json              # Isolated anomaly labels (JSON format - 250 objects)
    └── validation_summary.json        # Automated QA audit report & SHA-256 reproducibility proof
```

---

## 4. Relational Schema & Nomenclature Summary

| Entity / Table | Primary Key Format | Parent Foreign Key(s) | Cardinality | Primary Domain Responsibility |
| --- | --- | --- | --- | --- |
| `customers` | `CUST-2026-000001` | *None (Master)* | `1 : N` (`orders`) | Loyalty tiering (`STANDARD`..`VIP`), account status & risk scoring |
| `orders` | `ORD-2026-000001` | `customer_id` | `1 : N` (`order_lines`) | Order lifecycle dates and header-level financial reconciliation |
| `order_lines` | `ORDL-ORD-2026-000001-01` | `order_id` | `1 : N` (`return_lines`) | SKU category rules, return window days (`0, 15, 30`), tax & discounts |
| `return_requests` | `REQ-2026-000001` | `order_id`, `customer_id` | `1 : N` (`return_lines`) | Return initiation, `REFUND`/`EXCHANGE` tender, manager override flags |
| `return_lines` | `RMAL-RMA-2026-000001-01` | `return_request_id`, `order_line_id` | `1 : N` (`inspections`) | Requested vs. approved quantities, return reason & eligibility status |
| `return_authorizations` | `RMA-2026-000001` | `return_request_id` | `1 : 1` (Optional) | RMA issuance governance, 14-day expiration window & RMA status |
| `return_shipments` | `RTS-2026-000001` | `rma_id` | `1 : N` | Carrier telemetry (`UPS`, `FEDEX`, `DHL`, `USPS`), transit & WH receipt |
| `inspections` | `INSP-2026-000001` | `return_line_id`, `shipment_id` | `1 : 1` (`dispositions`) | Operator physical grading (`GRADE_A_NEW`..`FRAUD_MISMATCH`) |
| `refunds` | `REF-2026-000001` | `rma_id`, `return_line_id` | `1 : N` | Prorated GMV, discount clawback, tax refund, restocking fee & payout |
| `inventory_dispositions` | `DISP-2026-000001` | `inspection_id`, `return_line_id` | `1 : 1` | Physical bin routing (`RESTOCK`, `REFURBISH`, `QUARANTINE`, `SCRAP`) |
| `entity_state_events` | `EVT-2026-0000001` | Polymorphic (`entity_id`) | `N : 1` | Immutable append-only audit log of all state transitions |

---

## 5. Quickstart & CLI Execution Guide

### 5.1 Prerequisites

The benchmark engine is written in pure Python (`>= 3.8`) using **zero external third-party packages** (`csv`, `json`, `hashlib`, `random`, `datetime`, `argparse`), ensuring immediate execution in air-gapped enterprise environments or CI/CD runners.

### 5.2 Generate the Full Benchmark Dataset (`scale=1.0`)

Execute the generator with the default deterministic seed (`20261022`) to synthesize the complete `30,000` order / `5,000` return request / `8,000` return line dataset, run the automated validation suite, and verify dual-run SHA-256 reproducibility:

```bash
python3 src/erl_rma_benchmark.py \
  --seed 20261022 \
  --scale 1.0 \
  --out ./erl_rma_export
```

### 5.3 Generate the Starter / CI Test Dataset (`scale=0.1`)

To generate a lightweight `10%` starter dataset (`3,000` orders, `500` return requests, `800` return lines) using the exact same generation logic and anomaly distribution ratios:

```bash
python3 src/erl_rma_benchmark.py \
  --seed 20261022 \
  --scale 0.1 \
  --out ./erl_rma_starter
```

### 5.4 Deploy Relational Schema & Load Seed Data (PostgreSQL)

```bash
psql -U postgres -d erl_rma_db -f sql/schema_ddl.sql

# Load operational CSV tables in parent-first topological order
for tbl in customers orders order_lines return_requests return_authorizations \
           return_lines return_shipments inspections refunds inventory_dispositions; do
    psql -U postgres -d erl_rma_db -c "\COPY ${tbl} FROM './erl_rma_export/${tbl}.csv' WITH CSV HEADER;"
done
```

---

## 6. Injected Edge Cases & Ground-Truth Benchmark Taxonomy

To evaluate automated audit engines, business-rule validators, and anomaly-detection models, `erl_rma_benchmark.py` injects **5 distinct failure modes** (`50` instances each at `scale=1.0`; `250` total anomalies). Operational tables contain no anomaly indicator columns; ground truth is strictly segregated inside `ground_truth.json` and `ground_truth.csv`.

| Ground-Truth `issue_type` | Target Table | Violated Domain Invariant | Expected Audit / Mitigation Decision | Injected Count (`scale=1.0`) |
| --- | --- | --- | --- | --- |
| `ANOM_QTY_EXCEEDS_PURCHASED` | `return_lines` | `approved_qty > OrderLine.purchased_qty` | `REJECT_ELIGIBILITY_QTY_OVERFLOW` | `50` |
| `ANOM_LATE_RETURN_NO_OVERRIDE` | `return_requests` | `(request_date - delivery_date) > return_window_days` with `policy_override_flag = false` | `REVOKE_RMA_POLICY_VIOLATION` | `50` |
| `ANOM_RESTOCK_BEFORE_INSP` | `inventory_dispositions` | `disposed_at < Inspection.inspected_at` with `disposition_action = 'RESTOCK'` | `QUARANTINE_PREMATURE_RESTOCK` | `50` |
| `ANOM_REFUND_EXCEEDS_PAID` | `refunds` | `net_refund_amount > OrderLine.net_paid_amount` (missing discount clawback) | `BLOCK_PAYOUT_ARITHMETIC_MISMATCH` | `50` |
| `ANOM_DUPLICATE_REFUND` | `refunds` | Multiple `PROCESSED` refund records referencing the same `return_line_id` | `BLOCK_DUPLICATE_DISBURSEMENT` | `50` |

---

## 7. Automated Validation & Reproducibility Proof

Every execution of `erl_rma_benchmark.py` performs an internal two-pass generation check (`sha256_run1 == sha256_run2`) and executes `run_validation_suite()` across all generated tables before writing `validation_summary.json`:

1. **Primary & Foreign Key Integrity:** Confirms `100%` uniqueness on primary keys and `0` orphaned foreign key references across all 11 tables.
2. **Header-to-Line Financial Reconciliation:** Verifies that `Order.paid_total == SUM(OrderLine.net_paid_amount)` across all `30,000` orders with `0.00` penny drift.
3. **Chronological State Ordering:** Validates monotonic timestamp progression (`created_at <= order_date <= delivery_date <= request_date <= authorized_at <= shipped_at <= received_at <= inspected_at <= disposed_at`) across all non-anomalous lifecycles.
4. **100% Anomaly Recall & Zero Unlabelled Errors:** Confirms that the audit validator detects all `250` injected ground-truth anomalies (`verified_labelled_anomalies: 250`) while recording `unexplained_integrity_errors: 0` across clean baseline records.

---

## 8. Data Provenance, Privacy & Lawful Use Declaration

* **Synthetic Provenance:** `100%` of records in this repository are algorithmically synthesized from first-principles domain rules using Python's deterministic Mersenne Twister PRNG (`random.Random(20261022)`).
* **Zero PII / GDPR / DPDP Compliance:** No real-world customer names, street addresses, payment card numbers, carrier tracking numbers, or proprietary retail logs were accessed, scraped, or included.
* **Schema Attribution:** Entity lifecycle patterns and retail accounting rules are conceptually aligned with public ISO/IEC/IEEE 29148:2018 Systems Engineering standards and public NRF/ARTS Operational Data Model conventions.
* **License:** Released under dual **MIT / Apache-2.0 License** for unrestricted academic, enterprise QA, and machine-learning benchmark distribution.

