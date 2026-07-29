import { useState, useEffect, useCallback } from "react";

interface ToastData {
  id: number;
  message: string;
  type: "error" | "success";
}

let toastId = 0;
let addToastFn: ((msg: string, type: "error" | "success") => void) | null = null;

export function toast(msg: string, type: "error" | "success" = "error") {
  addToastFn?.(msg, type);
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  const add = useCallback((message: string, type: "error" | "success") => {
    const id = ++toastId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 4000);
  }, []);

  useEffect(() => {
    addToastFn = add;
    return () => { addToastFn = null; };
  }, [add]);

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container">
      {toasts.map((t) => (
        <div key={t.id} className={`toast toast-${t.type}`}>
          <span className="toast-icon">{t.type === "error" ? "!" : "✓"}</span>
          {t.message}
        </div>
      ))}
    </div>
  );
}
