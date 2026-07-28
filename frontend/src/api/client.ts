import type { AnalysisData, ApiHealthStatus, ReportSummary, ReportDetail } from "../types/api";

export async function checkHealth(apiBase: string): Promise<ApiHealthStatus> {
  try {
    const res = await fetch(`${apiBase}/health`, { method: "GET" });
    if (res.ok) {
      return { ok: true, label: "API connected", className: "status-ok" };
    }
    throw new Error("bad status");
  } catch {
    return { ok: false, label: "API unreachable", className: "status-down" };
  }
}

export async function analyzeTransactions(
  apiBase: string,
  formData: FormData
): Promise<AnalysisData & { report_id: string }> {
  const res = await fetch(`${apiBase}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Analysis failed.");
  }
  return data as AnalysisData & { report_id: string };
}

export async function fetchReports(apiBase: string): Promise<ReportSummary[]> {
  const res = await fetch(`${apiBase}/api/reports`);
  if (!res.ok) throw new Error("Failed to fetch reports.");
  return res.json();
}

export async function fetchReport(apiBase: string, id: string): Promise<ReportDetail> {
  const res = await fetch(`${apiBase}/api/reports/${id}`);
  if (!res.ok) throw new Error("Report not found.");
  return res.json();
}

export async function deleteReportApi(apiBase: string, id: string): Promise<void> {
  const res = await fetch(`${apiBase}/api/reports/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete report.");
}

export async function clearAllReportsApi(apiBase: string): Promise<void> {
  const res = await fetch(`${apiBase}/api/reports`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to clear reports.");
}
