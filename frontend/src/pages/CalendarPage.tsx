/** Renders the CalendarPage workspace and coordinates its API-driven interactions. */

import { useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, Clock3, MapPin } from "lucide-react";
import { Link } from "react-router-dom";
import { useCalendarQuery } from "../services/api";
import { Button, Card, EmptyState, ErrorState, PageHeader, Skeleton, StatusBadge } from "../components/ui";
import type { CalendarEvent } from "../types";

function startOfMonth(date: Date) { return new Date(date.getFullYear(), date.getMonth(), 1); }
export function CalendarPage() {
  const [cursor, setCursor] = useState(startOfMonth(new Date()));
  const range = useMemo(() => ({ start: new Date(cursor.getFullYear(), cursor.getMonth(), -6), end: new Date(cursor.getFullYear(), cursor.getMonth() + 1, 7, 23, 59, 59) }), [cursor]);
  const { start, end } = range;
  const { data, isLoading, error } = useCalendarQuery({ start: start.toISOString(), end: end.toISOString() });
  const events = useMemo(() => data?.data.events || [], [data]);
  const days = useMemo(() => Array.from({ length: 42 }, (_, index) => { const value = new Date(start); value.setDate(start.getDate() + index); return value; }), [start]);
  const byDay = useMemo(() => { const map = new Map<string, CalendarEvent[]>(); events.forEach((event) => { const key = new Date(event.start).toDateString(); map.set(key, [...(map.get(key) || []), event]); }); return map; }, [events]);
  return <div className="page-stack"><PageHeader title="University calendar" description="Classes, exams, document reviews and workflow milestones in one role-aware timeline." action={<div className="calendar-controls"><Button variant="secondary" onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() - 1, 1))}><ChevronLeft /></Button><strong>{cursor.toLocaleString(undefined, { month: "long", year: "numeric" })}</strong><Button variant="secondary" onClick={() => setCursor(new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1))}><ChevronRight /></Button></div>} />
    {error ? <ErrorState /> : <Card className="calendar-card">{isLoading ? <div className="calendar-grid">{days.map((_, index) => <Skeleton key={index} className="calendar-skeleton" />)}</div> : <><div className="calendar-weekdays">{["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map((day) => <span key={day}>{day}</span>)}</div><div className="calendar-grid">{days.map((day) => { const dayEvents = byDay.get(day.toDateString()) || []; const outside = day.getMonth() !== cursor.getMonth(); const today = day.toDateString() === new Date().toDateString(); return <article key={day.toISOString()} className={`calendar-day ${outside ? "calendar-outside" : ""} ${today ? "calendar-today" : ""}`}><header><span>{day.getDate()}</span>{dayEvents.length ? <em>{dayEvents.length}</em> : null}</header><div>{dayEvents.slice(0,3).map((event) => <Link to={event.url} className={`calendar-event event-${event.type}`} key={event.id}><strong>{event.title}</strong><small>{new Date(event.start).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}{event.location ? ` · ${event.location}` : ""}</small></Link>)}{dayEvents.length > 3 ? <small className="more-events">+{dayEvents.length - 3} more</small> : null}</div></article>; })}</div></>}</Card>}
    <section className="calendar-agenda"><div className="panel-heading"><div><p className="eyebrow">Agenda</p><h2>Upcoming priorities</h2></div><CalendarDays /></div>{!events.length ? <EmptyState title="No upcoming events" /> : events.slice(0,8).map((event) => <Link className="agenda-row" to={event.url} key={event.id}><span className={`agenda-icon event-${event.type}`}><CalendarDays /></span><div><strong>{event.title}</strong><p><Clock3 />{new Date(event.start).toLocaleString()} {event.location ? <><MapPin />{event.location}</> : null}</p></div><StatusBadge status={event.status} /></Link>)}</section>
  </div>;
}
