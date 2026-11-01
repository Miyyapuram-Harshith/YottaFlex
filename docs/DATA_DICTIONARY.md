# ERL-RMA Canonical Data Dictionary

| Table | Field | Type | Required | Allowed Values | Units | Uniqueness | Validation Rule | FK Target | Cardinality |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: | :--- | :--- | :--- |
| `customers` | `customer_id` | `VARCHAR(20)` | Yes | CUST-YYYY-NNNNNN | Token | PK | Format regex | `None` | 1:N Orders |
| `customers` | `account_status` | `VARCHAR(16)` | Yes | ACTIVE, SUSPENDED, FLAGGED | Enum | No | IN list | `None` | N/A |
| `customers` | `loyalty_tier` | `VARCHAR(16)` | Yes | STANDARD, SILVER, GOLD, VIP | Enum | No | IN list | `None` | N/A |
| `customers` | `risk_score_basis_points` | `INT` | Yes | 0..10000 | Basis points | No | Between 0 and 10000 | `None` | N/A |
| `orders` | `order_id` | `VARCHAR(20)` | Yes | ORD-YYYY-NNNNNN | Token | PK | Format regex | `None` | 1:N OrderLines |
| `orders` | `shipping_fee_paid_cents` | `INT` | Yes | >= 0 | USD Cents | No | >= 0 | `None` | N/A |
| `orders` | `paid_total_cents` | `INT` | Yes | >= 0 | USD Cents | No | subtotal - discount + tax + shipping | `None` | N/A |
| `order_lines` | `order_line_id` | `VARCHAR(32)` | Yes | OL-ORD-YYYY-NNNNNN-PP | Token | PK | Format regex | `None` | 1:N ReturnLines |
| `order_lines` | `unit_price_cents` | `INT` | Yes | > 0 | USD Cents | No | > 0 | `None` | N/A |
| `order_lines` | `net_paid_amount_cents` | `INT` | Yes | >= 0 | USD Cents | No | line_sub - disc + tax | `None` | N/A |
| `return_requests` | `return_request_id` | `VARCHAR(20)` | Yes | RMA-REQ-YYYY-NNNNNN | Token | PK | Format regex | `None` | 1:1 RMA |
| `return_requests` | `override_token` | `VARCHAR(128)` | No | mgr:ts:hmac_hex | Crypto hash | No | HMAC-SHA256 valid | `None` | N/A |
| `return_lines` | `return_line_id` | `VARCHAR(36)` | Yes | RMAL-RMA-YYYY-NNNNNN-PP | Token | PK | Format regex | `None` | 1:1 Refund |
| `return_lines` | `resolution_type` | `VARCHAR(16)` | Yes | REFUND, EXCHANGE, STORE_CREDIT | Enum | No | IN list | `None` | N/A |
| `return_lines` | `exchange_order_id` | `VARCHAR(20)` | No | ORD-YYYY-NNNNNN | Token | No | FK to orders | `orders.order_id` | N:1 |
| `refunds` | `refund_id` | `VARCHAR(20)` | Yes | REF-YYYY-NNNNNN | Token | PK | Format regex | `None` | N/A |
| `refunds` | `shipping_refund_cents` | `INT` | Yes | >= 0 | USD Cents | No | Merchant fault only | `None` | N/A |
| `refunds` | `idempotency_key` | `VARCHAR(64)` | Yes | IDEMP-REF-... | Token | Unique | Unique index | `None` | N/A |
| `entity_state_events` | `seq` | `INT` | Yes | >= 1 | Counter | Per entity | Monotonic | `None` | N/A |
| `entity_state_events` | `prev_event_hash` | `VARCHAR(64)` | No | SHA-256 hex | Hash | No | Prior event hash | `None` | N/A |
| `entity_state_events` | `event_hash` | `VARCHAR(64)` | Yes | SHA-256 hex | Hash | Yes | SHA-256 over row canonical JSON | `None` | N/A |
