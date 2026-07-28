import { useState, useEffect, useCallback } from "react";
import type { AnalysisData, ApiHealthStatus, ReportSummary } from "./types/api";
import { checkHealth, analyzeTransactions, fetchReports, fetchReport, deleteReportApi, clearAllReportsApi } from "./api/client";
import { AuthProvider, useAuth } from "./components/AuthContext";
import { LoginPage, SignupPage } from "./components/AuthPage";
import { LandingPage } from "./components/LandingPage";
import type { Page } from "./components/Sidebar";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { IntakeSection } from "./components/IntakeSection";
import { LoadingCard } from "./components/LoadingCard";
import { DashboardHome } from "./components/DashboardHome";
import { ResultsSection } from "./components/ResultsSection";
import { ReportsSection } from "./components/ReportsSection";
import { ComparePage } from "./components/ComparePage";
import "./App.css";

const INITIAL_STATUS: ApiHealthStatus = {
  ok: false,
  label: "Checking API\u2026",
  className: "status-unknown",
};

const TOPBAR_META: Record<Page | "compare", { title: string; desc: string }> = {
  dashboard: { title: "Dashboard", desc: "Overview of cash-flow analysis results." },
  upload: { title: "Upload", desc: "Upload transactions to generate an underwriting memo." },
  reports: { title: "Reports", desc: "View past analysis reports." },
  compare: { title: "Compare Reports", desc: "Side-by-side comparison of two reports." },
};

export default function App() {
  const [apiBase, setApiBase] = useState("http://localhost:8000");

  return (
    <AuthProvider apiBase={apiBase}>
      <AppInner apiBase={apiBase} onApiBaseChange={setApiBase} />
    </AuthProvider>
  );
}

type AuthPage = "landing" | "login" | "signup";

function AppInner({ apiBase, onApiBaseChange }: { apiBase: string; onApiBaseChange: (v: string) => void }) {
  const { user, loading, isDemo, enterDemo, exitDemo } = useAuth();
  const [page, setPage] = useState<Page>("dashboard");
  const [authPage, setAuthPage] = useState<AuthPage>("landing");
  const [apiStatus, setApiStatus] = useState<ApiHealthStatus>(INITIAL_STATUS);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisData | null>(null);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [currency, setCurrency] = useState("USD");

  const doHealthCheck = useCallback(async () => {
    const s = await checkHealth(apiBase);
    setApiStatus(s);
  }, [apiBase]);

  useEffect(() => { doHealthCheck(); }, [doHealthCheck]);

  useEffect(() => {
    if (user) refreshReports();
  }, [user]);

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
      const data = await analyzeTransactions(apiBase, formData, currency);
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

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
      </div>
    );
  }

  if (!user && !isDemo) {
    if (authPage === "landing") {
      return (
        <LandingPage
          onGetStarted={() => setAuthPage("login")}
          onSignIn={() => setAuthPage("login")}
          onTryDemo={enterDemo}
        />
      );
    }
    return (
      <div className="auth-layout">
        {authPage === "signup" ? (
          <SignupPage onSwitch={() => setAuthPage("login")} />
        ) : (
          <LoginPage onSwitch={() => setAuthPage("signup")} />
        )}
      </div>
    );
  }

  const currentPage = page as Page | "compare";
  const meta = TOPBAR_META[currentPage] || TOPBAR_META.dashboard;
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
        active={page === "compare" ? "reports" : page}
        onNavigate={setPage}
        open={mobileMenuOpen}
        onClose={() => setMobileMenuOpen(false)}
      />
      <main className="main">
        <Topbar
          apiBase={apiBase}
          onApiBaseChange={onApiBaseChange}
          title={title}
          description={desc}
          onMenuToggle={() => setMobileMenuOpen(!mobileMenuOpen)}
        />
        <div className="content">
          {analyzing ? (
            <LoadingCard />
          ) : page === "compare" ? (
            <ComparePage apiBase={apiBase} onNavigate={setPage} />
          ) : page === "dashboard" && results ? (
            <ResultsSection data={results} onReset={handleReset} apiBase={apiBase} />
          ) : page === "dashboard" ? (
            <DashboardHome onNavigate={setPage} />
          ) : page === "upload" ? (
            <IntakeSection onAnalyze={handleAnalyze} disabled={analyzing} currency={currency} onCurrencyChange={setCurrency} />
          ) : (
            <ReportsSection
              reports={reports}
              onOpen={handleOpenReport}
              onDelete={handleDeleteReport}
              onClearAll={handleClearAll}
              onCompare={() => setPage("compare")}
            />
          )}
        </div>
      </main>
    </div>
  );
}
