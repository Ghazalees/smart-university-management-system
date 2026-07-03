/** Renders the ExamsPage workspace and coordinates its API-driven interactions. */

import { useState } from "react";
import { CalendarClock, MapPin, Plus, Timer } from "lucide-react";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import { useClassesQuery, useCreateExamMutation, useExamsQuery } from "../services/api";
import { Badge, Button, Card, EmptyState, ErrorState, Input, LoadingState, Modal, PageHeader, Select, Textarea } from "../components/ui";
import { formatDate, getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

export function ExamsPage() {
  const [open, setOpen] = useState(false);
  const { user } = useAppSelector(selectAuth);
  const canCreate = user?.roles.includes("Professor") || user?.permissions.includes("academics.manage") || user?.permissions.includes("*");
  const { data, isLoading, error } = useExamsQuery({ page: 1 });
  const { data: classes } = useClassesQuery({ page: 1 });
  const [createExam, state] = useCreateExamMutation();
  const { show } = useToast();
  async function create(event: React.FormEvent<HTMLFormElement>) { event.preventDefault(); const form = new FormData(event.currentTarget); try { await createExam({ academic_class: Number(form.get("academic_class")), title: form.get("title"), scheduled_at: form.get("scheduled_at"), duration_minutes: Number(form.get("duration_minutes")), location: form.get("location"), instructions: form.get("instructions") }).unwrap(); show("Exam scheduled and students notified"); setOpen(false); } catch (reason) { show(getErrorMessage(reason), "error"); } }
  return <div className="page-stack"><PageHeader title="Examinations" description="Plan assessments without date ambiguity and keep enrolled students informed." action={canCreate ? <Button onClick={() => setOpen(true)}><Plus />Schedule exam</Button> : undefined} />{isLoading ? <LoadingState label="Loading exams" /> : error ? <ErrorState /> : !data?.data.length ? <EmptyState title="No upcoming exams" /> : <div className="exam-list">{data.data.map((exam) => <Card key={exam.id} className="exam-card"><span className="exam-date"><strong>{new Date(exam.scheduled_at).getDate()}</strong><small>{new Date(exam.scheduled_at).toLocaleString(undefined, { month: "short" })}</small></span><div><div className="badge-row"><Badge tone="info">{exam.course_title}</Badge></div><h2>{exam.title}</h2><p>{formatDate(exam.scheduled_at)}</p><footer><span><Timer />{exam.duration_minutes} minutes</span><span><MapPin />{exam.location}</span></footer></div></Card>)}</div>}{open ? <Modal title="Schedule an exam" onClose={() => setOpen(false)}><form className="form-grid" onSubmit={create}><Select name="academic_class" label="Class" required><option value="">Select class</option>{classes?.data.map((item) => <option key={item.id} value={item.id}>{item.course_detail.code} — {item.course_detail.title}</option>)}</Select><Input name="title" label="Exam title" required /><Input name="scheduled_at" label="Date and time" type="datetime-local" required /><Input name="duration_minutes" label="Duration (minutes)" type="number" min={15} defaultValue={90} required /><Input name="location" label="Location" required /><div className="form-span-2"><Textarea name="instructions" label="Instructions" rows={4} /></div><div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button><Button disabled={state.isLoading}><CalendarClock />Schedule exam</Button></div></form></Modal> : null}</div>;
}
