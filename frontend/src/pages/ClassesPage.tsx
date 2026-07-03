/** Renders the ClassesPage workspace and coordinates its API-driven interactions. */

import { useMemo, useState } from "react";
import { BarChart3, CalendarDays, Check, Clock, Lightbulb, MapPin, Pencil, Plus, Sparkles, Users } from "lucide-react";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import {
  useClassDetailQuery,
  useClassesQuery,
  useCoursesQuery,
  useCreateClassMutation,
  useScheduleSuggestionsMutation,
  useUpdateClassMutation,
  useUsersQuery,
} from "../services/api";
import type { AcademicClass } from "../types";
import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Input,
  LoadingState,
  Modal,
  PageHeader,
  Pagination,
  Select,
} from "../components/ui";
import { formatDate, getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

const weekdays = ["", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
interface SuggestedSlot { weekday: number; start_time: string; end_time: string; score: number; reason: string; }

function formatScore(value: number | null) {
  return value === null ? "—" : value.toFixed(1);
}

export function ClassesPage() {
  const [open, setOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [selectedClass, setSelectedClass] = useState<number | null>(null);
  const [editingClass, setEditingClass] = useState<AcademicClass | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<SuggestedSlot | null>(null);
  const [suggestions, setSuggestions] = useState<SuggestedSlot[]>([]);
  const [draft, setDraft] = useState({ professor: "", term: "Spring 2026", location: "", duration_minutes: "90" });
  const { user } = useAppSelector(selectAuth);
  const canManageAll = Boolean(user?.permissions.includes("academics.manage") || user?.permissions.includes("*"));
  const canCreate = Boolean(user?.permissions.includes("classes.create") || canManageAll);
  const { data, isLoading, error } = useClassesQuery({ page });
  const { data: detail, isLoading: detailLoading } = useClassDetailQuery(selectedClass ?? 0, { skip: selectedClass === null });
  const { data: courses } = useCoursesQuery({ page: 1 });
  const { data: professors } = useUsersQuery(
    { role: "Professor", is_active: "true" },
    { skip: !canManageAll },
  );
  const [createClass, createState] = useCreateClassMutation();
  const [updateClass, updateState] = useUpdateClassMutation();
  const [requestSuggestions, suggestionState] = useScheduleSuggestionsMutation();
  const { show } = useToast();

  const effectiveProfessor = draft.professor || String(user?.id || "");
  const utilization = useMemo(() => {
    const rows = data?.data || [];
    if (!rows.length) return 0;
    const capacity = rows.reduce((sum, item) => sum + item.capacity, 0);
    const enrolled = rows.reduce((sum, item) => sum + item.enrolled_count, 0);
    return capacity ? Math.round((enrolled / capacity) * 100) : 0;
  }, [data]);

  function canEdit(item: AcademicClass) {
    return canManageAll || item.professor === user?.id;
  }

  async function suggest() {
    if (!effectiveProfessor || !draft.term.trim()) {
      show("Select a professor and term before requesting suggestions.", "error");
      return;
    }
    try {
      const response = await requestSuggestions({
        professor: Number(effectiveProfessor),
        term: draft.term.trim(),
        location: draft.location.trim(),
        duration_minutes: Number(draft.duration_minutes),
        weekdays: [1, 2, 3, 4, 5],
      }).unwrap();
      setSuggestions(response.data.suggestions);
      setSelectedSlot(response.data.suggestions[0] || null);
      show(
        response.data.suggestions.length ? "Conflict-free schedule options generated" : "No conflict-free slots were found",
        response.data.suggestions.length ? "success" : "error",
      );
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await createClass({
        course: Number(form.get("course")),
        professor: Number(form.get("professor") || user?.id),
        term: form.get("term"),
        section: form.get("section"),
        weekday: Number(form.get("weekday")),
        start_time: form.get("start_time"),
        end_time: form.get("end_time"),
        location: form.get("location"),
        capacity: Number(form.get("capacity")),
      }).unwrap();
      show("Class created without schedule conflicts");
      setOpen(false);
      setSuggestions([]);
      setSelectedSlot(null);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function update(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editingClass) return;
    const form = new FormData(event.currentTarget);
    try {
      await updateClass({
        id: editingClass.id,
        body: {
          course: Number(form.get("course")),
          professor: Number(form.get("professor") || editingClass.professor),
          term: form.get("term"),
          section: form.get("section"),
          weekday: Number(form.get("weekday")),
          start_time: form.get("start_time"),
          end_time: form.get("end_time"),
          location: form.get("location"),
          capacity: Number(form.get("capacity")),
          is_active: form.get("is_active") === "on",
        },
      }).unwrap();
      show("Class updated successfully");
      setEditingClass(null);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  return <div className="page-stack">
    <PageHeader title="Class schedule" description="Plan conflict-free teaching with capacity signals, smart slot recommendations and class performance insights." action={canCreate ? <Button onClick={() => setOpen(true)}><Plus />Create class</Button> : undefined} />

    <section className="insight-strip">
      <Card className="compact-insight"><CalendarDays /><div><strong>{data?.pagination?.count ?? 0}</strong><span>Visible classes</span></div></Card>
      <Card className="compact-insight"><Users /><div><strong>{utilization}%</strong><span>Seat utilization</span></div></Card>
      <Card className="compact-insight"><Sparkles /><div><strong>Smart</strong><span>Conflict detection enabled</span></div></Card>
    </section>

    {isLoading ? <LoadingState label="Loading schedule" /> : error ? <ErrorState /> : !data?.data.length ? <EmptyState title="No active classes" message="Create the first class and let the scheduler propose a conflict-free slot." /> : <>
      <div className="schedule-grid">{data.data.map((item) => <Card key={item.id} className="class-card interactive-card">
        <header><span className="class-code">{item.course_detail.code}</span><Badge tone="info">{item.term}</Badge></header>
        <h2>{item.course_detail.title}</h2>
        <p>{item.professor_name} · Section {item.section}</p>
        <div className="class-facts"><span><CalendarDays />{weekdays[item.weekday]}</span><span><Clock />{item.start_time.slice(0, 5)}–{item.end_time.slice(0, 5)}</span><span><MapPin />{item.location}</span><span><Users />{item.enrolled_count}/{item.capacity}</span></div>
        <div className="capacity-track"><i style={{ width: `${Math.min(100, Math.round(item.enrolled_count / item.capacity * 100))}%` }} /></div>
        {canEdit(item) ? <div className="class-card-actions">
          <Button variant="secondary" onClick={() => setEditingClass(item)}><Pencil />Edit class</Button>
          <Button variant="secondary" onClick={() => setSelectedClass(item.id)}><BarChart3 />Class report</Button>
        </div> : null}
      </Card>)}</div>
      <Pagination page={page} pages={data.pagination?.pages ?? 1} onChange={setPage} />
    </>}

    {open ? <Modal title="Create a class with smart scheduling" onClose={() => setOpen(false)} wide><form className="form-grid" onSubmit={create}>
      <div className="form-span-2 smart-form-banner"><Sparkles /><div><strong>Conflict-aware planner</strong><span>Professor and room collisions are rejected by the API. Generate ranked free slots before submitting.</span></div></div>
      <Select name="course" label="Course" required><option value="">Select course</option>{courses?.data.map((course) => <option key={course.id} value={course.id}>{course.code} — {course.title}</option>)}</Select>
      {professors ? <Select name="professor" label="Professor" value={draft.professor} onChange={(event) => setDraft({ ...draft, professor: event.target.value })} required><option value="">Select professor</option>{professors.data.map((professor) => <option key={professor.id} value={professor.id}>{professor.full_name}</option>)}</Select> : <input type="hidden" name="professor" value={user?.id || ""} />}
      <Input name="term" label="Term" value={draft.term} onChange={(event) => setDraft({ ...draft, term: event.target.value })} required />
      <Input name="section" label="Section" defaultValue="01" required />
      <Input name="location" label="Room / location" value={draft.location} onChange={(event) => setDraft({ ...draft, location: event.target.value })} required />
      <Select label="Preferred duration" value={draft.duration_minutes} onChange={(event) => setDraft({ ...draft, duration_minutes: event.target.value })}><option value="60">60 minutes</option><option value="90">90 minutes</option><option value="120">120 minutes</option></Select>
      <div className="form-span-2 suggestion-action"><Button type="button" variant="secondary" onClick={() => void suggest()} disabled={suggestionState.isLoading}><Lightbulb />{suggestionState.isLoading ? "Analyzing calendar…" : "Suggest best time slots"}</Button><span>Scores favor central hours and avoid adjacent-class fatigue.</span></div>
      {suggestions.length ? <div className="form-span-2 slot-grid">{suggestions.slice(0, 6).map((slot) => <button key={`${slot.weekday}-${slot.start_time}`} type="button" className={`slot-card ${selectedSlot === slot ? "slot-selected" : ""}`} onClick={() => setSelectedSlot(slot)}><span>{selectedSlot === slot ? <Check /> : <Clock />}</span><div><strong>{weekdays[slot.weekday]} · {slot.start_time}–{slot.end_time}</strong><small>{slot.reason}</small></div><b>{slot.score}</b></button>)}</div> : null}
      <Select name="weekday" label="Weekday" value={selectedSlot?.weekday || ""} onChange={(event) => setSelectedSlot({ weekday: Number(event.target.value), start_time: selectedSlot?.start_time || "09:00", end_time: selectedSlot?.end_time || "10:30", score: 0, reason: "Manual selection" })} required><option value="">Choose weekday</option>{weekdays.slice(1).map((day, index) => <option key={day} value={index + 1}>{day}</option>)}</Select>
      <Input name="capacity" label="Capacity" type="number" min={1} max={500} defaultValue={30} required />
      <Input name="start_time" label="Start time" type="time" value={selectedSlot?.start_time || ""} onChange={(event) => setSelectedSlot({ weekday: selectedSlot?.weekday || 1, start_time: event.target.value, end_time: selectedSlot?.end_time || "", score: 0, reason: "Manual selection" })} required />
      <Input name="end_time" label="End time" type="time" value={selectedSlot?.end_time || ""} onChange={(event) => setSelectedSlot({ weekday: selectedSlot?.weekday || 1, start_time: selectedSlot?.start_time || "", end_time: event.target.value, score: 0, reason: "Manual selection" })} required />
      <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setOpen(false)}>Cancel</Button><Button disabled={createState.isLoading}>{createState.isLoading ? "Creating…" : "Create conflict-free class"}</Button></div>
    </form></Modal> : null}

    {editingClass ? <Modal title={`Edit ${editingClass.course_detail.code} class`} onClose={() => setEditingClass(null)} wide><form className="form-grid" onSubmit={update}>
      <div className="form-span-2 smart-form-banner"><Pencil /><div><strong>Professor class editor</strong><span>Schedule and room conflicts are revalidated by the API before any change is saved.</span></div></div>
      <Select name="course" label="Course" defaultValue={editingClass.course} required>{courses?.data.map((course) => <option key={course.id} value={course.id}>{course.code} — {course.title}</option>)}</Select>
      {canManageAll && professors ? <Select name="professor" label="Professor" defaultValue={editingClass.professor} required>{professors.data.map((professor) => <option key={professor.id} value={professor.id}>{professor.full_name}</option>)}</Select> : <input type="hidden" name="professor" value={editingClass.professor} />}
      <Input name="term" label="Term" defaultValue={editingClass.term} required />
      <Input name="section" label="Section" defaultValue={editingClass.section} required />
      <Select name="weekday" label="Weekday" defaultValue={editingClass.weekday} required>{weekdays.slice(1).map((day, index) => <option key={day} value={index + 1}>{day}</option>)}</Select>
      <Input name="capacity" label="Capacity" type="number" min={Math.max(1, editingClass.enrolled_count)} max={500} defaultValue={editingClass.capacity} required hint={`Cannot be lower than ${editingClass.enrolled_count} enrolled students.`} />
      <Input name="start_time" label="Start time" type="time" defaultValue={editingClass.start_time.slice(0, 5)} required />
      <Input name="end_time" label="End time" type="time" defaultValue={editingClass.end_time.slice(0, 5)} required />
      <div className="form-span-2"><Input name="location" label="Room / location" defaultValue={editingClass.location} required /></div>
      <label className="switch-row form-span-2"><input type="checkbox" name="is_active" defaultChecked={editingClass.is_active} /><span><strong>Class is active</strong><small>Inactive classes remain available for authorized historical reporting.</small></span></label>
      <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setEditingClass(null)}>Cancel</Button><Button disabled={updateState.isLoading}>{updateState.isLoading ? "Saving…" : "Save class changes"}</Button></div>
    </form></Modal> : null}

    {selectedClass !== null ? <Modal title="Class performance report" onClose={() => setSelectedClass(null)} wide>{detailLoading || !detail ? <LoadingState label="Loading class report" /> : <div className="report-modal">
      <div className="report-heading"><div><p className="eyebrow">{detail.data.class.course_detail.code} · {detail.data.class.term}</p><h2>{detail.data.class.course_detail.title}</h2><p>{detail.data.class.professor_name} · Section {detail.data.class.section}</p></div><Badge tone="info">{detail.data.class.enrolled_count} enrolled</Badge></div>
      <div className="report-stat-grid">
        <Card className="report-stat"><span>Students</span><strong>{detail.data.class.enrolled_count}</strong></Card>
        <Card className="report-stat"><span>Grades recorded</span><strong>{detail.data.report.graded_count}</strong></Card>
        <Card className="report-stat report-stat-warning"><span>Without grade</span><strong>{detail.data.report.ungraded_count}</strong></Card>
        <Card className="report-stat"><span>Class average</span><strong>{formatScore(detail.data.report.average)}</strong></Card>
        <Card className="report-stat"><span>Lowest grade</span><strong>{formatScore(detail.data.report.minimum)}</strong></Card>
        <Card className="report-stat"><span>Highest grade</span><strong>{formatScore(detail.data.report.maximum)}</strong></Card>
      </div>
      <div className="report-section-heading"><div><h3>Student results and feedback</h3><p>Every enrolled student is listed, including students who do not yet have a grade.</p></div></div>
      {!detail.data.report.students.length ? <EmptyState title="No enrolled students" message="Enroll students to begin class performance reporting." /> : <div className="report-table-wrap"><table className="report-table"><thead><tr><th>Student</th><th>Grade</th><th>Status</th><th>Feedback</th><th>Updated</th></tr></thead><tbody>{detail.data.report.students.map((student) => <tr key={student.enrollment_id}><td><strong>{student.student_name}</strong></td><td>{student.score === null ? "—" : student.score.toFixed(1)}</td><td>{student.has_grade ? <Badge tone="success">Graded</Badge> : <Badge tone="warning">No grade</Badge>}</td><td><span className="report-feedback">{student.feedback || (student.has_grade ? "No written feedback" : "Awaiting grade")}</span></td><td>{student.graded_at ? formatDate(student.graded_at) : "—"}</td></tr>)}</tbody></table></div>}
      <p className="muted-copy report-note">This report is calculated only from enrollment and grade records authorized for your role.</p>
    </div>}</Modal> : null}
  </div>;
}
