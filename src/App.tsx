import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppShell } from './components/AppShell';
import { OverviewPage } from './pages/OverviewPage';
import { WorkbenchPage } from './pages/WorkbenchPage';
import { ExceptionsPage } from './pages/ExceptionsPage';
import { EventLedgerPage } from './pages/EventLedgerPage';
import { DataExplorerPage } from './pages/DataExplorerPage';
import { DatasetPage } from './pages/DatasetPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppShell />}>
            <Route index element={<Navigate to="/overview" replace />} />
            <Route path="overview" element={<OverviewPage />} />
            <Route path="returns" element={<WorkbenchPage />} />
            <Route path="returns/:id" element={<WorkbenchPage />} />
            <Route path="exceptions" element={<ExceptionsPage />} />
            <Route path="ledger" element={<EventLedgerPage />} />
            <Route path="explorer" element={<DataExplorerPage />} />
            <Route path="dataset" element={<DatasetPage />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
};
