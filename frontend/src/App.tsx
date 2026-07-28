import { useState, useEffect, useCallback } from "react";
import type { AnalysisData, ApiHealthStatus, ReportSummary } from "./types/api";
import { checkHealth, analyzeTransactions, fetchReports, fetchReport, deleteReportApi, clearAllReportsApi } from "./api/client";
import type { Page } from "./components/Sidebar";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { IntakeSection } from "./components/IntakeSection";
import { LoadingCard } from "./components/LoadingCard";
import { DashboardHome } from "./components/DashboardHome";
import { ResultsSection } from "./components/ResultsSection";
import { ReportsSection } from "./components/ReportsSection";
import "./App.css";

const INITIAL_STATUS: ApiHealthStatus = {
  ok: false,
  label: "Checking API\u2026",
  className: "status-unknown",
};

const TOPBAR_META: Record<Page, { title: string; desc: string }> = {
  dashboard: { title: "Dashboard", desc: "Overview of cash-flow analysis results." },
  upload: { title: "Upload", desc: "Upload transactions to generate an underwriting memo." },
  reports: { title: "Reports", desc: "View past analysis reports." },
};

export default function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [apiBase, setApiBase] = useState("http://localhost:8000");
  const [apiStatus, setApiStatus] = useState<ApiHealthStatus>(INITIAL_STATUS);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisData | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const doHealthCheck = useCallback(async () => {
    const s = await checkHealth(apiBase);
    setApiStatus(s);
  }, [apiBase]);

  useEffect(() => { doHealthCheck(); }, [doHealthCheck]);

  async function refreshReports() {
    try {
      const list = await fetchReports(apiBase);
      setReports(list);
    } catch {
      // silently fail
    }
  }

  async function handleAnalyze(formData: FormData) {
    setAnalyzing(true);
    try {
      const data = await analyzeTransactions(apiBase, formData);
      setResults(data);
      setPage("dashboard");
      await refreshReports();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not reach the API.";
      alert(msg);
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleOpenReport(id: string) {
    try {
      const detail = await fetchReport(apiBase, id);
      setResults(detail.raw_data);
      setPage("dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not load report.";
      alert(msg);
    }
  }

  async function handleDeleteReport(id: string) {
    try {
      await deleteReportApi(apiBase, id);
      await refreshReports();
    } catch {
      // silently fail
    }
  }

  async function handleClearAll() {
    try {
      await clearAllReportsApi(apiBase);
      await refreshReports();
    } catch {
      // silently fail
    }
  }

  function handleReset() {
    setResults(null);
    setPage("upload");
  }

  const meta = TOPBAR_META[page];
  let title = meta.title;
  let desc = meta.desc;

  if (page === "dashboard" && results) {
    title = "Underwriting Memo";
    desc = `${results.start_date} \u2014 ${results.end_date} (${results.num_months} months)`;
  }

  return (
    <div className="layout">
      <Sidebar
        status={apiStatus}
        active={page}
        onNavigate={setPage}
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />
      <main className="main">
        <Topbar
          apiBase={apiBase}
          onApiBaseChange={setApiBase}
          title={title}
          description={desc}
          onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)}
        />
        <div className="content">
          {analyzing ? (
            <LoadingCard />
          ) : page === "dashboard" && results ? (
            <ResultsSection data={results} onReset={handleReset} />
          ) : page === "dashboard" ? (
            <DashboardHome onNavigate={setPage} />
          ) : page === "upload" ? (
            <IntakeSection onAnalyze={handleAnalyze} disabled={analyzing} />
          ) : (
            <ReportsSection
              reports={reports}
              onOpen={handleOpenReport}
              onDelete={handleDeleteReport}
              onClearAll={handleClearAll}
            />
          )}
        </div>
      </main>
    </div>
  );
}
