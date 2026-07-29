import { useState, useEffect, useCallback } from "react";

export function useDarkMode(): [boolean, () => void] {
  const [dark, setDark] = useState(() => localStorage.getItem("dark_mode") === "true");

  useEffect(() => {
    document.documentElement.classList.toggle("dark-mode", dark);
    localStorage.setItem("dark_mode", String(dark));
  }, [dark]);

  const toggle = useCallback(() => setDark((d) => !d), []);

  return [dark, toggle];
}
