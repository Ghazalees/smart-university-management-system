/** Provides the reusable Toast interface component and accessibility behavior. */

import { useCallback, useMemo, useState, type ReactNode } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { ToastContext } from "../app/toast-context";

interface ToastMessage { id: number; text: string; tone: "success" | "error" }

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);
  const show = useCallback((text: string, tone: "success" | "error" = "success") => {
    const id = Date.now();
    setMessages((current) => [...current, { id, text, tone }]);
    window.setTimeout(() => setMessages((current) => current.filter((message) => message.id !== id)), 3600);
  }, []);
  const value = useMemo(() => ({ show }), [show]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {messages.map((message) => (
          <div key={message.id} className={`toast toast-${message.tone}`}>
            {message.tone === "success" ? <CheckCircle2 /> : <XCircle />}
            <span>{message.text}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
