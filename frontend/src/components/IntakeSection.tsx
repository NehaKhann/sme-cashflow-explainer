import { useRef, useState, type FormEvent } from "react";
import { SAMPLE_CSV } from "../data/sample";

const CURRENCIES = [
  { code: "USD", label: "USD ($)" },
  { code: "EUR", label: "EUR (€)" },
  { code: "GBP", label: "GBP (£)" },
  { code: "JPY", label: "JPY (¥)" },
  { code: "CAD", label: "CAD (C$)" },
  { code: "AUD", label: "AUD (A$)" },
  { code: "CHF", label: "CHF (Fr)" },
  { code: "INR", label: "INR (₹)" },
  { code: "BRL", label: "BRL (R$)" },
  { code: "MXN", label: "MXN (MX$)" },
];

interface IntakeSectionProps {
  onAnalyze: (formData: FormData) => void;
  disabled: boolean;
  currency: string;
  onCurrencyChange: (currency: string) => void;
}

export function IntakeSection({ onAnalyze, disabled, currency, onCurrencyChange }: IntakeSectionProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [sampleMode, setSampleMode] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const ready = file !== null || sampleMode;

  function useFile(f: File) {
    setFile(f);
    setSampleMode(false);
    setError(null);
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    if (e.target.files?.[0]) useFile(e.target.files[0]);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) useFile(f);
  }

  function handleUseSample() {
    setSampleMode(true);
    setFile(null);
    setError(null);
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    const fd = new FormData();
    if (sampleMode) {
      const blob = new Blob([SAMPLE_CSV], { type: "text/csv" });
      fd.append("file", blob, "sample_transactions.csv");
    } else if (file) {
      fd.append("file", file);
    } else {
      return;
    }

    onAnalyze(fd);
  }

  return (
    <section className="intake-section" id="intake">
      <div className="card upload-card">
        <div className="card-body">
          <div className="upload-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
            </svg>
          </div>
          <h2>Upload transaction data</h2>
          <p className="upload-desc">
            Upload a CSV of your business transactions to generate a detailed cash-flow underwriting memo.
          </p>

          <div
            id="dropzone"
            className={`dropzone${dragOver ? " drag-over" : ""}`}
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
            onDragLeave={() => setDragOver(false)}
            onDrop={handleDrop}
          >
            <input ref={fileInputRef} type="file" accept=".csv" hidden onChange={handleFileChange} />
            <div className="dropzone-content">
              <span className="dropzone-action">Choose a CSV file</span>
              <span className="dropzone-hint">or drag and drop here</span>
            </div>
          </div>

          <div className="currency-selector">
            <label htmlFor="currency">Currency</label>
            <select id="currency" value={currency} onChange={(e) => onCurrencyChange(e.target.value)}>
              {CURRENCIES.map((c) => (
                <option key={c.code} value={c.code}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className="upload-options">
            <button type="button" className="btn-link" onClick={handleUseSample}>
              Use sample data instead
            </button>
            {file && <span className="file-chosen">{file.name}</span>}
            {sampleMode && <span className="file-chosen">Using built-in sample dataset</span>}
          </div>

          {error && <div className="error-banner">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={!ready || disabled}
            onClick={handleSubmit}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            Analyze cash flow
          </button>
        </div>
      </div>

      <div className="card info-card">
        <div className="card-body">
          <h3>Required CSV format</h3>
          <div className="info-grid">
            <div className="info-item">
              <code>date</code>
              <span>Transaction date</span>
            </div>
            <div className="info-item">
              <code>amount</code>
              <span>Signed amount (+ inflow, - outflow)</span>
            </div>
            <div className="info-item">
              <code>counterparty</code>
              <span>Payer or payee name</span>
            </div>
            <div className="info-item">
              <code>category</code>
              <span>Optional (e.g. revenue, rent)</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
