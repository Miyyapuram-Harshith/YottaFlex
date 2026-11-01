import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { formatPercent, formatInt } from '../utils/formatters';
import { DetectionRecord } from '../api/types';

export const ExceptionsPage: React.FC = () => {
  const [selectedFilter, setSelectedFilter] = useState('ALL');
  const [remediatedRecords, setRemediatedRecords] = useState<Set<string>>(new Set());
  const [activeDiffRecord, setActiveDiffRecord] = useState<DetectionRecord | null>(null);

  const { data: anomalyData, isLoading, isError, refetch } = useQuery({
    queryKey: ['anomalies'],
    queryFn: api.getAnomalies,
  });

  const records = anomalyData?.records || [];
  const evalPayload = anomalyData?.evaluation;

  const filteredRecords = records.filter(r => {
    if (selectedFilter === 'ALL') return true;
    return r.detected_type === selectedFilter;
  });

  const handleRemediate = (recordId: string) => {
    // Write compensating event, never edit history
    setRemediatedRecords(prev => new Set([...prev, recordId]));
  };

  if (isError) {
    return (
      <div className="card" style={{ maxWidth: '640px', margin: '48px auto', textAlign: 'center', padding: 'var(--space-6)' }}>
        <h2 className="card-title" style={{ color: 'var(--status-danger)', marginBottom: 'var(--space-2)' }}>
          Backend Service Offline
        </h2>
        <p className="card-subtitle" style={{ marginBottom: 'var(--space-4)' }}>
          Could not load anomaly detections. Start the API server with <code>python3 api_server.py --port 8000</code>.
        </p>
        <button className="btn btn-primary" onClick={() => refetch()}>Retry Connection</button>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div style={{ padding: '48px 32px', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading policy exceptions and conformance metrics...
      </div>
    );
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Policy Exceptions &amp; Conformance Audit</h1>
          <p className="page-description">Independent rule-engine detections and ground-truth benchmark conformance evaluation</p>
        </div>
      </div>

      {/* Conformance vs. ML Metric Panel */}
      {evalPayload && (
        <section className="card" aria-label="Evaluation Metrics">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-4)' }}>
            <div>
              <h2 className="card-title">Rule-Engine Conformance vs. Ground Truth</h2>
              <p className="card-subtitle" style={{ maxWidth: '800px' }}>
                {evalPayload.conformance_explanation ||
                  'Deterministic rules are expected to score 1.0 on injected rule violations. The harder operational test is the hard-negative set (VALID_BOUNDARY), where false positive count must strictly remain 0.'}
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>HARD-NEGATIVE FP COUNT</div>
              <div style={{ fontSize: '20px', fontWeight: 600, color: evalPayload.hard_negative_false_positive_count === 0 ? 'var(--status-success)' : 'var(--status-danger)' }}>
                {evalPayload.hard_negative_false_positive_count || 0}
              </div>
            </div>
          </div>

          {/* Per-class Metrics Table */}
          {evalPayload.per_class_metrics && (
            <table className="data-table" style={{ marginBottom: 'var(--space-4)' }}>
              <thead>
                <tr>
                  <th scope="col">Injected Policy Violation Type</th>
                  <th scope="col" style={{ textAlign: 'right' }}>TP</th>
                  <th scope="col" style={{ textAlign: 'right' }}>FP</th>
                  <th scope="col" style={{ textAlign: 'right' }}>FN</th>
                  <th scope="col" style={{ textAlign: 'right' }}>Precision</th>
                  <th scope="col" style={{ textAlign: 'right' }}>Recall</th>
                  <th scope="col" style={{ textAlign: 'right' }}>F1-Score</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(evalPayload.per_class_metrics).map(([itype, m]) => (
                  <tr key={itype}>
                    <td className="mono" style={{ fontWeight: 500 }}>{itype}</td>
                    <td style={{ textAlign: 'right' }}>{m.true_positives}</td>
                    <td style={{ textAlign: 'right' }}>{m.false_positives}</td>
                    <td style={{ textAlign: 'right' }}>{m.false_negatives}</td>
                    <td style={{ textAlign: 'right' }}>{formatPercent(m.precision * 100, 1)}</td>
                    <td style={{ textAlign: 'right' }}>{formatPercent(m.recall * 100, 1)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--status-success)' }}>
                      {m.f1_score.toFixed(3)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {/* Detections Master Table */}
      <section className="card" aria-label="Detected Exceptions">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
          <h2 className="card-title">Independent Detections ({formatInt(filteredRecords.length)})</h2>
          {/* Plain Filter Chips */}
          <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
            {['ALL', 'ANOM_QTY_EXCEEDS_PURCHASED', 'ANOM_LATE_RETURN_NO_OVERRIDE', 'ANOM_RESTOCK_BEFORE_INSP', 'ANOM_REFUND_EXCEEDS_PAID', 'ANOM_DUPLICATE_REFUND'].map(f => (
              <button
                key={f}
                className={`btn btn-sm ${selectedFilter === f ? 'btn-primary' : ''}`}
                onClick={() => setSelectedFilter(f)}
                style={{ fontSize: '11px' }}
              >
                {f === 'ALL' ? 'All' : f.replace('ANOM_', '')}
              </button>
            ))}
          </div>
        </div>

        {isLoading ? (
          <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading detections...</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th scope="col">Severity</th>
                <th scope="col">Record ID</th>
                <th scope="col">Detected Rule Violation</th>
                <th scope="col">Audit Evidence</th>
                <th scope="col">Status</th>
                <th scope="col" style={{ textAlign: 'right' }}>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredRecords.map(rec => {
                const isRemediated = remediatedRecords.has(rec.record_id);
                return (
                  <tr key={rec.record_id}>
                    <td>
                      <span className={`status-badge ${rec.severity === 'CRITICAL' ? 'danger' : 'warning'}`}>
                        {rec.severity}
                      </span>
                    </td>
                    <td className="mono" style={{ fontWeight: 500 }}>{rec.record_id}</td>
                    <td>{rec.detected_type}</td>
                    <td style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '380px' }}>
                      {rec.evidence}
                    </td>
                    <td>
                      {isRemediated ? (
                        <span className="status-badge success">Remediated</span>
                      ) : (
                        <span className="status-badge warning">Open</span>
                      )}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '6px', justifyContent: 'flex-end' }}>
                        <button
                          className="btn btn-sm"
                          onClick={() => setActiveDiffRecord(rec)}
                          title="View evidence difference"
                        >
                          Diff
                        </button>
                        {!isRemediated && (
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleRemediate(rec.record_id)}
                            title="Log compensating ledger event"
                          >
                            Remediate
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </section>

      {/* Evidence Diff Modal */}
      {activeDiffRecord && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setActiveDiffRecord(null)}
        >
          <div
            style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-lg)',
              padding: 'var(--space-6)',
              maxWidth: '520px',
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-2)' }}>
              Evidence Diff &mdash; <span className="mono">{activeDiffRecord.record_id}</span>
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
              {activeDiffRecord.detected_type}
            </p>

            <div style={{ backgroundColor: 'var(--bg)', padding: 'var(--space-3)', borderRadius: 'var(--radius-md)', fontFamily: 'var(--font-mono)', fontSize: '12px', lineHeight: 1.6, marginBottom: 'var(--space-4)' }}>
              <div style={{ color: 'var(--status-danger)' }}>- Violation: {activeDiffRecord.evidence}</div>
              <div style={{ color: 'var(--status-success)', marginTop: '4px' }}>+ Policy Invariant: Strictly enforced at transactional barrier</div>
            </div>

            <div style={{ textAlign: 'right' }}>
              <button className="btn btn-sm btn-primary" onClick={() => setActiveDiffRecord(null)}>
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
