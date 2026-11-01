import React, { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams, useNavigate } from 'react-router-dom';
import { useVirtualizer } from '@tanstack/react-virtual';
import { api } from '../api/client';
import { formatCurrency, formatDate } from '../utils/formatters';
import { AdjudicateResponse, CalculateRefundResponse } from '../api/types';

interface ReturnRequestRow {
  return_request_id: string;
  order_id: string;
  customer_id: string;
  request_date: string;
  request_type: string;
  request_status: string;
  policy_override_flag: boolean | number;
  override_approved_by: string;
  override_token?: string;
}

export const WorkbenchPage: React.FC = () => {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();

  const [statusFilter, setStatusFilter] = useState('ALL');
  const [selectedId, setSelectedId] = useState<string>(id || 'RMA-REQ-2026-000001');

  // Decision Simulator state
  const [simCategory, setSimCategory] = useState('APPAREL');
  const [simReason, setSimReason] = useState('CHANGED_MIND');
  const [simDays, setSimDays] = useState(14);
  const simWindow = 30;
  const simPurchasedQty = 2;
  const simRequestedQty = 1;
  const simUnitPrice = '80.00';
  const simDiscount = '15.00';
  const simTax = '11.60';
  const simPaid = '156.60';
  const [simOverride, setSimOverride] = useState(false);
  const [simGrade, setSimGrade] = useState('GRADE_A_NEW');
  const simTier = 'STANDARD';

  // Adjudication simulation results
  const [adjResult, setAdjResult] = useState<AdjudicateResponse | null>(null);
  const [refResult, setRefResult] = useState<CalculateRefundResponse | null>(null);

  // Fetch return requests
  const { data: reqData, isLoading } = useQuery({
    queryKey: ['table', 'return_requests'],
    queryFn: () => api.getTable<ReturnRequestRow>('return_requests', 1, 100),
  });

  // Fetch selected entity details
  const { data: entityData } = useQuery({
    queryKey: ['entity', 'returnrequest', selectedId],
    queryFn: () => api.getEntity('returnrequest', selectedId),
    enabled: Boolean(selectedId),
  });

  const allRows: ReturnRequestRow[] = reqData?.data || reqData?.records || [];
  const filteredRows = allRows.filter(r => {
    if (statusFilter === 'ALL') return true;
    return r.request_status === statusFilter;
  });

  useEffect(() => {
    if ((!selectedId || !filteredRows.some(r => r.return_request_id === selectedId)) && filteredRows.length > 0) {
      setSelectedId(filteredRows[0].return_request_id);
    }
  }, [filteredRows, selectedId]);

  // Virtualizer for master table
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredRows.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 5,
  });

  const handleSelectRow = (reqId: string) => {
    setSelectedId(reqId);
    navigate(`/returns/${reqId}`, { replace: true });
  };

  const handleSimulate = async () => {
    try {
      const adj = await api.adjudicate({
        category: simCategory,
        return_reason: simReason,
        days_elapsed: simDays,
        return_window_days: simWindow,
        purchased_qty: simPurchasedQty,
        requested_qty: simRequestedQty,
        unit_price: simUnitPrice,
        allocated_discount: simDiscount,
        tax_amount: simTax,
        net_paid_amount: simPaid,
        policy_override_flag: simOverride,
        override_approved_by: simOverride ? 'MGR-101' : undefined,
      });
      setAdjResult(adj);

      if (adj.approved_qty > 0) {
        const ref = await api.calculateRefund({
          purchased_qty: simPurchasedQty,
          inspected_qty: adj.approved_qty,
          unit_price: simUnitPrice,
          allocated_discount: simDiscount,
          tax_amount: simTax,
          net_paid_amount: simPaid,
          condition_grade: simGrade,
          return_reason: simReason,
          loyalty_tier: simTier,
        });
        setRefResult(ref);
      } else {
        setRefResult(null);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Returns Workbench &amp; Decision Simulator</h1>
          <p className="page-description">Master/detail inspection of return requests, lifecycle events, and rule adjudication</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
        {/* Master Table of Return Requests */}
        <div className="card" style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', height: '620px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
            <h2 className="card-title">Return Requests</h2>
            <div style={{ display: 'flex', gap: '6px' }}>
              {['ALL', 'APPROVED', 'PARTIALLY_APPROVED', 'REJECTED'].map(st => (
                <button
                  key={st}
                  className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : ''}`}
                  onClick={() => setStatusFilter(st)}
                >
                  {st}
                </button>
              ))}
            </div>
          </div>

          {/* Virtualized Table */}
          <div
            ref={parentRef}
            style={{
              flex: 1,
              overflowY: 'auto',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-md)',
            }}
          >
            {isLoading ? (
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading return requests...</div>
            ) : filteredRows.length === 0 ? (
              <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No return requests found.
              </div>
            ) : (
              <div
                style={{
                  height: `${rowVirtualizer.getTotalSize()}px`,
                  width: '100%',
                  position: 'relative',
                }}
              >
                {rowVirtualizer.getVirtualItems().map(virtualRow => {
                  const row = filteredRows[virtualRow.index];
                  const isSelected = row.return_request_id === selectedId;
                  return (
                    <div
                      key={row.return_request_id}
                      onClick={() => handleSelectRow(row.return_request_id)}
                      style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: `${virtualRow.size}px`,
                        transform: `translateY(${virtualRow.start}px)`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0 12px',
                        borderBottom: '1px solid var(--border)',
                        backgroundColor: isSelected ? 'var(--accent-subtle)' : 'transparent',
                        cursor: 'pointer',
                        fontSize: '12px',
                      }}
                    >
                      <span className="mono" style={{ fontWeight: isSelected ? 600 : 400, color: isSelected ? 'var(--accent)' : 'var(--text)' }}>
                        {row.return_request_id}
                      </span>
                      <span className="mono" style={{ color: 'var(--text-muted)' }}>{row.order_id}</span>
                      <span className={`status-badge ${row.request_status === 'APPROVED' ? 'success' : row.request_status === 'REJECTED' ? 'danger' : 'warning'}`}>
                        {row.request_status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Detail Drawer & Lifecycle Timeline */}
        <div className="card" style={{ padding: 'var(--space-6)', height: '620px', overflowY: 'auto' }}>
          <h2 className="card-title">Lifecycle Chain &amp; Audit Trail</h2>
          <p className="card-subtitle mono">{selectedId}</p>

          {entityData?.record && (
            <div style={{ backgroundColor: 'var(--bg)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', marginBottom: 'var(--space-4)', fontSize: '12px' }}>
              <div><strong>Order ID:</strong> <span className="mono">{entityData.record.order_id as string}</span></div>
              <div><strong>Customer ID:</strong> <span className="mono">{entityData.record.customer_id as string}</span></div>
              <div><strong>Submitted At:</strong> {formatDate(entityData.record.request_date as string)}</div>
              <div><strong>Override Auth:</strong> {entityData.record.override_approved_by ? `${entityData.record.override_approved_by} (HMAC Verified)` : 'None'}</div>
            </div>
          )}

          <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-3)', color: 'var(--text-muted)' }}>
            Sequential State Transitions
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {entityData?.events && entityData.events.length > 0 ? (
              entityData.events.map((ev, idx) => (
                <div
                  key={idx}
                  style={{
                    display: 'flex',
                    gap: 'var(--space-3)',
                    padding: '8px 12px',
                    border: '1px solid var(--border)',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--surface)',
                  }}
                >
                  <div style={{ width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--accent-subtle)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)', fontWeight: 600, fontSize: '11px' }}>
                    {ev.seq as number || idx + 1}
                  </div>
                  <div style={{ flex: 1, fontSize: '12px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ fontWeight: 600 }}>{ev.previous_state as string} → {ev.new_state as string}</span>
                      <span style={{ color: 'var(--text-faint)' }}>{formatDate(ev.event_timestamp as string)}</span>
                    </div>
                    <div style={{ color: 'var(--text-muted)', marginTop: '2px' }}>
                      Actor: <span className="mono">{ev.actor_id as string}</span>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div style={{ color: 'var(--text-muted)', fontSize: '12px' }}>No events logged for this entity.</div>
            )}
          </div>
        </div>
      </div>

      {/* Decision Simulator Panel */}
      <section className="card" aria-label="Decision Simulator">
        <h2 className="card-title">Simulate Adjudication &amp; Prorated Refund</h2>
        <p className="card-subtitle">Test strict Priority 1-5 rules and cumulative remainder penny calculations with worked step-by-step numbers</p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-4)', marginBottom: 'var(--space-4)' }}>
          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Category</label>
            <select
              value={simCategory}
              onChange={e => setSimCategory(e.target.value)}
              style={{ width: '100%', padding: '6px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            >
              <option value="APPAREL">APPAREL (30d)</option>
              <option value="ELECTRONICS">ELECTRONICS (15d)</option>
              <option value="HOME">HOME (30d)</option>
              <option value="FINAL_SALE">FINAL_SALE (0d)</option>
              <option value="HAZMAT">HAZMAT (0d)</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Return Reason</label>
            <select
              value={simReason}
              onChange={e => setSimReason(e.target.value)}
              style={{ width: '100%', padding: '6px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            >
              <option value="CHANGED_MIND">CHANGED_MIND</option>
              <option value="SIZE_FIT">SIZE_FIT</option>
              <option value="DEFECTIVE">DEFECTIVE (Merchant Fault)</option>
              <option value="DAMAGED_IN_TRANSIT">DAMAGED_IN_TRANSIT</option>
              <option value="WRONG_ITEM">WRONG_ITEM</option>
            </select>
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Days Elapsed</label>
            <input
              type="number"
              value={simDays}
              onChange={e => setSimDays(parseInt(e.target.value) || 0)}
              style={{ width: '100%', padding: '6px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            />
          </div>

          <div>
            <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Condition Grade</label>
            <select
              value={simGrade}
              onChange={e => setSimGrade(e.target.value)}
              style={{ width: '100%', padding: '6px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', background: 'var(--surface)', color: 'var(--text)' }}
            >
              <option value="GRADE_A_NEW">GRADE_A_NEW</option>
              <option value="GRADE_B_OPEN_BOX">GRADE_B_OPEN_BOX (15% Restock)</option>
              <option value="GRADE_C_DAMAGED">GRADE_C_DAMAGED</option>
              <option value="FRAUD_MISMATCH">FRAUD_MISMATCH ($0 Payout)</option>
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={simOverride}
              onChange={e => setSimOverride(e.target.checked)}
            />
            <span>Manager Override Authorized (MGR-101 · HMAC Signed)</span>
          </label>

          <button className="btn btn-primary" onClick={handleSimulate} style={{ marginLeft: 'auto' }}>
            Execute Simulation
          </button>
        </div>

        {/* Worked Arithmetic Output */}
        {adjResult && (
          <div style={{ backgroundColor: 'var(--bg)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
            <h3 style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
              Adjudication Outcome: <span style={{ color: adjResult.approved_qty > 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>{adjResult.eligibility_status}</span> (Priority {adjResult.triggered_priority})
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 'var(--space-3)' }}>{adjResult.rule_explanation}</p>

            {refResult && (
              <div style={{ borderTop: '1px solid var(--border)', paddingTop: 'var(--space-3)' }}>
                <h4 style={{ fontSize: '12px', fontWeight: 600, marginBottom: '6px' }}>Worked Fixed-Point Remainder Arithmetic</h4>
                <div style={{ fontSize: '12px', fontFamily: 'var(--font-mono)', lineHeight: 1.6 }}>
                  <div>1. GMV: {formatCurrency(refResult.gross_merch_value)} = unit_price × qty</div>
                  <div>2. Discount Clawback: -{formatCurrency(refResult.discount_clawback)} (Prorated)</div>
                  <div>3. Net Base: {formatCurrency(refResult.net_merch_base)}</div>
                  <div>4. Tax Refund: +{formatCurrency(refResult.tax_refund_amount)}</div>
                  <div>5. Restocking Fee: -{formatCurrency(refResult.restocking_fee)}</div>
                  <div style={{ fontWeight: 600, color: 'var(--accent)', marginTop: '4px' }}>
                    Final Net Refund: {formatCurrency(refResult.net_refund_amount)} (Invariant Verified: {refResult.invariant_passed ? 'Yes' : 'No'})
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
};
