import type { ReportSummary } from "../types/api";
import { BarChartIcon } from "./Icons";

function money(n: number, currency = "USD") {
  return new Intl.NumberFormat("en-US", {
    style: "currency", currency, maximumFractionDigits: 0,
  }).format(n);
}

function formatDate(iso: string) {
  const d = new Date(iso);
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

interface ReportsSectionProps {
  reports: ReportSummary[];
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
  onClearAll: () => void;
  onCompare?: () => void;
}

export function ReportsSection({ reports, onOpen, onDelete, onClearAll, onCompare }: ReportsSectionProps) {
  if (reports.length === 0) {
    return (
      <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
        <div className="upload-icon" style={{ margin: "0 auto 20px" }}>
          <BarChartIcon size={40} strokeWidth={1.5} />
        </div>
        <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>No reports yet</h2>
        <p style={{ color: "var(--text-muted)", fontSize: 13, maxWidth: 400, margin: "0 auto", lineHeight: 1.6 }}>
          Completed analyses will appear here. Upload a CSV or use the sample data to generate your first report.
        </p>
      </div>
    );
  }

  return (
    <div className="reports-section">
      <div className="reports-toolbar">
        <span className="reports-count">{reports.length} report{reports.length !== 1 ? "s" : ""}</span>
        <div className="reports-toolbar-right">
          {onCompare && reports.length >= 2 && (
            <button className="btn-link" onClick={onCompare}>Compare reports</button>
          )}
          <button className="btn-link" onClick={onClearAll} style={{ color: "var(--danger)" }}>
            Clear all
          </button>
        </div>
      </div>

      <div className="reports-list">
        {reports.map((report) => (
          <ReportCard
            key={report.id}
            report={report}
            onOpen={() => onOpen(report.id)}
            onDelete={() => onDelete(report.id)}
          />
        ))}
      </div>
    </div>
  );
}

interface ReportCardProps {
  report: ReportSummary;
  onOpen: () => void;
  onDelete: () => void;
}

function ReportCard({ report, onOpen, onDelete }: ReportCardProps) {
  const bandClass = report.risk_band;

  return (
    <div className="report-card" tabIndex={0} role="button" onClick={onOpen} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onOpen(); } }}>
      <div className="report-card-left">
        <div className="report-meta">
          <span className="report-period">{report.start_date} — {report.end_date}</span>
          <span className="report-date">{formatDate(report.created_at)}</span>
        </div>
        <div className="report-stats">
          <span className="report-stat">
            <span className="report-stat-label">Net</span>
            <span className={`report-stat-value${report.net_cash_flow >= 0 ? " text-success" : " text-danger"}`}>
              {money(report.net_cash_flow, report.currency)}
            </span>
          </span>
        </div>
      </div>
      <div className="report-card-right">
        <span className={`risk-badge ${bandClass}`} style={{ pointerEvents: "none" }}>
          {report.risk_band.toUpperCase()} RISK
        </span>
        <span className="report-score">{report.risk_score}</span>
        <button
          className="report-delete"
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          title="Delete report"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="3 6 5 6 21 6" />
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
