import { useState, useEffect, useCallback } from "react";
import type { AnalysisData, ApiHealthStatus } from "./types/api";
import { checkHealth, analyzeTransactions } from "./api/client";
import { Sidebar } from "./components/Sidebar";
import { Topbar } from "./components/Topbar";
import { IntakeSection } from "./components/IntakeSection";
import { LoadingCard } from "./components/LoadingCard";
import { ResultsSection } from "./components/ResultsSection";
import "./App.css";

type View = "intake" | "loading" | "results";

const INITIAL_STATUS: ApiHealthStatus = {
  ok: false,
  label: "Checking API…",
  className: "status-unknown",
};

export default function App() {
  const [view, setView] = useState<View>("intake");
  const [apiBase, setApiBase] = useState("http://localhost:8000");
  const [apiStatus, setApiStatus] = useState<ApiHealthStatus>(INITIAL_STATUS);
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<AnalysisData | null>(null);

  const doHealthCheck = useCallback(async () => {
    const s = await checkHealth(apiBase);
    setApiStatus(s);
  }, [apiBase]);

  useEffect(() => { doHealthCheck(); }, [doHealthCheck]);

  function handleApiBaseChange(value: string) {
    setApiBase(value);
  }

  async function handleAnalyze(formData: FormData) {
    setAnalyzing(true);
    setView("loading");
    try {
      const data = await analyzeTransactions(apiBase, formData);
      setResults(data);
      setView("results");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Could not reach the API.";
      setView("intake");
      alert(msg);
    } finally {
      setAnalyzing(false);
    }
  }

  function handleReset() {
    setResults(null);
    setView("intake");
  }

  return (
    <div className="layout">
      <Sidebar status={apiStatus} />
      <main className="main">
        <Topbar
          apiBase={apiBase}
          onApiBaseChange={handleApiBaseChange}
          title={view === "results" && results
            ? "Underwriting Memo"
            : "Cash-Flow Analysis"
          }
          description={view === "results" && results
            ? `${results.start_date} — ${results.end_date} (${results.num_months} months)`
            : "Upload transactions to generate an underwriting memo."
          }
        />
        <div className="content">
          {view === "intake" && (
            <IntakeSection onAnalyze={handleAnalyze} disabled={analyzing} />
          )}
          {view === "loading" && <LoadingCard />}
          {view === "results" && results && (
            <ResultsSection data={results} onReset={handleReset} />
          )}
        </div>
      </main>
    </div>
  );
}
