import type { AnalysisData, ApiHealthStatus } from "../types/api";

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
): Promise<AnalysisData> {
  const res = await fetch(`${apiBase}/api/analyze`, {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || "Analysis failed.");
  }
  return data as AnalysisData;
}
