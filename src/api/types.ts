/**
 * Strong TypeScript API Interface Types
 * Single source of truth for frontend API contracts. Zero `any` usage.
 */

export interface HealthResponse {
  status: string;
  service: string;
  compliance_practice: string;
  database_connected: boolean;
  database_path: string | null;
  table_row_counts: Record<string, number>;
  server_time: string;
}

export interface FinancialsOverview {
  total_order_revenue_cents: number;
  total_order_revenue: string;
  total_refunded_cents: number;
  total_refunded: string;
  total_restocking_fees_cents: number;
  total_restocking_fees: string;
  total_discount_clawback_cents: number;
  total_discount_clawback: string;
  discount_and_fee_recovery_cents: number;
  discount_and_fee_recovery: string;
  net_payout_ratio_pct: number;
}

export interface KpisOverview {
  return_authorization_rate_pct: number;
  net_recovery_rate_pct: number;
  rule_conformance_vs_ground_truth: number;
  hard_negative_false_positives: number;
  reproducibility_verified: boolean;
}

export interface DispositionItem {
  count: number;
  qty: number;
}

export interface CategoryItem {
  lines: number;
  revenue_cents: number;
  revenue: string;
}

export interface TenderItem {
  count: number;
  cents: number;
  amount: string;
}

export interface OverviewResponse {
  table_counts: Record<string, number>;
  financials: FinancialsOverview;
  kpis: KpisOverview;
  dispositions: Record<string, DispositionItem>;
  categories: Record<string, CategoryItem>;
  return_reasons: Record<string, number>;
  condition_grades: Record<string, number>;
  settlement_methods: Record<string, TenderItem>;
}

export interface KpiDefinition {
  label: string;
  formula: string;
  numerator: string;
  denominator: string;
  scope: string;
  unit: string;
}

export type KpiDefinitionsResponse = Record<string, KpiDefinition>;

export interface DetectionRecord {
  record_id: string;
  detected_type: string;
  evidence: string;
  entity_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
}

export interface ClassMetric {
  issue_type: string;
  true_positives: number;
  false_positives: number;
  false_negatives: number;
  precision: number;
  recall: number;
  f1_score: number;
}

export interface EvaluationPayload {
  per_class_metrics: Record<string, ClassMetric>;
  overall_precision: number;
  overall_recall: number;
  overall_f1: number;
  confusion_matrix: Record<string, Record<string, number>>;
  hard_negative_false_positive_count: number;
  false_positives: Array<{
    record_id: string;
    detected_type: string;
    actual_type: string;
    evidence: string;
  }>;
  false_negatives: Array<{
    record_id: string;
    expected_type: string;
    evidence: string;
  }>;
  total_anomalies_ground_truth: number;
  total_valid_boundaries: number;
  conformance_explanation: string;
}

export interface AnomalyResponse {
  total_count: number;
  taxonomy: Record<string, {
    title: string;
    table: string;
    severity: string;
    violated_rule: string;
    expected_action: string;
    description: string;
  }>;
  counts_by_type: Record<string, number>;
  records: DetectionRecord[];
  evaluation: Partial<EvaluationPayload>;
}

export interface TableQueryResponse<T = Record<string, unknown>> {
  table: string;
  page: number;
  limit: number;
  total_rows: number;
  total_pages: number;
  data: T[];
  records?: T[];
}

export interface LedgerVerifyResponse {
  status: 'VERIFIED' | 'CORRUPTED';
  verified: boolean;
  total_events_checked: number;
  total_entities_checked: number;
  broken_chains: Array<{
    entity_type: string;
    entity_id: string;
    broken_at_seq: number;
    reason: string;
  }>;
}

export interface AdjudicatePayload {
  order_line_id?: string;
  order_id?: string;
  sku_id?: string;
  category?: string;
  return_window_days?: number;
  purchased_qty?: number;
  unit_price?: string | number;
  allocated_discount?: string | number;
  tax_amount?: string | number;
  net_paid_amount?: string | number;
  days_elapsed?: number;
  requested_qty?: number;
  return_reason?: string;
  policy_override_flag?: boolean;
  override_approved_by?: string;
  override_token?: string;
  return_request_id?: string;
  prior_approved_qty?: number;
}

export interface AdjudicateResponse {
  eligibility_status: string;
  approved_qty: number;
  triggered_priority: number;
  rule_explanation: string;
  override_token_verified: boolean;
}

export interface CalculateRefundPayload {
  order_line_id?: string;
  order_id?: string;
  purchased_qty?: number;
  unit_price?: string | number;
  allocated_discount?: string | number;
  tax_amount?: string | number;
  net_paid_amount?: string | number;
  inspected_qty?: number;
  condition_grade?: string;
  return_reason?: string;
  loyalty_tier?: string;
  refund_status?: string;
  shipping_fee_paid?: string | number;
  is_final_remaining_line?: boolean;
}

export interface CalculateRefundResponse {
  gross_merch_value_cents: number;
  gross_merch_value: string;
  discount_clawback_cents: number;
  discount_clawback: string;
  net_merch_base_cents: number;
  net_merch_base: string;
  tax_refund_amount_cents: number;
  tax_refund_amount: string;
  restocking_fee_cents: number;
  restocking_fee: string;
  shipping_refund_cents: number;
  shipping_refund: string;
  net_refund_amount_cents: number;
  net_refund_amount: string;
  invariant_passed: boolean;
  explanation: string;
}

