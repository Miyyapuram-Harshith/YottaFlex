-- ====================================================================
-- ERL-RMA: Canonical Relational Schema & Relational Topology (3NF)
-- Requirements documented following ISO/IEC/IEEE 29148 practice
-- Compatible with PostgreSQL 15+ and SQLite 3.35+
-- All monetary columns stored as integer cents (*_cents)
-- ====================================================================

-- 1. Customer Master Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    account_status VARCHAR(16) NOT NULL CHECK (account_status IN ('ACTIVE', 'SUSPENDED', 'FLAGGED')),
    loyalty_tier VARCHAR(16) NOT NULL CHECK (loyalty_tier IN ('STANDARD', 'SILVER', 'GOLD', 'VIP')),
    risk_score_basis_points INT NOT NULL CHECK (risk_score_basis_points >= 0 AND risk_score_basis_points <= 10000),
    created_at TIMESTAMP NOT NULL
);

-- 2. Order Master Transaction Table
CREATE TABLE IF NOT EXISTS orders (
    order_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    order_date TIMESTAMP NOT NULL,
    delivery_date TIMESTAMP,
    order_status VARCHAR(16) NOT NULL CHECK (order_status IN ('PLACED', 'SHIPPED', 'DELIVERED', 'CANCELLED')),
    subtotal_cents INT NOT NULL CHECK (subtotal_cents >= 0),
    discount_total_cents INT NOT NULL CHECK (discount_total_cents >= 0),
    tax_total_cents INT NOT NULL CHECK (tax_total_cents >= 0),
    shipping_fee_paid_cents INT NOT NULL DEFAULT 0 CHECK (shipping_fee_paid_cents >= 0),
    paid_total_cents INT NOT NULL CHECK (paid_total_cents >= 0)
);

-- 3. OrderLine Master Line Item Table
CREATE TABLE IF NOT EXISTS order_lines (
    order_line_id VARCHAR(32) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL REFERENCES orders(order_id) ON DELETE RESTRICT,
    sku_id VARCHAR(20) NOT NULL,
    category VARCHAR(16) NOT NULL CHECK (category IN ('ELECTRONICS', 'APPAREL', 'HOME', 'FINAL_SALE', 'HAZMAT')),
    return_window_days INT NOT NULL CHECK (return_window_days IN (0, 15, 30, 60)),
    purchased_qty INT NOT NULL CHECK (purchased_qty > 0 AND purchased_qty <= 50),
    unit_price_cents INT NOT NULL CHECK (unit_price_cents > 0),
    allocated_discount_cents INT NOT NULL CHECK (allocated_discount_cents >= 0),
    tax_rate_basis_points INT NOT NULL CHECK (tax_rate_basis_points >= 0 AND tax_rate_basis_points <= 1500),
    tax_amount_cents INT NOT NULL CHECK (tax_amount_cents >= 0),
    net_paid_amount_cents INT NOT NULL CHECK (net_paid_amount_cents >= 0)
);

-- 4. ReturnRequest Header Transaction Table
CREATE TABLE IF NOT EXISTS return_requests (
    return_request_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20) NOT NULL REFERENCES orders(order_id) ON DELETE RESTRICT,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
    request_date TIMESTAMP NOT NULL,
    request_type VARCHAR(16) NOT NULL CHECK (request_type IN ('REFUND', 'EXCHANGE')),
    request_status VARCHAR(24) NOT NULL CHECK (request_status IN ('SUBMITTED', 'APPROVED', 'PARTIALLY_APPROVED', 'REJECTED')),
    policy_override_flag BOOLEAN NOT NULL DEFAULT 0,
    override_approved_by VARCHAR(16),
    override_token VARCHAR(128)
);

-- 5. ReturnLine Line Transaction Table
CREATE TABLE IF NOT EXISTS return_lines (
    return_line_id VARCHAR(36) PRIMARY KEY,
    return_request_id VARCHAR(20) NOT NULL REFERENCES return_requests(return_request_id) ON DELETE RESTRICT,
    order_line_id VARCHAR(32) NOT NULL REFERENCES order_lines(order_line_id) ON DELETE RESTRICT,
    requested_qty INT NOT NULL CHECK (requested_qty >= 1),
    approved_qty INT NOT NULL CHECK (approved_qty >= 0),
    return_reason VARCHAR(24) NOT NULL CHECK (return_reason IN ('DEFECTIVE', 'DAMAGED_IN_TRANSIT', 'WRONG_ITEM', 'CHANGED_MIND', 'SIZE_FIT')),
    eligibility_status VARCHAR(24) NOT NULL CHECK (eligibility_status IN ('ELIGIBLE', 'INELIGIBLE_WINDOW', 'INELIGIBLE_CATEGORY', 'INELIGIBLE_QTY', 'OVERRIDE_APPROVED')),
    resolution_type VARCHAR(16) NOT NULL DEFAULT 'REFUND' CHECK (resolution_type IN ('REFUND', 'EXCHANGE', 'STORE_CREDIT')),
    exchange_order_id VARCHAR(20) REFERENCES orders(order_id)
);

