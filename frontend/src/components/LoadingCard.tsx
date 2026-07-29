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

