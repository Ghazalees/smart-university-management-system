/** Renders the GradesPage workspace and coordinates its API-driven interactions. */

import { useState } from "react";
import { Award, Plus } from "lucide-react";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import { useClassesQuery, useEnrollmentsQuery, useGradesQuery, useSaveGradeMutation } from "../services/api";
import { Badge, Button, Card, EmptyState, ErrorState, Input, LoadingState, Modal, PageHeader, Select, Textarea } from "../components/ui";
import { getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

export function GradesPage() {
  const [open, setOpen] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState<number | null>(null);
  const [selectedStudentId, setSelectedStudentId] = useState("");
  const { user } = useAppSelector(selectAuth);
  const canGrade = Boolean(user?.roles.includes("Professor") || user?.permissions.includes("academics.manage") || user?.permissions.includes("*"));
  const { data, isLoading, error } = useGradesQuery({ page: 1 });
  const { data: classes } = useClassesQuery({ page: 1 });
  const { data: enrollments, isFetching: enrollmentsLoading } = useEnrollmentsQuery(
    { class_id: selectedClassId ?? 0, page_size: 500 },
    { skip: !canGrade || !open || selectedClassId === null },
  );
  const [saveGrade, state] = useSaveGradeMutation();
  const { show } = useToast();

  function openGradeModal() {
    setSelectedClassId(null);
    setSelectedStudentId("");
    setOpen(true);
  }

  function closeGradeModal() {
    setOpen(false);
    setSelectedClassId(null);
    setSelectedStudentId("");
  }

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await saveGrade({
        academic_class: Number(form.get("academic_class")),
        student: Number(form.get("student")),
        score: Number(form.get("score")),
        feedback: form.get("feedback"),
      }).unwrap();
      show("Grade saved and student notified");
      closeGradeModal();
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  return <div className="page-stack">
    <PageHeader
      title="Grades and feedback"
      description="Students see only their own results; professors manage only the classes they teach."
      action={canGrade ? <Button onClick={openGradeModal}><Plus />Record grade</Button> : undefined}
    />
    {isLoading ? <LoadingState label="Loading grades" /> : error ? <ErrorState /> : !data?.data.length ? <EmptyState title="No grades available" /> : <div className="grade-grid">{data.data.map((grade) => <Card key={grade.id} className="grade-card"><span className="grade-score">{Number(grade.score).toFixed(1)}</span><div><Badge tone="info">{grade.course_title}</Badge><h2>{grade.student_name}</h2><p>{grade.feedback || "No written feedback."}</p></div><Award /></Card>)}</div>}

    {open ? <Modal title="Record a grade" onClose={closeGradeModal}><form className="form-grid" onSubmit={save}>
      <Select
        name="academic_class"
        label="Class"
        required
        value={selectedClassId ?? ""}
        onChange={(event) => {
          setSelectedClassId(event.target.value ? Number(event.target.value) : null);
          setSelectedStudentId("");
        }}
      >
        <option value="">Select class</option>
        {classes?.data.map((item) => <option key={item.id} value={item.id}>{item.course_detail.code} — {item.course_detail.title}</option>)}
      </Select>
      <Select
        name="student"
        label="Student enrolled in this class"
        required
        value={selectedStudentId}
        disabled={selectedClassId === null || enrollmentsLoading}
        onChange={(event) => setSelectedStudentId(event.target.value)}
      >
        <option value="">{selectedClassId === null ? "Select a class first" : enrollmentsLoading ? "Loading enrolled students…" : "Select student"}</option>
        {enrollments?.data.map((enrollment) => <option key={enrollment.id} value={enrollment.student}>{enrollment.student_name}</option>)}
      </Select>
      <Input name="score" label="Score out of 100" type="number" min={0} max={100} step="0.01" required />
      <div className="form-span-2"><Textarea name="feedback" label="Feedback" rows={5} /></div>
      <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={closeGradeModal}>Cancel</Button><Button disabled={state.isLoading || enrollmentsLoading}>{state.isLoading ? "Saving…" : "Save grade"}</Button></div>
    </form></Modal> : null}
  </div>;
}