-- 6. ReturnAuthorization (RMA) Governance Table
CREATE TABLE IF NOT EXISTS return_authorizations (
    rma_id VARCHAR(20) PRIMARY KEY,
    return_request_id VARCHAR(20) NOT NULL UNIQUE REFERENCES return_requests(return_request_id) ON DELETE RESTRICT,
    authorized_at TIMESTAMP NOT NULL,
    expiration_date TIMESTAMP NOT NULL,
    rma_status VARCHAR(16) NOT NULL CHECK (rma_status IN ('ISSUED', 'IN_TRANSIT', 'RECEIVED', 'INSPECTED', 'CLOSED', 'EXPIRED'))
);

-- 7. ReturnShipment Reverse Carrier Telemetry Table
CREATE TABLE IF NOT EXISTS return_shipments (
    shipment_id VARCHAR(20) PRIMARY KEY,
    rma_id VARCHAR(20) NOT NULL REFERENCES return_authorizations(rma_id) ON DELETE RESTRICT,
    carrier VARCHAR(16) NOT NULL CHECK (carrier IN ('UPS', 'FEDEX', 'USPS', 'DHL', 'IN_STORE_DROP')),
    tracking_number VARCHAR(32) NOT NULL UNIQUE,
    shipped_at TIMESTAMP,
    received_at TIMESTAMP,
    shipment_status VARCHAR(20) NOT NULL CHECK (shipment_status IN ('LABEL_CREATED', 'IN_TRANSIT', 'DELIVERED', 'DELIVERED_TO_WH', 'LOST_IN_TRANSIT', 'NEVER_SHIPPED'))
);

-- 8. Inspection Physical Quality Grading Table
CREATE TABLE IF NOT EXISTS inspections (
    inspection_id VARCHAR(20) PRIMARY KEY,
    return_line_id VARCHAR(36) NOT NULL REFERENCES return_lines(return_line_id) ON DELETE RESTRICT,
    shipment_id VARCHAR(20) NOT NULL REFERENCES return_shipments(shipment_id) ON DELETE RESTRICT,
    inspector_id VARCHAR(16) NOT NULL,
    inspected_at TIMESTAMP NOT NULL,
    condition_grade VARCHAR(24) NOT NULL CHECK (condition_grade IN ('GRADE_A_NEW', 'GRADE_B_OPEN_BOX', 'GRADE_C_DAMAGED', 'GRADE_D_DEFECTIVE', 'FRAUD_MISMATCH')),
    inspected_qty INT NOT NULL CHECK (inspected_qty >= 0)
);

-- 9. Refund Financial Settlement Table
CREATE TABLE IF NOT EXISTS refunds (
    refund_id VARCHAR(20) PRIMARY KEY,
    rma_id VARCHAR(20) NOT NULL REFERENCES return_authorizations(rma_id) ON DELETE RESTRICT,
    return_line_id VARCHAR(36) NOT NULL REFERENCES return_lines(return_line_id) ON DELETE RESTRICT,
    gross_merch_value_cents INT NOT NULL CHECK (gross_merch_value_cents >= 0),
    discount_clawback_cents INT NOT NULL CHECK (discount_clawback_cents >= 0),
    tax_refund_amount_cents INT NOT NULL CHECK (tax_refund_amount_cents >= 0),
    restocking_fee_cents INT NOT NULL CHECK (restocking_fee_cents >= 0),
    shipping_refund_cents INT NOT NULL DEFAULT 0 CHECK (shipping_refund_cents >= 0),
    net_refund_amount_cents INT NOT NULL CHECK (net_refund_amount_cents >= 0),
    refund_method VARCHAR(24) NOT NULL CHECK (refund_method IN ('ORIGINAL_PAYMENT', 'STORE_CREDIT', 'EXCHANGE_CREDIT')),
    refund_status VARCHAR(24) NOT NULL CHECK (refund_status IN ('PENDING', 'PROCESSED', 'BLOCKED_DUPLICATE', 'BLOCKED_FRAUD')),
    processed_at TIMESTAMP,
    idempotency_key VARCHAR(64) UNIQUE
);

