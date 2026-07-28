import type { ApiHealthStatus } from "../types/api";
import { GridIcon, UploadIcon, BarChartIcon, CloseIcon } from "./Icons";

export type Page = "dashboard" | "upload" | "reports";

interface SidebarProps {
  status: ApiHealthStatus;
  active: Page;
  onNavigate: (page: Page) => void;
  open: boolean;
  onClose: () => void;
}

const NAV_ITEMS: { page: Page; label: string; icon: React.ReactNode }[] = [
  { page: "dashboard", label: "Dashboard", icon: <GridIcon /> },
  { page: "upload", label: "Upload", icon: <UploadIcon /> },
  { page: "reports", label: "Reports", icon: <BarChartIcon /> },
];

export function Sidebar({ status, active, onNavigate, open, onClose }: SidebarProps) {
  function handleNav(page: Page) {
    onNavigate(page);
    onClose();
  }

  return (
    <>
      {open && <div className="sidebar-backdrop" onClick={onClose} />}
      <aside className={`sidebar${open ? " open" : ""}`}>
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
          <button className="sidebar-close" onClick={onClose} aria-label="Close menu">
            <CloseIcon />
          </button>
        </div>

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => (
            <a
              key={item.page}
              href="#"
              className={`nav-item${active === item.page ? " active" : ""}`}
              onClick={(e) => { e.preventDefault(); handleNav(item.page); }}
            >
              {item.icon}
              {item.label}
            </a>
          ))}
        </nav>

        <div className="sidebar-footer">
          <span className={`status-badge ${status.className}`}>
            <span className="status-dot" />
            <span className="status-label">{status.label}</span>
          </span>
        </div>
      </aside>
    </>
  );
}
