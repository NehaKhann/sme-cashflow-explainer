import { useState, useEffect } from "react";
import type { AnalysisData, TransactionData } from "../types/api";
import { fetchTransactions } from "../api/client";
import { ChartCard } from "./ChartCard";

function money(n: number, currency: string = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

interface ResultsSectionProps {
  data: AnalysisData;
  prevData: AnalysisData | null;
  onReset: () => void;
  apiBase?: string;
}

function AnimatedScore({ score }: { score: number }) {
  const [display, setDisplay] = useState(0);
  useEffect(() => {
    let start = 0;
    const end = score;
    const duration = 800;
    const step = 16;
    const totalSteps = duration / step;
    const increment = end / totalSteps;
    const timer = setInterval(() => {
      start += increment;
      if (start >= end) {
        setDisplay(end);
        clearInterval(timer);
      } else {
        setDisplay(Math.round(start));
      }
    }, step);
    return () => clearInterval(timer);
  }, [score]);
  return <>{display} / 100</>;
}

export function ResultsSection({ data, prevData, onReset, apiBase }: ResultsSectionProps) {
  const netClass = data.net_cash_flow >= 0 ? "stat-positive" : "stat-negative";
  const [transactions, setTransactions] = useState<TransactionData[]>([]);
  const [txnLoading, setTxnLoading] = useState(false);
  const [showTxns, setShowTxns] = useState(false);
  const [sortKey, setSortKey] = useState<string>("date");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    if (showTxns && transactions.length === 0 && !data.demo && apiBase && data.report_id && data.report_id !== "demo") {
      setTxnLoading(true);
      fetchTransactions(apiBase, data.report_id)
        .then(setTransactions)
        .catch(() => {})
        .finally(() => setTxnLoading(false));
    }
  }, [showTxns, data.demo, apiBase, data.report_id]);

  function handleSort(key: string) {
    if (sortKey === key) {
      setSortDir(sortDir === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  const sortedTxns = [...transactions].sort((a, b) => {
    let cmp = 0;
    if (sortKey === "date") cmp = a.date.localeCompare(b.date);
    else if (sortKey === "amount") cmp = a.amount - b.amount;
    else if (sortKey === "counterparty") cmp = a.counterparty.localeCompare(b.counterparty);
    else if (sortKey === "category") cmp = a.category.localeCompare(b.category);
    return sortDir === "asc" ? cmp : -cmp;
  });

  const currency = data.currency || "USD";

  async function handleExportPdf() {
    const { default: jsPDF } = await import("jspdf");
    const { default: html2canvas } = await import("html2canvas");
    const el = document.getElementById("results");
    if (!el) return;
    const canvas = await html2canvas(el, { scale: 2, useCORS: true, backgroundColor: "#ffffff" });
    const imgData = canvas.toDataURL("image/png");
    const pdf = new jsPDF("p", "mm", "a4");
    const pdfW = pdf.internal.pageSize.getWidth();
    const pdfH = (canvas.height * pdfW) / canvas.width;
    pdf.addImage(imgData, "PNG", 0, 0, pdfW, pdfH);
    pdf.save(`ledger-memo-${data.start_date}-${data.end_date}.pdf`);
  }

  return (
    <section className="results-section" id="results">
      {data.demo && (
        <div className="demo-banner">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 9v4m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" />
          </svg>
          <span>This is a demo analysis. <a href="#" onClick={(e) => { e.preventDefault(); localStorage.removeItem("demo_mode"); location.reload(); }}>Sign up</a> to save your reports.</span>
        </div>
      )}

      <div className="results-header">
        <div className="results-header-left">
          <p className="results-eyebrow">Underwriting Memo</p>
          <h2 id="memo-period">{data.start_date} — {data.end_date} ({data.num_months} mo)</h2>
        </div>
        <div className="results-header-right">
          <div id="risk-stamp" className={`risk-badge ${data.risk_band}`}>
            <span>{data.risk_band.toUpperCase()} RISK</span>
          </div>
          <button className="btn btn-ghost-secondary" onClick={handleExportPdf} title="Export as PDF">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
            PDF
          </button>
        </div>
      </div>

      {prevData && (
        <div className="trend-banner">
          <div className="trend-header">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" />
              <polyline points="17 6 23 6 23 12" />
            </svg>
            Trend vs previous report
            <span className="trend-period">{prevData.start_date} \u2013 {prevData.end_date}</span>
          </div>
          <div className="trend-metrics">
            <div className="trend-item">
              <span className="trend-label">Net cash flow</span>
              <span className={`trend-delta ${data.net_cash_flow >= prevData.net_cash_flow ? "trend-up" : "trend-down"}`}>
                {data.net_cash_flow >= prevData.net_cash_flow ? "+" : ""}{money(data.net_cash_flow - prevData.net_cash_flow, currency)}
              </span>
            </div>
            <div className="trend-item">
              <span className="trend-label">Risk score</span>
              <span className={`trend-delta ${data.risk_score <= prevData.risk_score ? "trend-up" : "trend-down"}`}>
                {data.risk_score <= prevData.risk_score ? "\u2193 " : "\u2191 "}{Math.abs(data.risk_score - prevData.risk_score)} pts
              </span>
            </div>
            <div className="trend-item">
              <span className="trend-label">Revenue volatility</span>
              <span className={`trend-delta ${data.revenue_volatility_pct <= prevData.revenue_volatility_pct ? "trend-up" : "trend-down"}`}>
                {data.revenue_volatility_pct <= prevData.revenue_volatility_pct ? "\u2193 " : "\u2191 "}{Math.abs(data.revenue_volatility_pct - prevData.revenue_volatility_pct)}%
              </span>
            </div>
            <div className="trend-item">
              <span className="trend-label">Top customer share</span>
              <span className={`trend-delta ${data.top_customer_share_pct <= prevData.top_customer_share_pct ? "trend-up" : "trend-down"}`}>
                {data.top_customer_share_pct <= prevData.top_customer_share_pct ? "\u2193 " : "\u2191 "}{Math.abs(data.top_customer_share_pct - prevData.top_customer_share_pct)}%
              </span>
            </div>
          </div>
        </div>
      )}
      <div className="metrics-grid">
        <div className="stat-card">
          <span className="stat-label">Total inflow</span>
          <span className="stat-value stat-positive" id="fig-inflow">{money(data.total_inflow, currency)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Total outflow</span>
          <span className="stat-value stat-negative" id="fig-outflow">{money(Math.abs(data.total_outflow), currency)}</span>
        </div>
        <div className="stat-card">
          <span className="stat-label">Net cash flow</span>
          <span className={`stat-value ${netClass}`} id="fig-net">{money(data.net_cash_flow, currency)}</span>
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
          <span className="stat-value score-value" id="fig-score"><AnimatedScore score={data.risk_score} /></span>
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

      <div className="card txn-card">
        <div className="card-header">
          <h3>Transactions</h3>
          <button className="btn-link" onClick={() => setShowTxns(!showTxns)}>
            {showTxns ? "Hide" : `Show${!data.demo ? " all" : ""}`}
          </button>
        </div>
        {showTxns && (
          <div className="card-body">
            {txnLoading ? (
              <div className="txn-loading">Loading transactions...</div>
            ) : sortedTxns.length > 0 ? (
              <div className="txn-table-wrap">
                <table className="txn-table">
                  <thead>
                    <tr>
                      <th onClick={() => handleSort("date")} className="sortable">
                        Date {sortKey === "date" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                      <th onClick={() => handleSort("amount")} className="sortable">
                        Amount {sortKey === "amount" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                      <th onClick={() => handleSort("counterparty")} className="sortable">
                        Counterparty {sortKey === "counterparty" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                      <th onClick={() => handleSort("category")} className="sortable">
                        Category {sortKey === "category" ? (sortDir === "asc" ? "▲" : "▼") : ""}
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedTxns.map((t) => (
                      <tr key={t.id}>
                        <td>{formatDate(t.date)}</td>
                        <td className={t.amount >= 0 ? "txn-positive" : "txn-negative"}>{money(t.amount, currency)}</td>
                        <td>{t.counterparty}</td>
                        <td><span className="txn-category">{t.category}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : data.demo ? (
              <p className="txn-empty">Transaction list is not available in demo mode.</p>
            ) : (
              <p className="txn-empty">No transactions found.</p>
            )}
          </div>
        )}
      </div>

      <div className="results-footer">
        <span className="footer-note">Every figure traces to a computed value, not a model guess.</span>
        <div className="results-footer-actions">
          <button className="btn btn-secondary" onClick={handleExportPdf}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            Export PDF
          </button>
          <button className="btn btn-secondary" onClick={onReset}>Analyze another file</button>
        </div>
      </div>
    </section>
  );
}
