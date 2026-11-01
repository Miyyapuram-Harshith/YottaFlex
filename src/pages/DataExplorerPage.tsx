import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSearchParams } from 'react-router-dom';
import { Download, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { api } from '../api/client';
import { formatInt, formatCurrency, formatDate } from '../utils/formatters';

const TABLES = [
  'customers', 'orders', 'order_lines', 'return_requests',
  'return_lines', 'return_authorizations', 'return_shipments',
  'inspections', 'refunds', 'inventory_dispositions', 'entity_state_events'
];

export const DataExplorerPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const currentTable = searchParams.get('table') || 'orders';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const currentSearch = searchParams.get('search') || '';

  const [searchInput, setSearchInput] = useState(currentSearch);

  // Fetch health to get exact row counts per table
  const { data: healthData } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
  });

  // Fetch paginated table data
  const { data: tableData, isLoading } = useQuery({
    queryKey: ['table', currentTable, currentPage, currentSearch],
    queryFn: () => api.getTable(currentTable, currentPage, 25, currentSearch),
  });

  const handleTableChange = (tbl: string) => {
    setSearchParams({ table: tbl, page: '1', search: '' });
    setSearchInput('');
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ table: currentTable, page: '1', search: searchInput });
  };

  const rows = tableData?.data || tableData?.records || [];
  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];

  const handleExportCsv = () => {
    if (rows.length === 0) return;
    const cols = Object.keys(rows[0]);
    const csvContent = [
      cols.join(','),
      ...rows.map(r => cols.map(c => `"${String((r as Record<string, unknown>)[c] ?? '').replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${currentTable}_page_${currentPage}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Canonical 3NF Data Explorer</h1>
          <p className="page-description">Normalized SQLite relational database browser with schema types and export</p>
        </div>

        <button className="btn btn-sm" onClick={handleExportCsv} disabled={rows.length === 0}>
          <Download size={13} /> Export Current View (CSV)
        </button>
      </div>

      {/* Table Selection Pills */}
      <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: 'var(--space-3)', marginBottom: 'var(--space-4)' }}>
        {TABLES.map(tbl => {
          const count = healthData?.table_row_counts?.[tbl];
          const isSelected = tbl === currentTable;
          return (
            <button
              key={tbl}
              className={`btn btn-sm ${isSelected ? 'btn-primary' : ''}`}
              onClick={() => handleTableChange(tbl)}
              style={{ fontSize: '11px', whiteSpace: 'nowrap' }}
            >
              <span>{tbl}</span>
              {count !== undefined && (
                <span style={{ opacity: 0.7, fontSize: '10px' }}>({formatInt(count)})</span>
              )}
            </button>
          );
        })}
      </div>

      {/* Search & Pagination Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-4)' }}>
        <form onSubmit={handleSearchSubmit} style={{ display: 'flex', gap: '8px' }}>
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <Search size={14} style={{ position: 'absolute', left: 8, color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder={`Search ${currentTable}...`}
              value={searchInput}
              onChange={e => setSearchInput(e.target.value)}
              style={{
                padding: '6px 10px 6px 28px',
                fontSize: '12px',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                background: 'var(--surface)',
                color: 'var(--text)',
                width: '240px'
              }}
            />
          </div>
          <button type="submit" className="btn btn-sm">Filter</button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', fontSize: '12px', color: 'var(--text-muted)' }}>
          <span>
            Showing page {currentPage} of {tableData?.total_pages || 1} ({formatInt(tableData?.total_rows || 0)} total rows)
          </span>
          <div style={{ display: 'flex', gap: '4px' }}>
            <button
              className="btn btn-sm btn-icon"
              disabled={currentPage <= 1}
              onClick={() => setSearchParams({ table: currentTable, page: String(currentPage - 1), search: currentSearch })}
              aria-label="Previous Page"
            >
              <ChevronLeft size={14} />
            </button>
            <button
              className="btn btn-sm btn-icon"
              disabled={!tableData || currentPage >= tableData.total_pages}
              onClick={() => setSearchParams({ table: currentTable, page: String(currentPage + 1), search: currentSearch })}
              aria-label="Next Page"
            >
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>

      {/* Relational Table Browser */}
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        {isLoading ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>Loading table data...</div>
        ) : rows.length === 0 ? (
          <div style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>No records found matching query.</div>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                {columns.map(col => (
                  <th key={col} scope="col">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rIdx) => (
                <tr key={rIdx}>
                  {columns.map(col => {
                    const val = (row as Record<string, unknown>)[col];
                    const isId = col.includes('id');
                    const isMoney = col.includes('amount') || col.includes('price') || col.includes('discount') || col.includes('fee') || col.includes('total');
                    const isDate = col.includes('date') || col.includes('at') || col.includes('timestamp');

                    return (
                      <td key={col} className={isId ? 'mono' : ''} style={{ fontSize: '12px' }}>
                        {isMoney && typeof val === 'number'
                          ? formatCurrency(val, col.endsWith('_cents'))
                          : isDate && typeof val === 'string' && val.includes('T')
                          ? formatDate(val)
                          : String(val ?? '—')}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

