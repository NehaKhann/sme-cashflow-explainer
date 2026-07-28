import type { AnalysisData, ApiHealthStatus, ReportSummary, ReportDetail, AuthResponse, User } from "../types/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function apiFetch(apiBase: string, path: string, options: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...authHeaders(),
    ...(options.headers as Record<string, string> || {}),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  const res = await fetch(`${apiBase}${path}`, { ...options, headers });
  let data: unknown = null;
  const ct = res.headers.get("content-type") || "";
  if (ct.includes("application/json")) {
    data = await res.json().catch(() => null);
  }
  if (!res.ok) {
    const detail = data && typeof data === "object" && "detail" in data
      ? (data as Record<string, unknown>).detail
      : `Request failed: ${res.status}`;
    throw new Error(String(detail));
  }
  return data;
}

export async function checkHealth(apiBase: string): Promise<ApiHealthStatus> {
  try {
    const data = await apiFetch(apiBase, "/health");
    if (data && typeof data === "object" && "status" in data) {
      return { ok: true, label: "API connected", className: "status-ok" };
    }
    throw new Error("bad status");
  } catch {
    return { ok: false, label: "API unreachable", className: "status-down" };
  }
}

export async function analyzeTransactions(
  apiBase: string,
  formData: FormData,
): Promise<AnalysisData & { report_id: string }> {
  return apiFetch(apiBase, "/api/analyze", { method: "POST", body: formData }) as Promise<AnalysisData & { report_id: string }>;
}

export async function fetchReports(apiBase: string): Promise<ReportSummary[]> {
  return apiFetch(apiBase, "/api/reports") as Promise<ReportSummary[]>;
}

export async function fetchReport(apiBase: string, id: string): Promise<ReportDetail> {
  return apiFetch(apiBase, `/api/reports/${id}`) as Promise<ReportDetail>;
}

export async function deleteReportApi(apiBase: string, id: string): Promise<void> {
  await apiFetch(apiBase, `/api/reports/${id}`, { method: "DELETE" });
}

export async function clearAllReportsApi(apiBase: string): Promise<void> {
  await apiFetch(apiBase, "/api/reports", { method: "DELETE" });
}

export async function signupApi(apiBase: string, email: string, password: string, displayName: string): Promise<AuthResponse> {
  return apiFetch(apiBase, "/api/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, display_name: displayName }),
  }) as Promise<AuthResponse>;
}

export async function loginApi(apiBase: string, email: string, password: string): Promise<AuthResponse> {
  return apiFetch(apiBase, "/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  }) as Promise<AuthResponse>;
}

export async function getMeApi(apiBase: string): Promise<User> {
  return apiFetch(apiBase, "/api/auth/me") as Promise<User>;
}
