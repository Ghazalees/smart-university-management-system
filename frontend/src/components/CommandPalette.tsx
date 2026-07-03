/** Provides the reusable CommandPalette interface component and accessibility behavior. */

import { useEffect, useMemo, useState } from "react";
import { BookOpen, CalendarDays, FileText, Search, UserRound, Workflow, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useGlobalSearchQuery } from "../services/api";
import { EmptyState, Skeleton } from "./ui";

const icons: Record<string, typeof FileText> = { document: FileText, class: CalendarDays, workflow: Workflow, user: UserRound, course: BookOpen };

export function CommandPalette({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const { data, isFetching } = useGlobalSearchQuery({ q: query, limit: 6 }, { skip: !open || query.trim().length < 2 });
  function close() { setQuery(""); onClose(); }
  useEffect(() => {
    function key(event: KeyboardEvent) { if (event.key === "Escape") onClose(); }
    document.addEventListener("keydown", key); return () => document.removeEventListener("keydown", key);
  }, [onClose]);
  const grouped = useMemo(() => {
    const result = new Map<string, NonNullable<typeof data>["data"]["results"]>();
    for (const item of data?.data.results || []) result.set(item.result_type, [...(result.get(item.result_type) || []), item]);
    return [...result.entries()];
  }, [data]);
  if (!open) return null;
  return <div className="command-backdrop" onMouseDown={close}><section className="command-palette" onMouseDown={(event) => event.stopPropagation()} role="dialog" aria-modal="true" aria-label="Global search">
    <header><Search /><input autoFocus value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search people, classes, documents and requests…" /><kbd>ESC</kbd><button className="icon-button" onClick={close}><X /></button></header>
    <div className="command-results">
      {query.length < 2 ? <div className="command-hint"><strong>Search everything you can access</strong><span>Try a course code, person, policy or request number.</span><div><kbd>Ctrl</kbd><kbd>K</kbd><span>opens search anywhere</span></div></div> : isFetching ? <>{[1,2,3,4].map((item) => <div className="command-skeleton" key={item}><Skeleton className="skeleton-icon" /><div><Skeleton className="skeleton-copy" /><Skeleton className="skeleton-label" /></div></div>)}</> : !grouped.length ? <EmptyState title="No authorized results" message="Try a broader keyword or a different phrase." /> : grouped.map(([type, items]) => <section className="command-group" key={type}><h3>{type}</h3>{items.map((item) => { const Icon = icons[item.result_type] || Search; return <button key={`${item.result_type}-${item.identifier}`} onClick={() => { navigate(item.url); close(); }}><span><Icon /></span><div><strong>{item.title}</strong><small>{item.subtitle}</small></div><em>Open</em></button>; })}</section>)}
    </div>
  </section></div>;
}
