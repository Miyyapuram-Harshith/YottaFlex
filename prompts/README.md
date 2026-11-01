# System Architecture & Benchmark Prompts

This directory houses the formal engineering specification prompts and architectural blueprints governing the ERL-RMA (Enterprise Reverse Logistics & RMA Governance) platform and benchmark generator.

---

## Catalog of Prompts

| Specification File | Standard / Domain | Primary Purpose |
| :--- | :--- | :--- |
| [`ERL_RMA_BENCHMARK_SPEC.md`](./ERL_RMA_BENCHMARK_SPEC.md) | ISO/IEC/IEEE 29148:2018 | Complete reference architecture specification, relational 3NF schema, deterministic benchmark criteria, and ground-truth anomaly taxonomy. |

---

## Usage Guidelines

1. **Deterministic Benchmark Synthesis**:
   The rules, cardinalities, primary/foreign key naming conventions, and financial proration requirements detailed in [`ERL_RMA_BENCHMARK_SPEC.md`](./ERL_RMA_BENCHMARK_SPEC.md) serve as the formal specification executed by `erl_rma_benchmark.py`.
2. **Automated Audit & Conformance**:
   The 5 ground-truth anomaly failure modes specified in Section 6 define the evaluation baseline for independent audit rules (`core/audit.py`) and conformance scoring (`core/evaluate.py`).
3. **Database Schema Deployment**:
   Topological table loading orders and referential constraints in Section 4 and Section 5.4 guide both ANSI SQL / PostgreSQL deployments and local SQLite benchmark databases.
