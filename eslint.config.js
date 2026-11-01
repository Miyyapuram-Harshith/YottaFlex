import tseslint from 'typescript-eslint';

export default tseslint.config(
  ...tseslint.configs.recommended,
  {
    rules: {
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-console': ['warn', { allow: ['warn', 'error', 'info'] }],
    },
  },
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'erl_rma_export/**',
      'erl_rma_export_starter/**',
      'src/components/ExecutiveControlTower.tsx',
      'src/components/LifecycleStudio.tsx',
      'src/components/AnomalyAuditCenter.tsx',
      'src/components/EventLedgerExplorer.tsx',
      'src/components/DataExplorer.tsx',
      'src/components/BenchmarkStudio.tsx'
    ],
  }
);
