import { useState, useEffect, useCallback } from "react";
import type { AnalysisData, ApiHealthStatus } from "./types/api";
import { checkHealth, analyzeTransactions } from "./api/client";
import type { Page } from "./components/Sidebar";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { IntakeSection } from "./components/IntakeSection";
import { LoadingCard } from "./components/LoadingCard";
import { DashboardHome } from "./components/DashboardHome";
import { ResultsSection } from "./components/ResultsSection";
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

  const doHealthCheck = useCallback(async () => {
    const s = await checkHealth(apiBase);
    setApiStatus(s);
  }, [apiBase]);

  useEffect(() => { doHealthCheck(); }, [doHealthCheck]);

  async function handleAnalyze(formData: FormData) {
    setAnalyzing(true);
    try {
      const data = await analyzeTransactions(apiBase, formData);
      setResults(data);
      setPage("dashboard");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not reach the API.";
      alert(msg);
    } finally {
      setAnalyzing(false);
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
      <Sidebar status={apiStatus} active={page} onNavigate={setPage} />
      <main className="main">
        <Topbar
          apiBase={apiBase}
          onApiBaseChange={setApiBase}
          title={title}
          description={desc}
        />
        <div className="content">
          {analyzing ? (
            <LoadingCard />
          ) : page === "dashboard" && results ? (
            <ResultsSection data={results} onReset={handleReset} />
          ) : page === "dashboard" ? (
            <DashboardHome />
          ) : page === "upload" ? (
            <IntakeSection onAnalyze={handleAnalyze} disabled={analyzing} />
          ) : (
            <div className="card" style={{ padding: "48px 24px", textAlign: "center" }}>
              <div className="upload-icon" style={{ margin: "0 auto 20px" }}>
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" />
                </svg>
              </div>
              <h2 style={{ fontSize: 20, fontWeight: 600, marginBottom: 8 }}>Reports</h2>
              <p style={{ color: "var(--text-muted)", fontSize: 13, maxWidth: 400, margin: "0 auto", lineHeight: 1.6 }}>
                Analysis history is not yet persisted. This will show past underwriting memos once a database is connected.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
