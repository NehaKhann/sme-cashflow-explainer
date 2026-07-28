import type { ApiHealthStatus } from "../types/api";

interface SidebarProps {
  status: ApiHealthStatus;
}

export function Sidebar({ status }: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M3 3v18h18" />
            <path d="M7 16l4-8 4 4 4-6" />
          </svg>
        </div>
        <div className="brand-text">
          <span className="brand-title">Ledger</span>
          <span className="brand-sub">Underwriting</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <a href="#" className="nav-item active">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
            <rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />
          </svg>
          Dashboard
        </a>
        <a href="#" className="nav-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          Upload
        </a>
        <a href="#" className="nav-item">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" />
          </svg>
          Reports
        </a>
      </nav>

      <div className="sidebar-footer">
        <span id="api-status" className={`status-badge ${status.className}`}>
          <span className="status-dot" />
          <span className="status-label">{status.label}</span>
        </span>
      </div>
    </aside>
  );
}
