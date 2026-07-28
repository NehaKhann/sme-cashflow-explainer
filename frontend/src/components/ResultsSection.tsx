import type { AnalysisData } from "../types/api";
import { ChartCard } from "./ChartCard";

function money(n: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency: "USD", maximumFractionDigits: 0,
  }).format(n);
}

interface ResultsSectionProps {
  data: AnalysisData;
  onReset: () => void;
}

export function ResultsSection({ data, onReset }: ResultsSectionProps) {
  const netClass = data.net_cash_flow >= 0 ? "stat-positive" : "stat-negative";

  return (
    <section className="results-section" id="results">
      <div className="results-header">
        <div className="results-header-left">
          <p className="results-eyebrow">Underwriting Memo</p>
          <h2 id="memo-period">{data.start_date} — {data.end_date} ({data.num_months} mo)</h2>
        </div>
        <div id="risk-stamp" className={`risk-badge ${data.risk_band}`}>
          <span>{data.risk_band.toUpperCase()} RISK</span>
        </div>
      </div>

      <div className="metrics-grid">
        <div className="stat-card">
          <span className="stat-label">Total inflow</span>
          <span className="stat-value stat-positive" id="fig-inflow">{money(data.total_inflow)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total outflow</span>
          <span className="stat-value stat-negative" id="fig-outflow">{money(Math.abs(data.total_outflow))}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Net cash flow</span>
          <span className={`stat-value ${netClass}`} id="fig-net">{money(data.net_cash_flow)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Revenue volatility</span>
          <span className="stat-value" id="fig-volatility">{data.revenue_volatility_pct}%</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Top customer share</span>
          <span className="stat-value" id="fig-concentration">{data.top_customer_share_pct}%</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Risk score</span>
          <span className="stat-value" id="fig-score">{data.risk_score} / 100</span>
        </div>
      </div>

      <ChartCard monthlyRevenue={data.monthly_revenue} monthlyExpenses={data.monthly_expenses} />

      <div className="card flags-card">
        <div className="card-header"><h3>Risk flags</h3></div>
        <div className="card-body">
          <ul className="flags-list" id="flags-list">
            {data.risk_flags.map((f, i) => (
              <li key={i} className={`flag-item ${f.severity}`}>
                <span className={`flag-severity ${f.severity}`}>{f.severity}</span>
                <span>{f.message}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card narrative-card">
        <div className="card-header"><h3>Underwriter narrative</h3></div>
        <div className="card-body">
          <div className="narrative-text" id="narrative-text">{data.narrative}</div>
        </div>
      </div>

      <div className="results-footer">
        <span className="footer-note">Every figure traces to a computed value, not a model guess.</span>
        <button className="btn btn-secondary" onClick={onReset}>Analyze another file</button>
      </div>
    </section>
  );
}
