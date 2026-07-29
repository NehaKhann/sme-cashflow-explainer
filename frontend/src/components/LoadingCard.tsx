export function LoadingCard() {
  return (
    <section className="loading-section" id="loading">
      <div className="card loading-card">
        <div className="loading-spinner">
          <div className="spinner-ring" />
        </div>
        <h2>Analyzing transactions</h2>
        <p className="loading-desc">
          Computing cash-flow metrics and generating underwriting narrative&hellip;
        </p>
        <div className="loading-steps">
          <div className="step active">
            <span className="step-dot" />
            <span>Validating data</span>
          </div>
          <div className="step">
            <span className="step-dot" />
            <span>Calculating risk metrics</span>
          </div>
          <div className="step">
            <span className="step-dot" />
            <span>Generating narrative</span>
          </div>
        </div>
      </div>
    </section>
  );
}

export function SkeletonCard() {
  return (
    <section className="loading-section" id="skeleton">
      <div className="card loading-card" style={{ padding: "24px", gap: "12px", alignItems: "stretch" }}>
        <div className="skeleton skeleton-title" />
        <div className="skeleton skeleton-text" />
        <div className="skeleton skeleton-text" style={{ width: "80%" }} />
        <div className="skeleton skeleton-card" />
        <div className="skeleton skeleton-text" style={{ width: "40%" }} />
      </div>
    </section>
  );
}
