/** Renders the WorkflowsPage workspace and coordinates its API-driven interactions. */

import { useMemo, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileInput,
  Plus,
  RotateCcw,
  Search,
  UserRoundCog,
  XCircle,
} from "lucide-react";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import {
  useAssignWorkflowMutation,
  useCreateWorkflowMutation,
  useTransitionWorkflowMutation,
  useUsersQuery,
  useWorkflowTypesQuery,
  useWorkflowsQuery,
} from "../services/api";
import type { WorkflowRequest, WorkflowType } from "../types";
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
  Textarea,
} from "../components/ui";
import { formatDate, getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

const tones: Record<string, string> = {
  draft: "neutral",
  pending: "warning",
  under_review: "info",
  needs_revision: "warning",
  approved: "success",
  rejected: "danger",
};

interface RequestDraft {
  request_type: string;
  title: string;
  description: string;
  payload: Record<string, string>;
}

const emptyDraft: RequestDraft = { request_type: "", title: "", description: "", payload: {} };

interface SmartFieldDefinition {
  name: string;
  label: string;
  type: "text" | "date" | "number" | "select" | "textarea" | "checkbox" | "email";
  required: boolean;
  help?: string;
  placeholder?: string;
  options?: Array<{ value: string; label: string }>;
  visible_when?: { field: string; equals?: string | boolean; operator?: "equals" | "not_equals" | "not_empty" | "empty" };
  min?: number;
  max?: number;
}

function schemaDefinitions(type?: WorkflowType): SmartFieldDefinition[] {
  if (!type || !type.schema || typeof type.schema !== "object") return [];
  const schema = type.schema as Record<string, unknown>;
  const required = new Set(Array.isArray(schema.required) ? schema.required.filter((value): value is string => typeof value === "string") : []);
  const root = schema.properties && typeof schema.properties === "object" ? schema.properties as Record<string, unknown> : schema;
  return Object.entries(root).filter(([name]) => name !== "required" && name !== "properties").map(([name, raw]) => {
    const definition = raw && typeof raw === "object" ? raw as Record<string, unknown> : {};
    const rawOptions = Array.isArray(definition.options) ? definition.options : Array.isArray(definition.enum) ? definition.enum : [];
    const options = rawOptions.map((item) => typeof item === "object" && item !== null
      ? { value: String((item as Record<string, unknown>).value ?? ""), label: String((item as Record<string, unknown>).label ?? (item as Record<string, unknown>).value ?? "") }
      : { value: String(item), label: humanize(String(item)) });
    const inferred = name.includes("date") ? "date" : name.includes("email") ? "email" : options.length ? "select" : "text";
    return {
      name,
      label: String(definition.label || humanize(name)),
      type: String(definition.type || inferred) as SmartFieldDefinition["type"],
      required: required.has(name) || Boolean(definition.required),
      help: definition.help ? String(definition.help) : undefined,
      placeholder: definition.placeholder ? String(definition.placeholder) : undefined,
      options,
      visible_when: definition.visible_when && typeof definition.visible_when === "object" ? definition.visible_when as SmartFieldDefinition["visible_when"] : undefined,
      min: typeof definition.min === "number" ? definition.min : undefined,
      max: typeof definition.max === "number" ? definition.max : undefined,
    };
  });
}

function humanize(value: string) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function WorkflowsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [createStep, setCreateStep] = useState(1);
  const [draft, setDraft] = useState<RequestDraft>(emptyDraft);
  const [detail, setDetail] = useState<WorkflowRequest | null>(null);
  const [decision, setDecision] = useState<{ request: WorkflowRequest; action: string } | null>(null);
  const [assignTarget, setAssignTarget] = useState<WorkflowRequest | null>(null);
  const { user } = useAppSelector(selectAuth);
  const canReview = Boolean(user?.permissions.includes("workflows.review") || user?.permissions.includes("*"));
  const { data, isLoading, error } = useWorkflowsQuery({ page, search, status });
  const { data: typeData } = useWorkflowTypesQuery();
  const selectedType = useMemo(
    () => typeData?.data.find((type) => type.id === Number(draft.request_type)),
    [draft.request_type, typeData],
  );
  const schemaFields = useMemo(() => schemaDefinitions(selectedType), [selectedType]);
  const visibleSchemaFields = useMemo(() => schemaFields.filter((field) => {
    if (!field.visible_when) return true;
    const current = draft.payload[field.visible_when.field] ?? "";
    const operator = field.visible_when.operator || "equals";
    if (operator === "not_empty") return String(current).trim().length > 0;
    if (operator === "empty") return String(current).trim().length === 0;
    if (operator === "not_equals") return String(current) !== String(field.visible_when.equals ?? "");
    return String(current) === String(field.visible_when.equals ?? "");
  }), [draft.payload, schemaFields]);
  const { data: reviewers } = useUsersQuery(
    { role: "AdministrativeStaff", is_active: "true" },
    { skip: !canReview },
  );
  const [createWorkflow, createState] = useCreateWorkflowMutation();
  const [transition, transitionState] = useTransitionWorkflowMutation();
  const [assignWorkflow, assignState] = useAssignWorkflowMutation();
  const { show } = useToast();

  function startCreate() {
    setDraft(emptyDraft);
    setCreateStep(1);
    setCreateOpen(true);
  }

  function nextStep() {
    if (!draft.request_type || !draft.title.trim() || !draft.description.trim()) {
      show("Complete the request type, title and description before continuing.", "error");
      return;
    }
    setCreateStep(2);
  }

  async function create() {
    const missing = visibleSchemaFields.filter((field) => field.required && !String(draft.payload[field.name] ?? "").trim());
    if (missing.length) {
      show(`Complete the required fields: ${missing.map((field) => field.label).join(", ")}`, "error");
      return;
    }
    try {
      const response = await createWorkflow({
        request_type: Number(draft.request_type),
        title: draft.title.trim(),
        description: draft.description.trim(),
        payload: draft.payload,
      }).unwrap();
      await transition({
        id: response.data.id,
        action: "submit",
        expected_version: response.data.version,
      }).unwrap();
      show("Request submitted for review");
      setCreateOpen(false);
      setDraft(emptyDraft);
      setCreateStep(1);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function perform(request: WorkflowRequest, action: string, note = "") {
    try {
      await transition({ id: request.id, action, note, expected_version: request.version }).unwrap();
      show("Request status updated");
      setDecision(null);
      setDetail(null);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function assign(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!assignTarget) return;
    const form = new FormData(event.currentTarget);
    try {
      await assignWorkflow({
        id: assignTarget.id,
        assigned_to: Number(form.get("assigned_to")),
        expected_version: assignTarget.version,
      }).unwrap();
      show("Request ownership assigned");
      setAssignTarget(null);
      setDetail(null);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="Requests and approvals"
        description="Adaptive smart forms, transparent approval timelines, clear ownership and optimistic concurrency protection."
        action={<Button onClick={startCreate}><Plus />New request</Button>}
      />
      <Card className="toolbar">
        <div className="search-box"><Search /><input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1); }} placeholder="Search number, title or requester" /></div>
        <select className="toolbar-select" value={status} onChange={(event) => { setStatus(event.target.value); setPage(1); }}>
          <option value="">All statuses</option><option value="pending">Pending</option><option value="under_review">Under review</option><option value="needs_revision">Needs revision</option><option value="approved">Approved</option><option value="rejected">Rejected</option>
        </select>
      </Card>
      {isLoading ? <LoadingState label="Loading requests" /> : error ? <ErrorState /> : !data?.data.length ? <EmptyState title="No requests found" /> : (
        <Card className="table-card">
          <div className="table-scroll"><table><thead><tr><th>Request</th><th>Requester</th><th>Owner</th><th>Status</th><th>Updated</th><th /></tr></thead><tbody>
            {data.data.map((request) => <tr key={request.id}>
              <td><strong>{request.title}</strong><span className="table-subtitle">{request.request_number} · {request.request_type_detail.name}</span></td>
              <td>{request.requester_detail.full_name}</td>
              <td>{request.assigned_to_detail?.full_name || "Unassigned"}</td>
              <td><Badge tone={tones[request.status] || "neutral"}>{request.status.replaceAll("_", " ")}</Badge></td>
              <td>{formatDate(request.updated_at)}</td>
              <td><Button variant="ghost" onClick={() => setDetail(request)}>View <ArrowRight /></Button></td>
            </tr>)}
          </tbody></table></div>
          <Pagination page={page} pages={data.pagination?.pages ?? 1} onChange={setPage} />
        </Card>
      )}

      {createOpen ? <Modal title="Start a university request" onClose={() => setCreateOpen(false)}>
        <div className="form-grid">
          <div className="stepper"><span className={createStep === 1 ? "active" : ""}>1</span><i /><span className={createStep === 2 ? "active" : ""}>2</span></div>
          {createStep === 1 ? <>
            <Select label="Request type" required value={draft.request_type} onChange={(event) => setDraft({ ...draft, request_type: event.target.value, payload: {} })}><option value="">Choose a request type</option>{typeData?.data.map((type) => <option key={type.id} value={type.id}>{type.name}</option>)}</Select>
            <Input label="Request title" required value={draft.title} onChange={(event) => setDraft({ ...draft, title: event.target.value })} />
            <div className="form-span-2"><Textarea label="Description and supporting details" rows={7} required value={draft.description} onChange={(event) => setDraft({ ...draft, description: event.target.value })} /></div>
            <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setCreateOpen(false)}>Cancel</Button><Button type="button" onClick={nextStep}>Continue <ArrowRight /></Button></div>
          </> : <>
            <div className="form-span-2 smart-form-banner"><FileInput /><div><strong>Adaptive request form</strong><span>Fields, validation and conditional questions are generated from the selected workflow schema.</span></div></div>
            {visibleSchemaFields.map((field) => {
              const value = draft.payload[field.name] || "";
              const update = (next: string) => setDraft({ ...draft, payload: { ...draft.payload, [field.name]: next } });
              if (field.type === "textarea") return <div className="form-span-2" key={field.name}><Textarea label={field.label} hint={field.help} placeholder={field.placeholder} required={field.required} value={value} onChange={(event) => update(event.target.value)} rows={5} /></div>;
              if (field.type === "select") return <Select key={field.name} label={field.label} required={field.required} value={value} onChange={(event) => update(event.target.value)}><option value="">Choose an option</option>{field.options?.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Select>;
              if (field.type === "checkbox") return <label className="toggle-setting" key={field.name}><input type="checkbox" checked={value === "true"} onChange={(event) => update(String(event.target.checked))} /><span><strong>{field.label}</strong><small>{field.help || "Enable this option when it applies to your request."}</small></span></label>;
              return <Input key={field.name} label={field.label} hint={field.help} placeholder={field.placeholder} required={field.required} value={value} onChange={(event) => update(event.target.value)} type={field.type === "number" ? "number" : field.type === "date" ? "date" : field.type === "email" ? "email" : "text"} min={field.min} max={field.max} />;
            })}
            {!visibleSchemaFields.length ? <div className="review-panel"><h3>No additional fields required</h3><p>This request type can be submitted using the information from the first step.</p></div> : null}
            <div className="review-panel"><h3>Review request</h3><p><strong>{selectedType?.name}</strong> · {draft.title}</p><p>{draft.description}</p></div>
            <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setCreateStep(1)}><ArrowLeft />Back</Button><Button type="button" onClick={() => void create()} disabled={createState.isLoading || transitionState.isLoading}>{createState.isLoading || transitionState.isLoading ? "Submitting…" : "Submit request"}</Button></div>
          </>}
        </div>
      </Modal> : null}

      {detail && !decision && !assignTarget ? <Modal title={detail.request_number} onClose={() => setDetail(null)}><div className="workflow-detail">
        <div className="detail-summary"><div><Badge tone={tones[detail.status] || "neutral"}>{detail.status.replaceAll("_", " ")}</Badge><h2>{detail.title}</h2><p>{detail.description}</p></div><dl><div><dt>Type</dt><dd>{detail.request_type_detail.name}</dd></div><div><dt>Requester</dt><dd>{detail.requester_detail.full_name}</dd></div><div><dt>Assigned reviewer</dt><dd>{detail.assigned_to_detail?.full_name || "Not assigned"}</dd></div><div><dt>Updated</dt><dd>{formatDate(detail.updated_at)}</dd></div></dl></div>
        {Object.keys(detail.payload).length ? <Card><h3>Submitted details</h3><dl className="detail-list">{Object.entries(detail.payload).map(([key, value]) => <div key={key}><dt>{humanize(key)}</dt><dd>{String(value)}</dd></div>)}</dl></Card> : null}
        <div className="timeline"><h3>Status timeline</h3>{detail.history.map((event) => <div className="timeline-item" key={event.id}><span className="timeline-dot" /><div><strong>{event.event.replaceAll("_", " ")}</strong><p>{event.note || `${event.from_status || "start"} → ${event.to_status || detail.status}`}</p><small>{event.actor_name} · {formatDate(event.created_at)}</small></div></div>)}</div>
        <div className="modal-actions">
          {detail.status === "needs_revision" && detail.requester_detail.id === user?.id ? <Button onClick={() => perform(detail, "submit")}><RotateCcw />Resubmit</Button> : null}
          {canReview && ["pending", "under_review"].includes(detail.status) ? <Button variant="secondary" onClick={() => setAssignTarget(detail)}><UserRoundCog />Assign</Button> : null}
          {canReview && detail.status === "pending" ? <Button onClick={() => perform(detail, "start_review")}><Clock3 />Start review</Button> : null}
          {canReview && detail.status === "under_review" ? <><Button variant="secondary" onClick={() => setDecision({ request: detail, action: "request_revision" })}><FileInput />Request revision</Button><Button variant="danger" onClick={() => setDecision({ request: detail, action: "reject" })}><XCircle />Reject</Button><Button onClick={() => perform(detail, "approve")}><CheckCircle2 />Approve</Button></> : null}
        </div>
      </div></Modal> : null}

      {decision ? <Modal title={decision.action === "reject" ? "Reject request" : "Request revision"} onClose={() => setDecision(null)}><form className="form-stack" onSubmit={(event) => { event.preventDefault(); const form = new FormData(event.currentTarget); void perform(decision.request, decision.action, String(form.get("note"))); }}><Textarea name="note" label="Reason" rows={5} required /><div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setDecision(null)}>Cancel</Button><Button variant={decision.action === "reject" ? "danger" : "primary"} disabled={transitionState.isLoading}>Confirm</Button></div></form></Modal> : null}

      {assignTarget ? <Modal title="Assign request reviewer" onClose={() => setAssignTarget(null)}><form className="form-stack" onSubmit={assign}><Select name="assigned_to" label="Administrative reviewer" defaultValue={assignTarget.assigned_to ?? ""} required><option value="">Choose a reviewer</option>{reviewers?.data.map((reviewer) => <option key={reviewer.id} value={reviewer.id}>{reviewer.full_name} · {reviewer.email}</option>)}</Select><p className="muted-copy">Assignment uses optimistic concurrency; a stale request cannot overwrite another reviewer’s update.</p><div className="modal-actions"><Button type="button" variant="secondary" onClick={() => setAssignTarget(null)}>Cancel</Button><Button disabled={assignState.isLoading}>{assignState.isLoading ? "Assigning…" : "Assign reviewer"}</Button></div></form></Modal> : null}
    </div>
  );
}
