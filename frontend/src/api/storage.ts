import type { AnalysisData, StoredReport } from "../types/api";

const STORAGE_KEY = "ledger_reports";
const MAX_REPORTS = 50;

function generateId(): string {
  try { return crypto.randomUUID(); } catch { /* fallback for HTTP */ }
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 10);
}

export function saveReport(data: AnalysisData, filename: string): StoredReport {
  const reports = loadReports();
  const report: StoredReport = {
    id: generateId(),
    createdAt: new Date().toISOString(),
    filename,
    data,
  };
  reports.unshift(report);
  const trimmed = reports.slice(0, MAX_REPORTS);
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
  } catch {
    if (trimmed.length > 1) {
      trimmed.pop();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(trimmed));
    }
  }
  return report;
}

export function loadReports(): StoredReport[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as StoredReport[];
  } catch {
    return [];
  }
}

export function deleteReport(id: string): void {
  const reports = loadReports().filter((r) => r.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(reports));
}

export function clearAllReports(): void {
  localStorage.removeItem(STORAGE_KEY);
}
