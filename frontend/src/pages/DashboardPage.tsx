/** Renders the DashboardPage workspace and coordinates its API-driven interactions. */

import { Activity, BookOpen, Bot, CheckCircle2, FileText, GraduationCap, Lightbulb, Timer, TrendingUp, Users, Workflow } from "lucide-react";
import { Link } from "react-router-dom";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import { useActivityFeedQuery, useDashboardQuery } from "../services/api";
import { Card, DashboardSkeleton, ErrorState, KpiCard, MiniBarChart, ProgressRing, Sparkline, StatusBadge } from "../components/ui";
import { formatDate } from "../app/formatters";
import type { AcademicRecommendation, ActivityItem, DegreeProgress } from "../types";

const iconMap = { users: Users, documents: FileText, my_questions: Bot, my_requests: Workflow, classes: BookOpen, upcoming_exams: Timer, grades: GraduationCap, grades_recorded: CheckCircle2, pending_workflows: Activity, students: Users, ungraded: Timer };
const labels: Record<string, string> = { users: "Active users", documents: "Published knowledge", my_questions: "My questions", my_requests: "My requests", classes: "Active classes", upcoming_exams: "Upcoming exams", grades: "Available grades", grades_recorded: "Grades recorded", pending_workflows: "Requests awaiting action", students: "Students reached", ungraded: "Ungraded students" };

function asObject(value: unknown): Record<string, unknown> { return value && typeof value === "object" ? value as Record<string, unknown> : {}; }
function ActivityFeed({ items }: { items: ActivityItem[] }) { return <Card className="activity-panel"><div className="panel-heading"><div><p className="eyebrow">Live operations</p><h2>Recent activity</h2></div><Activity /></div><div className="activity-feed">{items.length ? items.map((item) => <div className="activity-row" key={item.id}><span className="activity-pulse" /><div><strong>{item.action.replaceAll(".", " · ").replaceAll("_", " ")}</strong><p>{item.actor}{item.entity_type ? ` updated ${item.entity_type}` : ""}</p></div><time>{formatDate(item.created_at)}</time></div>) : <p className="muted-copy">Activity will appear as you use the system.</p>}</div></Card>; }

export function DashboardPage() {
  const { user } = useAppSelector(selectAuth);
  const { data, isLoading, error } = useDashboardQuery();
  const { data: feed } = useActivityFeedQuery({ limit: 8 });
  if (isLoading) return <DashboardSkeleton />;
  if (error || !data) return <ErrorState message="The role dashboard could not be composed." />;
  const payload = data.data;
  const entries = Object.entries(payload).filter(([key, value]) => key in labels && typeof value === "number");
  const scope = String(payload.scope || "student");
  const progress = payload.degree_progress as DegreeProgress | undefined;
  const recommendations = (payload.recommendations || []) as AcademicRecommendation[];
  const trends = asObject(payload.trends);
  const questionTrend = (trends.questions || []) as Array<{ date: string; value: number }>;
  const gradeTrend = (payload.grade_trend || []) as Array<{ course: string; score: number }>;
  const today = (payload.today || []) as Array<{ id: number; code: string; title: string; start_time: string; end_time: string; location: string }>;
  const attention = (payload.attention || []) as Array<{ label: string; value: number; severity: string; url: string }>;

  return <div className="page-stack dashboard-page">
    <section className="dashboard-hero"><div><p className="eyebrow">{scope === "management" ? "Executive command center" : scope === "professor" ? "Teaching intelligence" : "Academic navigator"}</p><h1>Good to see you, {user?.first_name || user?.username}</h1><p>{String(payload.headline || "A clear snapshot of what needs your attention today.")}</p><div className="hero-actions"><Link className="button button-primary" to={scope === "management" ? "/analytics" : scope === "professor" ? "/academics/classes" : "/calendar"}>{scope === "management" ? "Open intelligence center" : scope === "professor" ? "Manage teaching" : "Plan my week"}</Link><Link className="button button-secondary" to="/questions"><Bot />Ask UniFlow AI</Link></div></div><div className="hero-orbit"><span className="orbit orbit-one" /><span className="orbit orbit-two" /><div className="hero-logo"><TrendingUp /></div></div></section>

    <section className="metric-grid">{entries.slice(0, 6).map(([key, value], index) => { const Icon = iconMap[key as keyof typeof iconMap] || Activity; return <KpiCard key={key} label={labels[key]} value={String(value)} icon={<Icon />} tone={["primary", "violet", "emerald", "amber"][index % 4]} />; })}</section>

    {scope === "student" && progress ? <section className="dashboard-grid dashboard-grid-wide"><Card className="degree-card"><div className="panel-heading"><div><p className="eyebrow">Degree progress</p><h2>{progress.completed_credits} of {progress.total_credits} credits complete</h2></div><ProgressRing value={progress.percentage} label="complete" /></div><div className="category-progress">{Object.entries(progress.categories).map(([category, item]) => <div key={category}><span><strong>{category}</strong><em>{item.completed_credits}/{item.credits} credits</em></span><div><i style={{ width: `${item.credits ? item.completed_credits / item.credits * 100 : 0}%` }} /></div></div>)}</div><Link className="text-link" to="/academics/classes">Review degree requirements →</Link></Card><Card className="recommendation-card"><div className="panel-heading"><div><p className="eyebrow">Smart guidance</p><h2>Recommended next actions</h2></div><Lightbulb /></div><div className="recommendation-list">{recommendations.length ? recommendations.map((item) => <Link to={item.action_url} key={item.code}><span className={`recommendation-priority priority-${item.priority}`} /><div><strong>{item.title}</strong><p>{item.description}</p></div></Link>) : <p className="muted-copy">You are on track. New recommendations will appear as your records change.</p>}</div></Card></section> : null}

    {scope === "student" && gradeTrend.length ? <Card className="trend-card"><div className="panel-heading"><div><p className="eyebrow">Performance</p><h2>Grade momentum</h2></div><Sparkline values={gradeTrend.map((item) => item.score)} /></div><MiniBarChart label="Grade trend" data={gradeTrend.map((item) => ({ label: item.course, value: item.score }))} /></Card> : null}

    {scope === "management" ? <section className="dashboard-grid"><Card className="trend-card"><div className="panel-heading"><div><p className="eyebrow">14-day pulse</p><h2>AI question activity</h2></div><Sparkline values={questionTrend.map((item) => item.value)} /></div><MiniBarChart data={questionTrend.map((item) => ({ label: item.date.slice(5), value: item.value }))} /></Card><Card><div className="panel-heading"><div><p className="eyebrow">Needs attention</p><h2>Operational queue</h2></div><Timer /></div><div className="attention-list">{attention.map((item) => <Link to={item.url} key={item.label}><StatusBadge status={item.severity} /><strong>{item.value}</strong><span>{item.label}</span></Link>)}</div></Card></section> : null}

    {today.length ? <Card><div className="panel-heading"><div><p className="eyebrow">Today</p><h2>{scope === "professor" ? "Teaching schedule" : "Your campus rhythm"}</h2></div><BookOpen /></div><div className="today-strip">{today.map((item) => <div key={item.id}><span>{item.start_time.slice(0,5)}</span><div><strong>{item.code} · {item.title}</strong><small>{item.location} · until {item.end_time.slice(0,5)}</small></div></div>)}</div></Card> : null}

    <ActivityFeed items={feed?.data.items || []} />
  </div>;
}
