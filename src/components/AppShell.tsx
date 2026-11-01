import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LayoutDashboard,
  RotateCcw,
  AlertTriangle,
  FileText,
  Database,
  Cpu,
  Sun,
  Moon,
  Search,
  UserCheck,
  ChevronRight
} from 'lucide-react';
import { api, getDemoIdentity, setDemoIdentity } from '../api/client';

export const AppShell: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Theme state persisted in localStorage
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    try {
      const saved = localStorage.getItem('yottaflex_theme');
      if (saved === 'dark' || saved === 'light') return saved;
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    } catch {
      return 'dark';
    }
  });

  // Demo identity state
  const [identity, setIdentity] = useState(getDemoIdentity());

  // Backend service health
  const { data: healthData, isError: isHealthError } = useQuery({
    queryKey: ['health'],
    queryFn: api.getHealth,
    refetchInterval: 8000,
    retry: 1,
  });

  const isConnected = !isHealthError && Boolean(healthData?.database_connected);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try {
      localStorage.setItem('yottaflex_theme', theme);
    } catch {
      // ignore
    }
  }, [theme]);

  // Global search keyboard shortcut '/'
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === '/' && document.activeElement?.tagName !== 'INPUT') {
        e.preventDefault();
        const searchInput = document.getElementById('global-search-input');
        if (searchInput) searchInput.focus();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const handleIdentityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    let newId = { role: 'OPERATOR', id: 'OP-1042' };
    if (val === 'MGR-101') {
      newId = { role: 'MANAGER', id: 'MGR-101' };
    } else if (val === 'FIN-201') {
      newId = { role: 'FINANCE', id: 'FIN-201' };
    } else if (val === 'ANL-9021') {
      newId = { role: 'ANALYST', id: 'ANL-9021' };
    }
    setIdentity(newId);
    setDemoIdentity(newId.role, newId.id);
  };

  // Compute breadcrumb from current path
  const pathParts = location.pathname.split('/').filter(Boolean);
  const pageNameMap: Record<string, string> = {
    '': 'Overview',
    'overview': 'Overview',
    'returns': 'Returns workbench',
    'exceptions': 'Exceptions',
    'ledger': 'Event ledger',
    'explorer': 'Data explorer',
    'dataset': 'Dataset & reproducibility',
  };
  const currentPageTitle = pageNameMap[pathParts[0] || ''] || 'Overview';

  return (
    <>
      <div className="app-layout">
        {/* Left Vertical Nav (220px, stroke 1.5 icons) */}
        <aside className="app-sidebar" aria-label="Main Navigation">
          <div className="sidebar-header">
            <NavLink to="/overview" style={{ display: 'flex', alignItems: 'center', textDecoration: 'none' }} title="YottaFlex Home">
              <img
                src="/logo.png"
                alt="YottaFlex.ai"
                className="sidebar-brand-logo"
              />
            </NavLink>
          </div>

          <nav className="sidebar-nav">
            <NavLink to="/overview" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <LayoutDashboard size={16} strokeWidth={1.5} />
              <span>Overview</span>
            </NavLink>

            <NavLink to="/returns" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <RotateCcw size={16} strokeWidth={1.5} />
              <span>Returns workbench</span>
            </NavLink>

            <NavLink to="/exceptions" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <AlertTriangle size={16} strokeWidth={1.5} />
              <span>Exceptions</span>
            </NavLink>

            <NavLink to="/ledger" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <FileText size={16} strokeWidth={1.5} />
              <span>Event ledger</span>
            </NavLink>

            <NavLink to="/explorer" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Database size={16} strokeWidth={1.5} />
              <span>Data explorer</span>
            </NavLink>

            <NavLink to="/dataset" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Cpu size={16} strokeWidth={1.5} />
              <span>Dataset &amp; repro</span>
            </NavLink>
          </nav>

          <div className="sidebar-footer">
            <div>Seed 20261022 · Scale 1.0</div>
            <div>ISO/IEC/IEEE 29148 practice</div>
          </div>
        </aside>

        {/* Main Application Area */}
        <div className="app-main">
          {/* Top Bar with Breadcrumbs, Global Search, Env Meta, Theme & Demo Identity */}
          <header className="app-topbar" role="banner">
            <div className="topbar-left">
              <nav className="breadcrumb-trail" aria-label="Breadcrumb">
                <span>YottaFlex</span>
                <ChevronRight size={12} strokeWidth={1.5} />
                <span className="breadcrumb-current">{currentPageTitle}</span>
                {pathParts.length > 1 && (
                  <>
                    <ChevronRight size={12} strokeWidth={1.5} />
                    <span className="mono">{pathParts[1]}</span>
                  </>
                )}
              </nav>

              <span className="topbar-meta-env" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span
                  style={{
                    display: 'inline-block',
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    backgroundColor: isConnected ? 'var(--status-success)' : 'var(--status-danger)',
                  }}
                />
                <span>{isConnected ? 'API Connected' : 'API Offline (Port 8000)'} · Seed 20261022</span>
              </span>
            </div>

            <div className="topbar-right">
              {/* Global search */}
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <Search size={14} strokeWidth={1.5} style={{ position: 'absolute', left: 8, color: 'var(--text-muted)' }} />
                <input
                  id="global-search-input"
                  type="text"
                  placeholder="Search records... (/)"
                  style={{
                    padding: '5px 10px 5px 28px',
                    fontSize: '12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)',
                    backgroundColor: 'var(--bg)',
                    color: 'var(--text)',
                    width: '180px',
                  }}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      navigate(`/explorer?search=${encodeURIComponent(e.currentTarget.value)}`);
                    }
                  }}
                />
              </div>

              {/* Theme Toggle */}
              <button
                className="btn btn-icon"
                onClick={toggleTheme}
                aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
                title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
              >
                {theme === 'dark' ? <Sun size={15} strokeWidth={1.5} /> : <Moon size={15} strokeWidth={1.5} />}
              </button>

              {/* Demo Identity Switcher */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <UserCheck size={14} strokeWidth={1.5} style={{ color: 'var(--text-muted)' }} />
                <label htmlFor="demo-identity-select" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                  Demo identity:
                </label>
                <select
                  id="demo-identity-select"
                  value={identity.id}
                  onChange={handleIdentityChange}
                  style={{
                    fontSize: '12px',
                    padding: '4px 8px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)',
                    backgroundColor: 'var(--surface)',
                    color: 'var(--text)',
                    fontFamily: 'var(--font-sans)',
                  }}
                >
                  <option value="OP-1042">Warehouse Operator (OP-1042)</option>
                  <option value="MGR-101">Operations Manager (MGR-101)</option>
                  <option value="FIN-201">Finance Officer (FIN-201)</option>
                  <option value="ANL-9021">Merchandising Analyst (ANL-9021)</option>
                </select>
              </div>
            </div>
          </header>

          {!isConnected && (
            <div
              style={{
                backgroundColor: 'rgba(239, 68, 68, 0.08)',
                borderBottom: '1px solid rgba(239, 68, 68, 0.25)',
                padding: '6px 24px',
                fontSize: '12px',
                color: 'var(--status-danger)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
              }}
            >
              <span>
                <strong>Backend Service Offline:</strong> Run <code>python3 api_server.py --port 8000</code> to connect live SQLite data.
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Auto-reconnecting every 8s</span>
            </div>
          )}

          {/* Routed Page Container */}
          <main className="page-container" role="main">
            <Outlet />
          </main>
        </div>
      </div>

      {/* Responsive notice below 1024px */}
      <div className="mobile-notice">
        <h2 style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>Best viewed on desktop</h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '13px' }}>
          The YottaFlex reverse logistics operations workbench requires a minimum viewport width of 1024px.
        </p>
      </div>
    </>
  );
};
