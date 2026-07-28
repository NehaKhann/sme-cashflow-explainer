import type { Page } from "./Sidebar";
import { ChartIcon, TrendingUpIcon, UsersIcon, AlertIcon } from "./Icons";

interface DashboardHomeProps {
  onNavigate: (page: Page) => void;
}

export function DashboardHome({ onNavigate }: DashboardHomeProps) {
  return (
    <div className="dashboard-home">
      <div className="card welcome-card">
        <div className="welcome-icon">
          <ChartIcon size={40} strokeWidth={1.5} />
        </div>
        <h2>No analysis yet</h2>
        <p className="welcome-desc">
          Upload a CSV of business transactions to generate a cash-flow underwriting memo with
          computed metrics, risk flags, and a narrative summary.
        </p>
        <button className="btn btn-primary welcome-cta" onClick={() => onNavigate("upload")}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload transactions
        </button>
      </div>

      <div className="feature-grid">
        <div className="feature-card">
          <TrendingUpIcon size={20} />
          <div>
            <div className="feature-title">Revenue volatility</div>
            <div className="feature-desc">Coefficient of variation across monthly revenue — detects unpredictable cash inflows.</div>
          </div>
        </div>
        <div className="feature-card">
          <UsersIcon size={20} />
          <div>
            <div className="feature-title">Concentration risk</div>
            <div className="feature-desc">Top customer share of total revenue — identifies dependence on a single client.</div>
          </div>
        </div>
        <div className="feature-card">
          <AlertIcon size={20} />
          <div>
            <div className="feature-title">Negative flow streaks</div>
            <div className="feature-desc">Consecutive months of negative net cash flow — flags runway and liquidity risk.</div>
          </div>
        </div>
      </div>
    </div>
  );
}
