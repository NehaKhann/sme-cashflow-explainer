import { useState, useEffect } from "react";
import type { ReportSummary, CompareResult } from "../types/api";
import { fetchReports, compareReportsApi } from "../api/client";
import { TrendingUpIcon } from "./Icons";

function money(n: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(n);
}

interface ComparePageProps {
  apiBase: string;
}

export function ComparePage({ apiBase }: ComparePageProps) {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedA, setSelectedA] = useState("");
  const [selectedB, setSelectedB] = useState("");
  const [result, setResult] = useState<CompareResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let ignore = false;
    fetchReports(apiBase).then((list) => { if (!ignore) setReports(list); }).catch(() => {}).finally(() => { if (!ignore) setLoading(false); });
    return () => { ignore = true; };
  }, [apiBase]);

  async function handleCompare() {
    if (!selectedA || !selectedB || selectedA === selectedB) {
      setError("Select two different reports.");
      return;
    }
    setError("");
    setBusy(true);
    try {
      const res = await compareReportsApi(apiBase, [selectedA, selectedB]);
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Comparison failed.");
    } finally {
      setBusy(false);
    }
  }

  function deltaClass(val: number, inverse = false) {
    if (val === 0) return "";
    const positive = inverse ? val < 0 : val > 0;
    return positive ? "delta-positive" : "delta-negative";
  }

  return (
    <div className="compare-page">
      <div className="compare-controls">
        <select value={selectedA} onChange={(e) => setSelectedA(e.target.value)} aria-label="First report">
          <option value="">— Select first report —</option>
          {reports.map((r) => (
            <option key={r.id} value={r.id}>{r.start_date} — {r.end_date} ({r.risk_band})</option>
          ))}
        </select>
        <span className="compare-vs">vs</span>
        <select value={selectedB} onChange={(e) => setSelectedB(e.target.value)} aria-label="Second report">
          <option value="">— Select second report —</option>
          {reports.map((r) => (
            <option key={r.id} value={r.id}>{r.start_date} — {r.end_date} ({r.risk_band})</option>
          ))}
        </select>
        <button className="btn btn-primary" onClick={handleCompare} disabled={busy || !selectedA || !selectedB}>
          {busy ? "Comparing..." : "Compare"}
        </button>
      </div>
      {loading && <div className="loading-text" style={{ textAlign: "center", padding: 24, color: "var(--text-muted)" }}>Loading reports...</div>}
      {error && <div className="error-banner">{error}</div>}

      {result && (
        <div className="compare-results">
          <div className="compare-pair">
            <div className="compare-report">
              <h3>{result.report_a.start_date} — {result.report_a.end_date}</h3>
              <span className={`risk-badge ${result.report_a.risk_band}`}>{result.report_a.risk_band.toUpperCase()} RISK</span>
              <div className="compare-stats">
                <div className="compare-stat">
                  <span className="stat-label">Net cash flow</span>
                  <span className={`stat-value ${result.report_a.net_cash_flow >= 0 ? "stat-positive" : "stat-negative"}`}>
                    {money(result.report_a.net_cash_flow, result.report_a.currency)}
                  </span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Volatility</span>
                  <span className="stat-value">{result.report_a.revenue_volatility_pct}%</span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Top customer</span>
                  <span className="stat-value">{result.report_a.top_customer_share_pct}%</span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Risk score</span>
                  <span className="stat-value">{result.report_a.risk_score}</span>
                </div>
              </div>
            </div>
            <div className="compare-vs-divider">
              <TrendingUpIcon size={24} />
            </div>
            <div className="compare-report">
              <h3>{result.report_b.start_date} — {result.report_b.end_date}</h3>
              <span className={`risk-badge ${result.report_b.risk_band}`}>{result.report_b.risk_band.toUpperCase()} RISK</span>
              <div className="compare-stats">
                <div className="compare-stat">
                  <span className="stat-label">Net cash flow</span>
                  <span className={`stat-value ${result.report_b.net_cash_flow >= 0 ? "stat-positive" : "stat-negative"}`}>
                    {money(result.report_b.net_cash_flow, result.report_b.currency)}
                  </span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Volatility</span>
                  <span className="stat-value">{result.report_b.revenue_volatility_pct}%</span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Top customer</span>
                  <span className="stat-value">{result.report_b.top_customer_share_pct}%</span>
                </div>
                <div className="compare-stat">
                  <span className="stat-label">Risk score</span>
                  <span className="stat-value">{result.report_b.risk_score}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="card deltas-card">
            <div className="card-header"><h3>Changes (B - A)</h3></div>
            <div className="card-body">
              <div className="deltas-grid">
                <div className="delta-item">
                  <span className="delta-label">Net cash flow</span>
                  <span className={`delta-value ${deltaClass(result.deltas.net_cash_flow)}`}>
                    {result.deltas.net_cash_flow > 0 ? "+" : ""}{money(result.deltas.net_cash_flow)}
                  </span>
                </div>
                <div className="delta-item">
                  <span className="delta-label">Volatility</span>
                  <span className={`delta-value ${deltaClass(result.deltas.revenue_volatility_pct, true)}`}>
                    {result.deltas.revenue_volatility_pct > 0 ? "+" : ""}{result.deltas.revenue_volatility_pct.toFixed(1)}pp
                  </span>
                </div>
                <div className="delta-item">
                  <span className="delta-label">Top customer share</span>
                  <span className={`delta-value ${deltaClass(result.deltas.top_customer_share_pct, true)}`}>
                    {result.deltas.top_customer_share_pct > 0 ? "+" : ""}{result.deltas.top_customer_share_pct.toFixed(1)}pp
                  </span>
                </div>
                <div className="delta-item">
                  <span className="delta-label">Risk score</span>
                  <span className={`delta-value ${deltaClass(result.deltas.risk_score, true)}`}>
                    {result.deltas.risk_score > 0 ? "+" : ""}{result.deltas.risk_score}
                  </span>
                </div>
                <div className="delta-item">
                  <span className="delta-label">Total inflow</span>
                  <span className={`delta-value ${deltaClass(result.deltas.total_inflow)}`}>
                    {result.deltas.total_inflow > 0 ? "+" : ""}{money(result.deltas.total_inflow)}
                  </span>
                </div>
                <div className="delta-item">
                  <span className="delta-label">Avg monthly burn</span>
                  <span className={`delta-value ${deltaClass(result.deltas.avg_monthly_burn, true)}`}>
                    {result.deltas.avg_monthly_burn > 0 ? "+" : ""}{money(result.deltas.avg_monthly_burn)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}