import { useState, useEffect } from "react";
import { TrendingUpIcon, AlertIcon, BarChartIcon, UploadIcon, UsersIcon, ChartIcon } from "./Icons";

interface LandingPageProps {
  onGetStarted: () => void;
  onSignIn: () => void;
  onTryDemo: () => void;
}

function scrollTo(id: string) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth" });
}

export function LandingPage({ onGetStarted, onSignIn, onTryDemo }: LandingPageProps) {
  const [dark, setDark] = useState(() => localStorage.getItem("dark_mode") === "true");
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark-mode", dark);
    localStorage.setItem("dark_mode", String(dark));
  }, [dark]);

  function closeMenu() { setMenuOpen(false); }

  return (
    <div className="landing">
      <header className="landing-header">
        <div className="landing-header-inner">
          <div className="landing-brand">
            <TrendingUpIcon size={22} />
            <span>Ledger</span>
          </div>
          <div className="landing-header-center">
            <button className="btn-dark-toggle-nav" onClick={() => setDark(!dark)} title="Toggle dark mode">
              {dark ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
            </button>
          </div>
          <nav className="landing-nav">
            <button className="btn-link-nav" onClick={() => scrollTo("features")}>Features</button>
            <button className="btn-link-nav" onClick={() => scrollTo("how-it-works")}>How it works</button>
            <button className="btn-ghost" onClick={onTryDemo}>Try demo</button>
            <button className="btn-ghost" onClick={onSignIn}>Sign in</button>
            <button className="btn-primary" onClick={onGetStarted}>Get started</button>
          </nav>
          <button className="landing-menu-btn" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle menu">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {menuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <path d="M3 12h18M3 6h18M3 18h18" />
              )}
            </svg>
          </button>
        </div>
        {menuOpen && (
          <div className="landing-mobile-menu">
            <button className="btn-link-nav" onClick={() => { scrollTo("features"); closeMenu(); }}>Features</button>
            <button className="btn-link-nav" onClick={() => { scrollTo("how-it-works"); closeMenu(); }}>How it works</button>
            <div className="landing-mobile-divider" />
            <button className="btn-ghost" onClick={() => { onTryDemo(); closeMenu(); }}>Try demo</button>
            <button className="btn-ghost" onClick={() => { onSignIn(); closeMenu(); }}>Sign in</button>
            <button className="btn-primary" onClick={() => { onGetStarted(); closeMenu(); }}>Get started</button>
          </div>
        )}
      </header>

      <section className="landing-hero">
        <div className="landing-hero-bg" />
        <div className="landing-hero-content">
          <h1>
            Turn bank transactions into<br />
            <span className="text-gradient">auditable risk memos</span>
          </h1>
          <p className="landing-hero-desc">
            Ledger analyzes cash-flow data from raw CSV exports, computes every underwriting
            metric deterministically, and generates a clear narrative — so you know exactly
            why each number is what it is.
          </p>
          <div className="landing-hero-actions">
            <button className="btn-primary btn-lg" onClick={onGetStarted}>
              Start analyzing
            </button>
            <button className="btn-secondary btn-lg" onClick={onTryDemo}>
              Try demo
            </button>
            <button className="btn-secondary btn-lg" onClick={onSignIn}>
              Sign in
            </button>
          </div>
          <div className="landing-hero-stats">
            <span>Deterministic computation</span>
            <span className="dot" />
            <span>Optional AI narrative</span>
            <span className="dot" />
            <span>Open source</span>
          </div>
        </div>
      </section>

      <section id="features" className="landing-section">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">Everything an underwriter needs</h2>
          <p className="landing-section-sub">
            From raw CSV to structured memo in seconds — every figure traceable to a calculation.
          </p>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "var(--primary-subtle)", color: "var(--primary)" }}>
                <ChartIcon size={24} />
              </div>
              <h3>Cash-flow metrics</h3>
              <p>Revenue volatility, seasonal patterns, month-over-month trends, and expense breakdowns — computed automatically from your transaction data.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "rgba(239,68,68,0.08)", color: "var(--danger)" }}>
                <AlertIcon size={24} />
              </div>
              <h3>Risk flagging</h3>
              <p>Customer concentration, sustained negative flows, sharp revenue drops, thin customer bases — flagged with severity and explained in plain language.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "rgba(16,185,129,0.08)", color: "var(--success)" }}>
                <BarChartIcon size={24} />
              </div>
              <h3>Report history</h3>
              <p>Every analysis is saved permanently. Revisit past memos, compare risk scores, and track changes over time — all scoped to your account.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "rgba(99,102,241,0.08)", color: "var(--accent)" }}>
                <UploadIcon size={24} />
              </div>
              <h3>CSV in, memo out</h3>
              <p>Upload any bank-export CSV with date, amount, and counterparty columns. No setup, no configuration — just drop and analyze.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "rgba(245,158,11,0.08)", color: "var(--warning)" }}>
                <UsersIcon size={24} />
              </div>
              <h3>Concentration analysis</h3>
              <p>Know your customer risk instantly — top-customer share, top-3 concentration, and revenue dependency scored and explained in the memo.</p>
            </div>
            <div className="feature-card">
              <div className="feature-icon" style={{ background: "rgba(59,130,246,0.08)", color: "var(--primary)" }}>
                <TrendingUpIcon size={24} />
              </div>
              <h3>Optional LLM narrative</h3>
              <p>Connect a Groq API key for AI-generated prose, or use the deterministic template — both paths explain the same computed numbers, just different prose.</p>
            </div>
          </div>
        </div>
      </section>

      <section id="how-it-works" className="landing-section landing-section-alt">
        <div className="landing-section-inner">
          <h2 className="landing-section-title">How it works</h2>
          <p className="landing-section-sub">
            Three steps from raw data to an underwriter-ready memo.
          </p>
          <div className="steps-row">
            <div className="step-item">
              <div className="step-number">1</div>
              <h3>Upload</h3>
              <p>Drop a CSV of bank transactions or use the built-in sample data. The only required columns are <code>date</code>, <code>amount</code>, and <code>counterparty</code>.</p>
            </div>
            <div className="step-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M13 5l7 7-7 7" /></svg>
            </div>
            <div className="step-item">
              <div className="step-number">2</div>
              <h3>Analyze</h3>
              <p>Pandas computes 20+ financial metrics, risk rules assign a score and band (low / medium / high), and the narrative generator produces the memo.</p>
            </div>
            <div className="step-arrow">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M5 12h14M13 5l7 7-7 7" /></svg>
            </div>
            <div className="step-item">
              <div className="step-number">3</div>
              <h3>Review</h3>
              <p>Read the narrative, inspect every metric, check the risk flags, and download or revisit the report later. Every figure links back to a calculation.</p>
            </div>
          </div>
        </div>
      </section>

      <section className="landing-cta">
        <div className="landing-cta-inner">
          <h2>Ready to analyze?</h2>
          <p>Create an account and run your first cash-flow analysis in under a minute.</p>
          <button className="btn-primary btn-lg" onClick={onGetStarted}>
            Get started free
          </button>
          <p className="landing-cta-sub">
            Already have an account? <button className="btn-link" onClick={onSignIn}>Sign in</button>
            {" / "}
            <button className="btn-link" onClick={onTryDemo}>Try demo</button>
          </p>
        </div>
      </section>

      <footer className="landing-footer">
        <p>Ledger — SME Cash-Flow Underwriting Platform</p>
      </footer>
    </div>
  );
}
