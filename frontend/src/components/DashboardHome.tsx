export function DashboardHome() {
  return (
    <div className="dashboard-home">
      <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
        <div className="upload-icon" style={{ margin: "0 auto 20px" }}>
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M3 3v18h18" />
            <path d="M7 16l4-8 4 4 4-6" />
          </svg>
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No analysis yet</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13, maxWidth: 400, margin: "0 auto 24px", lineHeight: 1.6 }}>
          Upload a CSV of business transactions to generate a cash-flow underwriting memo with
          computed metrics, risk flags, and a narrative summary.
        </p>
        <button
          className="btn btn-primary"
          style={{ width: "auto", padding: "10px 28px" }}
          onClick={() => document.querySelector<HTMLElement>('[data-page="upload"]')?.click()}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload transactions
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginTop: 24 }}>
        <FeatureCard
          title="Revenue volatility"
          desc="Coefficient of variation across monthly revenue — detects unpredictable cash inflows."
          icon="M13 17V9M13 3l-4 4h3v4h-3l4 4"
        />
        <FeatureCard
          title="Concentration risk"
          desc="Top customer share of total revenue — identifies dependence on a single client."
          icon="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"
        />
        <FeatureCard
          title="Negative flow streaks"
          desc="Consecutive months of negative net cash flow — flags runway and liquidity risk."
          icon="M12 8v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"
        />
      </div>
    </div>
  );
}

function FeatureCard({ title, desc, icon }: { title: string; desc: string; icon: string }) {
  return (
    <div className="stat-card" style={{ gap: 12 }}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" strokeWidth="2" style={{ flexShrink: 0 }}>
        <path d={icon} />
      </svg>
      <div>
        <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 12, color: "var(--text-muted)", lineHeight: 1.5 }}>{desc}</div>
      </div>
    </div>
  );
}
