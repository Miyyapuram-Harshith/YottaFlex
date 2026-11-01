# ERL-RMA Lifecycle State Machine Specification

## 1. Overview
The Enterprise Reverse Logistics & Return Merchandise Authorization (ERL-RMA) lifecycle models the end-to-end traversal of returned items from initial customer request through receipt, physical inspection, disposition routing, and final financial settlement.

All state transitions are strictly sequential, validated against state machines, and recorded in the append-only `entity_state_events` audit ledger with cryptographic SHA-256 hash chains.

---

## 2. Entity State Machines

### 2.1 ReturnRequest Lifecycle
```
                 ┌──────────────┐
                 │  SUBMITTED   │
                 └──────┬───────┘
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     ┌─────────────┐         ┌──────────────┐
     │  APPROVED   │         │   REJECTED   │
     └──────┬──────┘         └──────────────┘
            │
            ▼
     ┌─────────────┐
     │  CANCELLED  │ (Optional before shipment)
     └─────────────┘
```
- **SUBMITTED**: Customer initiated return request with reason and quantities.
- **APPROVED**: Automated eligibility engine passed Priorities 1–5 or valid manager HMAC override verified.
- **REJECTED**: Request failed policy check (hazard item, out-of-window, quantity exceeded).
- **CANCELLED**: Return cancelled by customer prior to carrier scan.

---

### 2.2 ReturnShipment Lifecycle
```
                 ┌──────────────┐
                 │   LABEL_GEN  │
                 └──────┬───────┘
                        │ Carrier scan
                        ▼
                 ┌──────────────┐
                 │  IN_TRANSIT  │
                 └──────┬───────┘
                        │ Dock receipt scan
                        ▼
                 ┌──────────────┐
                 │  DELIVERED   │
                 └──────────────┘
```
- **LABEL_GEN**: Return authorization issued and shipping label generated.
- **IN_TRANSIT**: Carrier has accepted package into network.
- **DELIVERED**: Carrier delivered package to return processing facility dock.

---

### 2.3 Inspection Lifecycle
```
                 ┌──────────────┐
                 │   PENDING    │
                 └──────┬───────┘
                        │ Warehouse tech graded
                        ▼
                 ┌──────────────┐
                 │  COMPLETED   │
                 └──────────────┘
```
- **PENDING**: Package received at facility; awaiting grading and functional testing.
- **COMPLETED**: Line-level grading applied (`GRADE_A_NEW`, `GRADE_B_OPEN_BOX`, `GRADE_C_DAMAGED`, `FRAUD_MISMATCH`).

---

### 2.4 Inventory Disposition Routing
Physical item routing is conditioned on inspection condition grade and customer return tier:

| Grade | Routing Destination | Action | Restocking Fee |
| :--- | :--- | :--- | :--- |
| `GRADE_A_NEW` | Active Primary Warehouse | `RESTOCK` | 0% |
| `GRADE_B_OPEN_BOX` | Refurbishment / Outlet Annex | `REFURBISH` | 15% |
| `GRADE_C_DAMAGED` | Salvage Quarantine | `QUARANTINE` | 0% |
| `FRAUD_MISMATCH` | Asset Protection / Scrap | `SCRAP` | 100% deduction ($0 refund) |

**Invariant Guard**: Disposition action `RESTOCK` is strictly prohibited before physical inspection is completed (`disposed_at >= inspected_at`). Violation is flagged as `ANOM_RESTOCK_BEFORE_INSP`.

---

### 2.5 Refund Settlement Lifecycle
```
                 ┌──────────────┐
                 │   PENDING    │
                 └──────┬───────┘
                        │ Payment processor execution
                        ▼
                 ┌──────────────┐
                 │  PROCESSED   │
                 └──────┬───────┘
                        │ (Optional downstream exception)
                        ▼
                 ┌──────────────┐
                 │    FAILED    │
                 └──────────────┘
```
- **PENDING**: Settlement calculated by fixed-point cumulative remainder engine.
- **PROCESSED**: Refund transaction posted to customer ledger.
- **FAILED**: Processor transaction declined (invalid card token, expired account).

---

## 3. Segregation of Duties (SoD) Rules
To prevent collusion and fraud in returns handling, the following role constraints are strictly enforced:
1. **Adjudication vs. Inspection**: A Customer Support Representative (`CSR-*`) who approves a return authorization cannot execute the physical inspection (`TECH-*`).
2. **Adjudication vs. Override**: A standard agent (`CSR-*`) cannot approve policy overrides (`MGR-*` HMAC signature required).
3. **Refund Processing**: Automated batch processors (`PROC-*`) or finance managers execute refunds; warehouse technicians cannot issue ledger payouts.

---

## 4. Compensating Remediations
Because `entity_state_events` and historical accounting records are immutable:
- Historical states and timestamps are **never modified or deleted**.
- If an operational defect or fraud is detected (e.g., duplicate refund or unauthorized override), a **compensating transaction** is posted (`REMEDIATION_HOLD`, `CHARGEBACK_INITIATED`, or `CREDIT_MEMO`) referencing the original entity identifier.
