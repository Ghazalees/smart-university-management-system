/** Renders the AnalyticsPage workspace and coordinates its API-driven interactions. */

import { Bot, BookMarked, CheckCircle2, Gauge, ShieldAlert, TrendingUp } from "lucide-react";
import { useAiAnalyticsQuery } from "../services/api";
import { Card, DashboardSkeleton, ErrorState, KpiCard, MiniBarChart, PageHeader, ProgressRing, Sparkline } from "../components/ui";

export function AnalyticsPage() {
  const { data, isLoading, error } = useAiAnalyticsQuery();
  if (isLoading) return <DashboardSkeleton />;
  if (error || !data) return <ErrorState message="AI analytics requires management access." />;
  const value = data.data;
  return <div className="page-stack"><PageHeader title="AI trust and quality center" description="Measure groundedness, escalation, confidence, source coverage and operational demand." />
    <section className="metric-grid"><KpiCard label="Questions" value={value.total_questions} icon={<Bot />} /><KpiCard label="Answered" value={value.answered} icon={<CheckCircle2 />} tone="emerald" /><KpiCard label="Escalated" value={value.escalated} icon={<ShieldAlert />} tone="amber" /><KpiCard label="Average confidence" value={`${Math.round((value.average_confidence || 0) * 100)}%`} icon={<Gauge />} tone="violet" /></section>
    <section className="dashboard-grid dashboard-grid-wide"><Card className="quality-scorecard"><div><p className="eyebrow">Grounded quality</p><h2>Evidence coverage</h2><p>Answers are counted as documented only when authorized source records are attached to the persisted response.</p></div><div className="ring-pair"><ProgressRing value={value.documented_rate} label="documented" /><ProgressRing value={100 - value.escalation_rate} label="resolved" /></div></Card><Card className="trend-card"><div className="panel-heading"><div><p className="eyebrow">Demand trend</p><h2>Questions over 14 days</h2></div><Sparkline values={value.trend.map((item) => item.value)} /></div><MiniBarChart data={value.trend.map((item) => ({ label: item.date.slice(5), value: item.value }))} /></Card></section>
    <section className="dashboard-grid"><Card><div className="panel-heading"><div><p className="eyebrow">Confidence bands</p><h2>Response certainty</h2></div><TrendingUp /></div><div className="distribution-bars">{Object.entries(value.confidence_bands).map(([label, count]) => <div key={label}><span><strong>{label}</strong><em>{count}</em></span><div><i style={{ width: `${value.total_questions ? count / value.total_questions * 100 : 0}%` }} /></div></div>)}</div></Card><Card><div className="panel-heading"><div><p className="eyebrow">Knowledge impact</p><h2>Most cited sources</h2></div><BookMarked /></div><div className="rank-list">{value.top_sources.length ? value.top_sources.map((source, index) => <div key={source.document_id}><span>{index + 1}</span><strong>{source.title}</strong><em>{source.uses} uses</em></div>) : <p className="muted-copy">Sources will rank after grounded answers are generated.</p>}</div></Card></section>
  </div>;
}
