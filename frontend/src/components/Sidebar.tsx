import type { ApiHealthStatus } from "../types/api";

export type Page = "dashboard" | "upload" | "reports";

interface SidebarProps {
  status: ApiHealthStatus;
  active: Page;
  onNavigate: (page: Page) => void;
}

const NAV_ITEMS: { page: Page; label: string; icon: string }[] = [
  {
    page: "dashboard",
    label: "Dashboard",
    icon: '<rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="3" y="14" width="7" height="7" /><rect x="14" y="14" width="7" height="7" />',
  },
  {
    page: "upload",
    label: "Upload",
    icon: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />',
  },
  {
    page: "reports",
    label: "Reports",
    icon: '<path d="M12 20V10" /><path d="M18 20V4" /><path d="M6 20v-4" />',
  },
];

export function Sidebar({ status, active, onNavigate }: SidebarProps) {
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
        {NAV_ITEMS.map((item) => (
          <a
            key={item.page}
            href="#"
            className={`nav-item${active === item.page ? " active" : ""}`}
            onClick={(e) => { e.preventDefault(); onNavigate(item.page); }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" dangerouslySetInnerHTML={{ __html: item.icon }} />
            {item.label}
          </a>
        ))}
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
