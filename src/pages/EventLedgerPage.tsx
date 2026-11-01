import React, { useState, useRef, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';
import { CheckCircle2, AlertTriangle, RefreshCw } from 'lucide-react';
import { api } from '../api/client';

interface EventRow {
  event_id: string;
  entity_type: string;
  entity_id: string;
  previous_state: string;
  new_state: string;
  actor_id: string;
  event_timestamp: string;
  seq: number;
  prev_event_hash: string;
  event_hash: string;
}

export const EventLedgerPage: React.FC = () => {
  const [selectedEvent, setSelectedEvent] = useState<EventRow | null>(null);
  const [entityFilter, setEntityFilter] = useState('');

  // Fetch events
  const { data: eventsData, isLoading, refetch: refetchEvents } = useQuery({
    queryKey: ['table', 'entity_state_events'],
    queryFn: () => api.getTable<EventRow>('entity_state_events', 1, 200),
  });

  // Verify hash chain
  const { data: verifyData, isLoading: isVerifying, refetch: refetchVerify } = useQuery({
    queryKey: ['ledger-verify'],
    queryFn: api.getLedgerVerify,
  });

  const allEvents: EventRow[] = eventsData?.data || eventsData?.records || [];
  const filteredEvents = allEvents.filter(e => {
    if (!entityFilter) return true;
    return (
      e.entity_id.toLowerCase().includes(entityFilter.toLowerCase()) ||
      e.entity_type.toLowerCase().includes(entityFilter.toLowerCase()) ||
      e.actor_id.toLowerCase().includes(entityFilter.toLowerCase())
    );
  });

  useEffect(() => {
    if ((!selectedEvent || !filteredEvents.some(e => e.event_id === selectedEvent.event_id)) && filteredEvents.length > 0) {
      setSelectedEvent(filteredEvents[0]);
    }
  }, [filteredEvents, selectedEvent]);

  // Virtualizer for event ledger
  const parentRef = useRef<HTMLDivElement>(null);
  const rowVirtualizer = useVirtualizer({
    count: filteredEvents.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 40,
    overscan: 10,
  });

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Immutable Event Ledger &amp; Cryptographic Audit</h1>
          <p className="page-description">Monotonic sequence audit trail with SHA-256 hash chains and Segregation of Duties (SoD) verification</p>
        </div>

        {/* Hash-Chain Verification Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isVerifying ? (
            <span className="status-badge neutral">Verifying SHA-256 Chain...</span>
          ) : verifyData?.verified ? (
            <span className="status-badge success" style={{ padding: '6px 12px', fontSize: '12px' }}>
              <CheckCircle2 size={14} /> Hash Chain Verified ({verifyData.total_events_checked} Events)
            </span>
          ) : (
            <span className="status-badge danger" style={{ padding: '6px 12px', fontSize: '12px' }}>
              <AlertTriangle size={14} /> Broken Chain at seq {verifyData?.broken_chains?.[0]?.broken_at_seq}
            </span>
          )}

          <button className="btn btn-sm btn-icon" onClick={() => { refetchVerify(); refetchEvents(); }} title="Verify ledger chain">
            <RefreshCw size={13} />
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 'var(--space-6)' }}>
        {/* Virtualized Event Table */}
        <div className="card" style={{ padding: 'var(--space-4)', height: '680px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-3)' }}>
            <h2 className="card-title">Sequenced Transition Records ({filteredEvents.length})</h2>
            <input
              type="text"
              placeholder="Filter by entity or actor..."
              value={entityFilter}
              onChange={e => setEntityFilter(e.target.value)}
              style={{
                padding: '4px 8px',
                fontSize: '12px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                background: 'var(--bg)',
                color: 'var(--text)',
                width: '200px'
              }}
            />
          </div>

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
              <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading ledger events...</div>
            ) : filteredEvents.length === 0 ? (
              <div style={{ padding: '32px 16px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '13px' }}>
                No events found matching filter.
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
                  const ev = filteredEvents[virtualRow.index];
                  const isSelected = selectedEvent?.event_id === ev.event_id;
                  const isSodViolation = ev.actor_id === 'MGR-101' && ev.entity_type === 'Refund';

                  return (
                    <div
                      key={ev.event_id}
                      onClick={() => setSelectedEvent(ev)}
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
                        backgroundColor: isSelected ? 'var(--accent-subtle)' : isSodViolation ? 'var(--status-danger-bg)' : 'transparent',
                        cursor: 'pointer',
                        fontSize: '12px',
                      }}
                    >
                      <span className="mono" style={{ width: '40px', color: 'var(--text-muted)' }}>#{ev.seq}</span>
                      <span className="mono" style={{ fontWeight: 500, width: '130px' }}>{ev.event_id}</span>
                      <span style={{ width: '130px' }}>{ev.entity_type}</span>
                      <span className="mono" style={{ width: '150px', color: 'var(--text-muted)' }}>{ev.entity_id}</span>
                      <span style={{ width: '140px', fontWeight: 500 }}>{ev.previous_state} → {ev.new_state}</span>
                      <span className="mono" style={{ width: '90px', color: isSodViolation ? 'var(--status-danger)' : 'var(--text-faint)' }}>
                        {ev.actor_id}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Monospaced JSON Inspector Side Panel */}
        <div className="card" style={{ padding: 'var(--space-6)', height: '680px', display: 'flex', flexDirection: 'column' }}>
          <h2 className="card-title">Cryptographic Hash Inspector</h2>
          <p className="card-subtitle">Canonical row JSON &amp; SHA-256 chain verification</p>

          {selectedEvent ? (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-3)', minHeight: 0 }}>
              <div style={{ backgroundColor: 'var(--bg)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', fontSize: '11px', fontFamily: 'var(--font-mono)' }}>
                <div style={{ color: 'var(--text-muted)', marginBottom: '4px' }}>CURRENT EVENT HASH (SHA-256):</div>
                <div style={{ color: 'var(--accent)', wordBreak: 'break-all' }}>{selectedEvent.event_hash}</div>

                <div style={{ color: 'var(--text-muted)', marginTop: '8px', marginBottom: '4px' }}>PREVIOUS EVENT HASH:</div>
                <div style={{ color: 'var(--text-faint)', wordBreak: 'break-all' }}>
                  {selectedEvent.prev_event_hash || '00000000000000000000000000000000 (GENESIS)'}
                </div>
              </div>

              <div style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: '4px' }}>CANONICAL EVENT JSON:</div>
                <pre
                  style={{
                    flex: 1,
                    overflowY: 'auto',
                    backgroundColor: 'var(--bg)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)',
                    fontSize: '11px',
                    lineHeight: 1.5,
                  }}
                >
                  {JSON.stringify(selectedEvent, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div style={{ color: 'var(--text-muted)', fontSize: '12px', textAlign: 'center', marginTop: '40px' }}>
              Select an event row from the ledger to inspect its SHA-256 hash payload.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
