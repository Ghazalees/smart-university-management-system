/** Provides the reusable ui interface component and accessibility behavior. */

import { useEffect, useId, useMemo, useRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode } from "react";
import { AlertCircle, ArrowDownRight, ArrowUpRight, Inbox, LoaderCircle, Minus, X } from "lucide-react";

export function Button({ className = "", variant = "primary", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "ghost" | "danger" }) {
  return <button className={`button button-${variant} ${className}`} {...props} />;
}

export function Input({ label, error, hint, ...props }: InputHTMLAttributes<HTMLInputElement> & { label?: string; error?: string; hint?: string }) {
  const id = useId();
  return <label className="field" htmlFor={props.id || id}>{label ? <span className="field-label">{label}</span> : null}<input id={props.id || id} className={`input ${error ? "input-error" : ""}`} aria-invalid={Boolean(error)} {...props} />{hint && !error ? <span className="field-hint">{hint}</span> : null}{error ? <span className="field-error">{error}</span> : null}</label>;
}

export function Select({ label, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string; children: ReactNode }) {
  const id = useId();
  return <label className="field" htmlFor={props.id || id}>{label ? <span className="field-label">{label}</span> : null}<select id={props.id || id} className="input" {...props}>{children}</select></label>;
}

export function Textarea({ label, hint, ...props }: React.TextareaHTMLAttributes<HTMLTextAreaElement> & { label?: string; hint?: string }) {
  const id = useId();
  return <label className="field" htmlFor={props.id || id}>{label ? <span className="field-label">{label}</span> : null}<textarea id={props.id || id} className="input textarea" {...props} />{hint ? <span className="field-hint">{hint}</span> : null}</label>;
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) { return <section className={`card ${className}`}>{children}</section>; }
export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: string }) { return <span className={`badge badge-${tone}`}>{children}</span>; }

const statusTone: Record<string, string> = {
  approved: "success", answered: "success", published: "success", active: "success", completed: "success", current: "success", resolved: "success",
  pending: "warning", draft: "warning", needs_revision: "warning", review_due_soon: "warning", in_progress: "warning",
  rejected: "danger", failed: "danger", archived: "danger", expired: "danger", review_overdue: "danger", urgent: "danger",
  under_review: "info", escalated: "info", scheduled: "info", triaged: "info",
};
export function StatusBadge({ status }: { status: string }) { return <Badge tone={statusTone[status.toLowerCase()] || "neutral"}>{status.replaceAll("_", " ")}</Badge>; }

export function PageHeader({ title, description, action, eyebrow = "Smart University" }: { title: string; description: string; action?: ReactNode; eyebrow?: string }) {
  return <header className="page-header"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1><p>{description}</p></div>{action ? <div className="page-actions">{action}</div> : null}</header>;
}

export function Skeleton({ className = "" }: { className?: string }) { return <span className={`skeleton ${className}`} aria-hidden="true" />; }
export function DashboardSkeleton() { return <div className="page-stack"><div><Skeleton className="skeleton-kicker" /><Skeleton className="skeleton-title" /><Skeleton className="skeleton-copy" /></div><div className="metric-grid">{[1,2,3,4].map((n) => <Card key={n} className="metric-card"><Skeleton className="skeleton-icon" /><div className="skeleton-flex"><Skeleton className="skeleton-number" /><Skeleton className="skeleton-label" /></div></Card>)}</div><div className="dashboard-grid"><Card><Skeleton className="skeleton-panel" /></Card><Card><Skeleton className="skeleton-panel" /></Card></div></div>; }

export function LoadingState({ label = "Loading" }: { label?: string }) { return <div className="state-card"><LoaderCircle className="spin" /><strong>{label}</strong><span>Please wait a moment.</span></div>; }
export function EmptyState({ title = "Nothing here yet", message = "New items will appear here.", action }: { title?: string; message?: string; action?: ReactNode }) { return <div className="state-card"><span className="state-illustration"><Inbox /></span><strong>{title}</strong><span>{message}</span>{action}</div>; }
export function ErrorState({ message = "Something went wrong.", action }: { message?: string; action?: ReactNode }) { return <div className="state-card state-error"><span className="state-illustration"><AlertCircle /></span><strong>Unable to load</strong><span>{message}</span>{action}</div>; }