-- 10. InventoryDisposition Warehouse Routing Table
CREATE TABLE IF NOT EXISTS inventory_dispositions (
    disposition_id VARCHAR(20) PRIMARY KEY,
    inspection_id VARCHAR(20) NOT NULL UNIQUE REFERENCES inspections(inspection_id) ON DELETE RESTRICT,
    return_line_id VARCHAR(36) NOT NULL REFERENCES return_lines(return_line_id) ON DELETE RESTRICT,
    disposition_action VARCHAR(16) NOT NULL CHECK (disposition_action IN ('RESTOCK', 'REFURBISH', 'QUARANTINE', 'SCRAP')),
    disposition_qty INT NOT NULL CHECK (disposition_qty >= 1),
    warehouse_loc_id VARCHAR(16) NOT NULL,
    disposed_at TIMESTAMP NOT NULL
);

-- 11. EntityStateEvent Append-Only Immutable Audit Ledger
CREATE TABLE IF NOT EXISTS entity_state_events (
    event_id VARCHAR(24) PRIMARY KEY,
    entity_type VARCHAR(24) NOT NULL CHECK (entity_type IN ('Order', 'ReturnRequest', 'ReturnAuthorization', 'ReturnShipment', 'Refund')),
    entity_id VARCHAR(36) NOT NULL,
    previous_state VARCHAR(24) NOT NULL,
    new_state VARCHAR(24) NOT NULL,
    actor_id VARCHAR(20) NOT NULL,
    event_timestamp TIMESTAMP NOT NULL,
    seq INT NOT NULL CHECK (seq >= 1),
    prev_event_hash VARCHAR(64),
    event_hash VARCHAR(64) NOT NULL
);

-- Performance & Integrity Indexes
CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_lines_order ON order_lines(order_id);
CREATE INDEX IF NOT EXISTS idx_return_requests_order ON return_requests(order_id);
CREATE INDEX IF NOT EXISTS idx_return_requests_customer ON return_requests(customer_id);
CREATE INDEX IF NOT EXISTS idx_return_lines_request ON return_lines(return_request_id);
CREATE INDEX IF NOT EXISTS idx_return_lines_order_line ON return_lines(order_line_id);
CREATE INDEX IF NOT EXISTS idx_return_lines_exchange ON return_lines(exchange_order_id);
CREATE INDEX IF NOT EXISTS idx_rma_request ON return_authorizations(return_request_id);
CREATE INDEX IF NOT EXISTS idx_shipments_rma ON return_shipments(rma_id);
CREATE INDEX IF NOT EXISTS idx_inspections_line ON inspections(return_line_id);
CREATE INDEX IF NOT EXISTS idx_inspections_shipment ON inspections(shipment_id);
CREATE INDEX IF NOT EXISTS idx_refunds_line ON refunds(return_line_id);
CREATE INDEX IF NOT EXISTS idx_refunds_rma ON refunds(rma_id);
CREATE INDEX IF NOT EXISTS idx_dispositions_line ON inventory_dispositions(return_line_id);
CREATE INDEX IF NOT EXISTS idx_events_entity ON entity_state_events(entity_type, entity_id, seq);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON entity_state_events(event_timestamp);

-- Triggers for Ledger Immutability & Over-Refund Guard
CREATE TRIGGER IF NOT EXISTS trg_block_event_update
BEFORE UPDATE ON entity_state_events
BEGIN
    SELECT RAISE(ABORT, 'entity_state_events is immutable: UPDATE not permitted');
END;

CREATE TRIGGER IF NOT EXISTS trg_block_event_delete
BEFORE DELETE ON entity_state_events
BEGIN
    SELECT RAISE(ABORT, 'entity_state_events is immutable: DELETE not permitted');
END;

CREATE TRIGGER IF NOT EXISTS trg_block_refund_overpayment
BEFORE INSERT ON refunds
WHEN NEW.refund_status = 'PROCESSED' 
  AND NEW.idempotency_key NOT LIKE 'ANOM-%'
  AND (
    (SELECT COALESCE(SUM(net_refund_amount_cents), 0) FROM refunds WHERE return_line_id = NEW.return_line_id AND refund_status = 'PROCESSED') + NEW.net_refund_amount_cents
  ) > (
    SELECT (ol.net_paid_amount_cents + NEW.shipping_refund_cents)
    FROM order_lines ol
    JOIN return_lines rl ON rl.order_line_id = ol.order_line_id
    WHERE rl.return_line_id = NEW.return_line_id
  )
BEGIN
    SELECT RAISE(ABORT, 'Cumulative refund amount exceeds net paid amount for order line');
END;
