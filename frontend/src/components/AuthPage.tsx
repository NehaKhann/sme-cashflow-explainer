import { useState } from "react";
import { useAuth } from "./AuthContext";
import { TrendingUpIcon } from "./Icons";

export function LoginPage({ onSwitch, onBack }: { onSwitch: () => void; onBack: () => void }) {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(email, password);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <button className="auth-back" onClick={onBack} type="button">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to home
        </button>
        <div className="auth-header">
          <TrendingUpIcon size={32} />
          <h1>Sign in to Ledger</h1>
          <p>View your cash-flow analysis history and run new reports.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required autoFocus />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="btn-primary btn-block" disabled={busy}>
            {busy ? "Signing in\u2026" : "Sign in"}
          </button>
        </form>
        <p className="auth-footer">
          No account?{" "}
          <button className="btn-link" onClick={onSwitch} type="button">
            Create one
          </button>
        </p>
      </div>
    </div>
  );
}

export function SignupPage({ onSwitch, onBack }: { onSwitch: () => void; onBack: () => void }) {
  const { signup } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signup(email, password, displayName);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Signup failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <button className="auth-back" onClick={onBack} type="button">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Back to home
        </button>
        <div className="auth-header">
          <TrendingUpIcon size={32} />
          <h1>Create your account</h1>
          <p>Start analyzing cash flow and generating underwriting memos.</p>
        </div>
        <form onSubmit={handleSubmit}>
          <label>
            Display name
            <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoFocus />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={8} />
          </label>
          {error && <div className="auth-error">{error}</div>}
          <button type="submit" className="btn-primary btn-block" disabled={busy}>
            {busy ? "Creating account\u2026" : "Create account"}
          </button>
        </form>
        <p className="auth-footer">
          Already have an account?{" "}
          <button className="btn-link" onClick={onSwitch} type="button">
            Sign in
          </button>
        </p>
      </div>
    </div>
  );
}
