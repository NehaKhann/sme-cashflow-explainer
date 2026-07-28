export interface RiskFlagData {
  severity: "low" | "medium" | "high";
  code: string;
  message: string;
}

export interface AnalysisData {
  start_date: string;
  end_date: string;
  num_months: number;

  total_inflow: number;
  total_outflow: number;
  net_cash_flow: number;

  monthly_revenue: Record<string, number>;
  revenue_volatility_pct: number;
  largest_mom_drop_pct: number;
  largest_mom_drop_month: string | null;

  top_customer_share_pct: number;
  top_customer_name: string | null;
  top_3_customer_share_pct: number;
  num_unique_customers: number;

  seasonality_detected: boolean;
  seasonal_low_months: string[];
  seasonal_high_months: string[];

  monthly_expenses: Record<string, number>;
  expense_by_category: Record<string, number>;
  avg_monthly_burn: number;
  months_of_negative_flow: number;
  longest_negative_streak_months: number;

  risk_score: number;
  risk_band: "low" | "medium" | "high";
  risk_flags: RiskFlagData[];
  narrative: string;
}

export interface ApiHealthStatus {
  ok: boolean;
  label: string;
  className: string;
}