export function KpiCard({ label, value, icon, delta, tone = "primary", caption }: { label: string; value: ReactNode; icon: ReactNode; delta?: number | null; tone?: string; caption?: string }) {
  return <Card className={`metric-card metric-${tone}`}><span className="metric-icon">{icon}</span><div className="metric-copy"><span>{label}</span><strong>{value}</strong>{caption ? <small>{caption}</small> : null}</div>{delta !== undefined && delta !== null ? <span className={`metric-delta ${delta > 0 ? "delta-up" : delta < 0 ? "delta-down" : "delta-flat"}`}>{delta > 0 ? <ArrowUpRight /> : delta < 0 ? <ArrowDownRight /> : <Minus />}{Math.abs(delta)}%</span> : null}</Card>;
}

export function ProgressRing({ value, label, size = 116 }: { value: number; label: string; size?: number }) {
  const safe = Math.max(0, Math.min(100, value));
  const radius = 42; const circumference = 2 * Math.PI * radius;
  return <div className="progress-ring" style={{ width: size, height: size }} role="img" aria-label={`${label}: ${safe}%`}><svg viewBox="0 0 100 100"><circle className="ring-track" cx="50" cy="50" r={radius} /><circle className="ring-value" cx="50" cy="50" r={radius} strokeDasharray={circumference} strokeDashoffset={circumference * (1 - safe / 100)} /></svg><div><strong>{safe}%</strong><span>{label}</span></div></div>;
}

export function MiniBarChart({ data, label = "Trend" }: { data: Array<{ label: string; value: number }>; label?: string }) {
  const max = Math.max(...data.map((item) => item.value), 1);
  return <div className="mini-chart" role="img" aria-label={label}>{data.map((item) => <div className="mini-bar-wrap" key={item.label} title={`${item.label}: ${item.value}`}><span className="mini-bar" style={{ height: `${Math.max(7, item.value / max * 100)}%` }} /><small>{item.label}</small></div>)}</div>;
}

export function Sparkline({ values }: { values: number[] }) {
  const points = useMemo(() => {
    if (!values.length) return "";
    const max = Math.max(...values, 1); const min = Math.min(...values, 0); const range = max - min || 1;
    return values.map((value, index) => `${(index / Math.max(values.length - 1, 1)) * 100},${36 - ((value - min) / range) * 32}`).join(" ");
  }, [values]);
  return <svg className="sparkline" viewBox="0 0 100 40" preserveAspectRatio="none" aria-hidden="true"><polyline points={points} fill="none" /></svg>;
}

export function Modal({ title, children, onClose, wide = false }: { title: string; children: ReactNode; onClose: () => void; wide?: boolean }) {
  const modalRef = useRef<HTMLElement>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    const modal = modalRef.current;
    const focusSelector = [
      "[data-autofocus]",
      "input:not([type='hidden']):not([disabled])",
      "select:not([disabled])",
      "textarea:not([disabled])",
      "button:not([data-modal-close]):not([disabled])",
      "[tabindex]:not([tabindex='-1'])",
    ].join(", ");
    modal?.querySelector<HTMLElement>(focusSelector)?.focus();

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onCloseRef.current();
        return;
      }
      if (event.key !== "Tab" || !modal) return;
      const controls = Array.from(modal.querySelectorAll<HTMLElement>("button, input, select, textarea, [tabindex]:not([tabindex='-1'])"))
        .filter((element) => !element.hasAttribute("disabled") && element.getAttribute("aria-hidden") !== "true");
      if (!controls.length) return;
      const first = controls[0]; const last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", handleKey);
    return () => {
      document.removeEventListener("keydown", handleKey);
      document.body.style.overflow = previousOverflow;
      previous?.focus();
    };
  }, []);

  function closeFromBackdrop(event: React.MouseEvent<HTMLDivElement>) {
    if (event.target === event.currentTarget) onCloseRef.current();
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={closeFromBackdrop}><section ref={modalRef} className={`modal ${wide ? "modal-wide" : ""}`} role="dialog" aria-modal="true" aria-label={title}><header><h2>{title}</h2><button type="button" className="icon-button" data-modal-close onClick={() => onCloseRef.current()} aria-label={`Close ${title}`}><X /></button></header>{children}</section></div>;
}

export function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) {
  if (pages <= 1) return null;
  return <div className="pagination"><Button variant="secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>Previous</Button><span>Page {page} of {pages}</span><Button variant="secondary" disabled={page >= pages} onClick={() => onChange(page + 1)}>Next</Button></div>;
}
