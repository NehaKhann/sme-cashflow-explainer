import { useState, useEffect } from "react";
import type { ApiHealthStatus } from "../types/api";
import { GridIcon, UploadIcon, BarChartIcon, CloseIcon, LogOutIcon } from "./Icons";
import { useAuth } from "./AuthContext";

export type Page = "dashboard" | "upload" | "reports";

interface SidebarProps {
  status: ApiHealthStatus;
  active: Page;
  onNavigate: (page: Page) => void;
  open: boolean;
  onClose: () => void;
  onAuthAction?: (action: "login" | "signup") => void;
}

const NAV_ITEMS: { page: Page | "compare"; label: string; icon: React.ReactNode }[] = [
  { page: "dashboard", label: "Dashboard", icon: <GridIcon /> },
  { page: "upload", label: "Upload", icon: <UploadIcon /> },
  { page: "reports", label: "Reports", icon: <BarChartIcon /> },
];

export function Sidebar({ status, active, onNavigate, open, onClose, onAuthAction }: SidebarProps) {
  const { user, isDemo, logout } = useAuth();
  const [dark, setDark] = useState(() => localStorage.getItem("dark_mode") === "true");

  useEffect(() => {
    document.documentElement.classList.toggle("dark-mode", dark);
    localStorage.setItem("dark_mode", String(dark));
  }, [dark]);

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
          {user && (
            <div className="sidebar-user">
              <span className="sidebar-user-name">{user.display_name || user.email}</span>
              <button className="btn-logout" onClick={logout} title="Sign out">
                <LogOutIcon size={14} />
                Sign out
              </button>
            </div>
          )}
          {isDemo && onAuthAction && (
            <div className="sidebar-demo-actions">
              <span className="sidebar-demo-label">Demo mode</span>
              <button className="btn-logout" onClick={() => onAuthAction("signup")} title="Create account">
                Create account
              </button>
              <button className="btn-logout" onClick={() => onAuthAction("login")} title="Sign in">
                Sign in
              </button>
            </div>
          )}
          <div className="sidebar-actions">
            <button className="btn-dark-toggle" onClick={() => setDark(!dark)} title="Toggle dark mode">
              {dark ? (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="5" />
                  <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                  <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                  <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                  <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                </svg>
              ) : (
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                </svg>
              )}
              {dark ? "Light mode" : "Dark mode"}
            </button>
          </div>
          <span className={`status-badge ${status.className}`}>
            <span className="status-dot" />
            <span className="status-label">{status.label}</span>
          </span>
        </div>
      </aside>
    </>
  );
}
