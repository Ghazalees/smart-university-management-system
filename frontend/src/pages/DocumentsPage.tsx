/** Renders the DocumentsPage workspace and coordinates its API-driven interactions. */

import { useMemo, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  Archive,
  BookMarked,
  Download,
  Eye,
  FileClock,
  FilePlus2,
  FileUp,
  History,
  Pencil,
  RefreshCw,
  RotateCcw,
  Search,
  Send,
  ShieldCheck,
  Upload,
} from "lucide-react";
import {
  useArchiveDocumentMutation,
  useCreateDocumentMutation,
  useDocumentQuery,
  useDocumentsQuery,
  useDocumentVersionsQuery,
  useImportDocumentsMutation,
  usePublishDocumentMutation,
  useReindexDocumentMutation,
  useRestoreDocumentMutation,
  useRestoreDocumentVersionMutation,
  useRolesQuery,
  useUpdateDocumentMutation,
  useUploadDocumentMutation,
} from "../services/api";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import type { DocumentRecord } from "../types";
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
  StatusBadge,
  Textarea,
} from "../components/ui";
import { formatDate, getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

const emptyDocument = {
  title: "",
  document_type: "policy",
  content: "",
  access_level: "authenticated",
  status: "draft",
  knowledge_enabled: true,
  effective_from: "",
  expires_at: "",
  review_due_at: "",
  tags: "",
  change_summary: "",
};

export function DocumentsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [governance, setGovernance] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [editing, setEditing] = useState<DocumentRecord | null>(null);
  const [viewing, setViewing] = useState<DocumentRecord | null>(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([]);

  const { id } = useParams();
  const navigate = useNavigate();
  const documentId = id ? Number(id) : 0;
  const { user, accessToken } = useAppSelector(selectAuth);
  const canManage = Boolean(
    user?.permissions.includes("documents.manage") || user?.permissions.includes("*"),
  );

  const { data, isLoading, error } = useDocumentsQuery({
    page,
    search,
    status,
    governance,
    include_archived: canManage ? "true" : "false",
    ordering: "-updated_at",
  });
  const { data: linked } = useDocumentQuery(documentId, { skip: !documentId });
  const detailSuppressed = Boolean(editing || createOpen || importOpen || uploadOpen);
  const activeDocument = detailSuppressed
    ? null
    : documentId ? linked?.data || viewing : null;
  const { data: versions } = useDocumentVersionsQuery(activeDocument?.id || 0, {
    skip: !activeDocument,
  });
  const { data: roles } = useRolesQuery(undefined, { skip: !canManage });

  const [createDocument, createState] = useCreateDocumentMutation();
  const [updateDocument, updateState] = useUpdateDocumentMutation();
  const [archiveDocument] = useArchiveDocumentMutation();
  const [publishDocument] = usePublishDocumentMutation();
  const [restoreDocument] = useRestoreDocumentMutation();
  const [reindexDocument] = useReindexDocumentMutation();
  const [restoreVersion, restoreVersionState] = useRestoreDocumentVersionMutation();
  const [importDocuments, importState] = useImportDocumentsMutation();
  const [uploadDocument, uploadState] = useUploadDocumentMutation();
  const { show } = useToast();

  const governanceCounts = useMemo(
    () => ({
      expired: data?.data.filter((item) => item.governance_status === "expired").length || 0,
      due: data?.data.filter((item) => item.governance_status.includes("review")).length || 0,
    }),
    [data],
  );

  function resetRoles() {
    setSelectedRoleIds([]);
  }

  function closeView() {
    setViewing(null);
    if (documentId) navigate("/documents", { replace: true });
  }

  function closeEditor() {
    setEditing(null);
    resetRoles();
  }

  function edit(document: DocumentRecord) {
    setViewing(null);
    if (documentId) navigate("/documents", { replace: true });
    setSelectedRoleIds(
      roles?.data
        .filter((role) => document.allowed_roles.includes(role.name))
        .map((role) => role.id) || [],
    );
    setEditing(document);
  }

  async function save(event: React.FormEvent<HTMLFormElement>, existing?: DocumentRecord) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const body = {
      title: String(formData.get("title")),
      document_type: String(formData.get("document_type")),
      content: String(formData.get("content")),
      access_level: String(formData.get("access_level")),
      status: String(formData.get("status")),
      knowledge_enabled: formData.get("knowledge_enabled") === "on",
      allowed_role_ids: selectedRoleIds,
      effective_from: formData.get("effective_from") || null,
      expires_at: formData.get("expires_at") || null,
      review_due_at: formData.get("review_due_at") || null,
      tags: String(formData.get("tags") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      change_summary: String(formData.get("change_summary") || ""),
    };
    try {
      if (existing) await updateDocument({ id: existing.id, body }).unwrap();
      else await createDocument(body).unwrap();
      show(existing ? "Revision created successfully" : "Document created with an initial version");
      closeEditor();
      setCreateOpen(false);
      resetRoles();
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function uploadFile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const file = formData.get("file");
    if (!(file instanceof File) || !file.size) {
      show("Choose a supported file before uploading.", "error");
      return;
    }

    const metadata = {
      title: String(formData.get("title") || "").trim(),
      document_type: String(formData.get("document_type") || "other"),
      access_level: String(formData.get("access_level") || "authenticated"),
      status: String(formData.get("status") || "published"),
      knowledge_enabled: formData.get("knowledge_enabled") === "on",
      allowed_role_ids: selectedRoleIds,
      effective_from: formData.get("effective_from") || null,
      expires_at: formData.get("expires_at") || null,
      review_due_at: formData.get("review_due_at") || null,
      tags: String(formData.get("tags") || "")
        .split(",")
        .map((item) => item.trim())
        .filter(Boolean),
      change_summary: String(formData.get("change_summary") || `Uploaded from ${file.name}`),
    };
    const payload = new FormData();
    payload.append("file", file);
    payload.append("metadata", JSON.stringify(metadata));

    try {
      const response = await uploadDocument(payload).unwrap();
      show(`${response.data.title} was uploaded, indexed and added to knowledge`);
      setUploadOpen(false);
      resetRoles();
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function perform(
    action: "archive" | "publish" | "restore" | "reindex",
    document: DocumentRecord,
  ) {
    try {
      if (action === "archive") await archiveDocument(document.id).unwrap();
      if (action === "publish") await publishDocument(document.id).unwrap();
      if (action === "restore") await restoreDocument(document.id).unwrap();
      if (action === "reindex") await reindexDocument(document.id).unwrap();
      show(`Document ${action} completed`);
      closeView();
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function restoreHistoricalVersion(document: DocumentRecord, version: number) {
    try {
      await restoreVersion({ id: document.id, version }).unwrap();
      show(`Version ${version} restored as a new revision`);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function importData(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    try {
      const response = await importDocuments({
        format: String(formData.get("format")),
        content: String(formData.get("content")),
      }).unwrap();
      show(
        `${response.data.created} documents imported${
          response.data.errors.length ? `, ${response.data.errors.length} rows need attention` : ""
        }`,
      );
      setImportOpen(false);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function download(format: "json" | "csv") {
    const response = await fetch(`/api/v1/documents/export?format=${format}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    if (!response.ok) {
      show("Export failed", "error");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `documents.${format}`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  const roleChoices = (
    <div className="form-span-2">
      <span className="field-label">Allowed roles for role-restricted access</span>
      <div className="choice-grid">
        {roles?.data.map((role) => (
          <label className="choice-card" key={role.id}>
            <input
              type="checkbox"
              checked={selectedRoleIds.includes(role.id)}
              onChange={(event) =>
                setSelectedRoleIds((current) =>
                  event.target.checked
                    ? Array.from(new Set([...current, role.id]))
                    : current.filter((roleId) => roleId !== role.id),
                )
              }
            />
            {role.name}
          </label>
        ))}
      </div>
    </div>
  );

  const documentForm = (existing?: DocumentRecord) => (
    <form className="form-grid" onSubmit={(event) => void save(event, existing)}>
      <div className="form-span-2">
        <Input
          name="title"
          label="Title"
          required
          defaultValue={existing?.title || emptyDocument.title}
        />
      </div>
      <Select name="document_type" label="Type" defaultValue={existing?.document_type || "policy"}>
        <option value="policy">Policy</option>
        <option value="regulation">Regulation</option>
        <option value="faq">FAQ</option>
        <option value="guide">Guide</option>
        <option value="academic">Academic</option>
        <option value="administrative">Administrative</option>
        <option value="other">Other</option>
      </Select>
      <Select name="status" label="Lifecycle status" defaultValue={existing?.status || "draft"}>
        <option value="draft">Draft</option>
        <option value="published">Published</option>
        <option value="archived">Archived</option>
      </Select>
      <Select
        name="access_level"
        label="Access level"
        defaultValue={existing?.access_level || "authenticated"}
      >
        <option value="public">Public</option>
        <option value="authenticated">Authenticated users</option>
        <option value="role">Role restricted</option>
        <option value="private">Managers only</option>
      </Select>
      <Input
        name="tags"
        label="Tags"
        defaultValue={existing?.tags.join(", ") || ""}
        placeholder="policy, leave, student"
      />
      <Input
        name="effective_from"
        label="Effective from"
        type="datetime-local"
        defaultValue={existing?.effective_from?.slice(0, 16) || ""}
      />
      <Input
        name="expires_at"
        label="Expires at"
        type="datetime-local"
        defaultValue={existing?.expires_at?.slice(0, 16) || ""}
      />
      <Input
        name="review_due_at"
        label="Review due"
        type="datetime-local"
        defaultValue={existing?.review_due_at?.slice(0, 16) || ""}
      />
      <Input
        name="change_summary"
        label="Change summary"
        required={Boolean(existing)}
        placeholder="What changed in this version?"
      />
      <div className="form-span-2">
        <Textarea
          name="content"
          label="Document content"
          rows={12}
          required
          defaultValue={existing?.content || ""}
        />
      </div>
      <label className="switch-row form-span-2">
        <input
          type="checkbox"
          name="knowledge_enabled"
          defaultChecked={existing?.knowledge_enabled ?? true}
        />
        <span>
          <strong>Include in grounded AI retrieval</strong>
          <small>Only users authorized to read this document can retrieve it.</small>
        </span>
      </label>
      {roleChoices}
      <div className="modal-actions form-span-2">
        <Button
          type="button"
          variant="secondary"
          onClick={() => {
            setCreateOpen(false);
            closeEditor();
          }}
        >
          Cancel
        </Button>
        <Button disabled={createState.isLoading || updateState.isLoading}>
          {existing ? "Save revision" : "Create document"}
        </Button>
      </div>
    </form>
  );

  return (
    <div className="page-stack">
      <PageHeader
        title="Knowledge governance"
        description="Create, upload, version, review, publish and export the authorized knowledge used by people and AI."
        action={canManage ? (
          <div className="page-actions">
            <Button
              variant="secondary"
              onClick={() => {
                resetRoles();
                setUploadOpen(true);
              }}
            >
              <FileUp />Upload file
            </Button>
            <Button variant="secondary" onClick={() => setImportOpen(true)}>
              <Upload />Import data
            </Button>
            <Button variant="secondary" onClick={() => void download("csv")}>
              <Download />Export
            </Button>
            <Button
              onClick={() => {
                resetRoles();
                setCreateOpen(true);
              }}
            >
              <FilePlus2 />New document
            </Button>
          </div>
        ) : undefined}
      />

      {canManage ? (
        <section className="governance-strip">
          <div><FileClock /><span><strong>{governanceCounts.due}</strong>reviews due</span></div>
          <div><Archive /><span><strong>{governanceCounts.expired}</strong>expired documents</span></div>
          <div><ShieldCheck /><span><strong>{data?.pagination?.count || 0}</strong>authorized records</span></div>
        </section>
      ) : null}

      <Card className="toolbar">
        <div className="search-box">
          <Search />
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search title and content"
          />
        </div>
        <div className="filter-row">
          <select
            className="toolbar-select"
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="draft">Draft</option>
            <option value="published">Published</option>
            <option value="archived">Archived</option>
          </select>
          <select
            className="toolbar-select"
            value={governance}
            onChange={(event) => {
              setGovernance(event.target.value);
              setPage(1);
            }}
          >
            <option value="">All governance states</option>
            <option value="expired">Expired</option>
            <option value="review_due">Review due</option>
          </select>
        </div>
      </Card>

      {isLoading ? (
        <LoadingState label="Loading knowledge" />
      ) : error ? (
        <ErrorState />
      ) : !data?.data.length ? (
        <EmptyState
          title="No documents found"
          message="Create or upload a governed source, or change the current filters."
          action={canManage ? <Button onClick={() => setCreateOpen(true)}>Create document</Button> : undefined}
        />
      ) : (
        <div className="document-grid">
          {data.data.map((document) => (
            <Card key={document.id} className={`document-card governance-${document.governance_status}`}>
              <header>
                <span className="document-icon"><BookMarked /></span>
                <div className="badge-row">
                  <StatusBadge status={document.status} />
                  <StatusBadge status={document.governance_status} />
                </div>
              </header>
              <h2>{document.title}</h2>
              <p>{document.content.slice(0, 150)}{document.content.length > 150 ? "…" : ""}</p>
              <div className="tag-row">
                {document.tags.slice(0, 4).map((tag) => <span key={tag}>{tag}</span>)}
              </div>
              <dl>
                <div><dt>Versions</dt><dd>{document.version_count}</dd></div>
                <div><dt>AI index</dt><dd>v{document.index_version}</dd></div>
                <div><dt>Updated</dt><dd>{formatDate(document.updated_at)}</dd></div>
              </dl>
              <footer>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setViewing(document);
                    navigate(`/documents/${document.id}`);
                  }}
                >
                  <Eye />View
                </Button>
                {canManage ? <Button variant="ghost" onClick={() => edit(document)}><Pencil />Edit</Button> : null}
              </footer>
            </Card>
          ))}
        </div>
      )}
      <Pagination page={page} pages={data?.pagination?.pages || 1} onChange={setPage} />

      {createOpen ? (
        <Modal title="Create governed document" onClose={() => { setCreateOpen(false); resetRoles(); }} wide>
          {documentForm()}
        </Modal>
      ) : null}

      {editing ? (
        <Modal title={`Create revision — ${editing.title}`} onClose={closeEditor} wide>
          {documentForm(editing)}
        </Modal>
      ) : null}

      {activeDocument ? (
        <Modal title={activeDocument.title} onClose={closeView} wide>
          <div className="document-detail">
            <div className="detail-summary">
              <div>
                <div className="badge-row">
                  <StatusBadge status={activeDocument.status} />
                  <StatusBadge status={activeDocument.governance_status} />
                  <Badge tone="info">{activeDocument.document_type}</Badge>
                </div>
                <p className="document-content">{activeDocument.content}</p>
              </div>
              <dl>
                <div><dt>Access</dt><dd>{activeDocument.access_level}</dd></div>
                <div><dt>Review owner</dt><dd>{activeDocument.review_owner_name || "Not assigned"}</dd></div>
                <div><dt>Expires</dt><dd>{activeDocument.expires_at ? formatDate(activeDocument.expires_at) : "No expiry"}</dd></div>
                <div><dt>Last indexed</dt><dd>{activeDocument.indexed_at ? formatDate(activeDocument.indexed_at) : "Not indexed"}</dd></div>
              </dl>
            </div>
            <Card>
              <div className="panel-heading">
                <div><p className="eyebrow">Version history</p><h2>Traceable changes</h2></div>
                <History />
              </div>
              <div className="version-list">
                {versions?.data.map((version) => (
                  <div key={version.id}>
                    <span>v{version.version_number}</span>
                    <div>
                      <strong>{version.change_summary || "Document updated"}</strong>
                      <small>{version.created_by_name} · {formatDate(version.created_at)}</small>
                    </div>
                    {canManage && version.version_number !== activeDocument.version_count ? (
                      <Button
                        variant="ghost"
                        disabled={restoreVersionState.isLoading}
                        onClick={() => void restoreHistoricalVersion(activeDocument, version.version_number)}
                      >
                        <RotateCcw />Restore
                      </Button>
                    ) : null}
                  </div>
                ))}
              </div>
            </Card>
            {canManage ? (
              <div className="modal-actions">
                <Button variant="secondary" onClick={() => edit(activeDocument)}>
                  <Pencil />Create revision
                </Button>
                <Button variant="secondary" onClick={() => void perform("reindex", activeDocument)}>
                  <RefreshCw />Reindex
                </Button>
                {activeDocument.status === "archived" ? (
                  <Button onClick={() => void perform("restore", activeDocument)}>
                    <RotateCcw />Restore draft
                  </Button>
                ) : (
                  <>
                    <Button onClick={() => void perform("publish", activeDocument)}>
                      <Send />Publish
                    </Button>
                    <Button variant="danger" onClick={() => void perform("archive", activeDocument)}>
                      <Archive />Archive
                    </Button>
                  </>
                )}
              </div>
            ) : null}
          </div>
        </Modal>
      ) : null}

      {uploadOpen ? (
        <Modal title="Upload a file to knowledge" onClose={() => { setUploadOpen(false); resetRoles(); }} wide>
          <form className="form-grid" onSubmit={uploadFile}>
            <div className="form-span-2 upload-dropzone">
              <FileUp />
              <div>
                <strong>Select the source file</strong>
                <span>TXT, Markdown, CSV, JSON, HTML, DOCX and text-based PDF files up to 5 MB.</span>
              </div>
              <input
                name="file"
                type="file"
                accept=".txt,.md,.csv,.json,.html,.htm,.docx,.pdf,text/plain,text/csv,application/json,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                required
              />
            </div>
            <div className="form-span-2">
              <Input name="title" label="Knowledge title" placeholder="Leave empty to use the file name" />
            </div>
            <Select name="document_type" label="Type" defaultValue="other">
              <option value="policy">Policy</option>
              <option value="regulation">Regulation</option>
              <option value="faq">FAQ</option>
              <option value="guide">Guide</option>
              <option value="academic">Academic</option>
              <option value="research">Research</option>
              <option value="administrative">Administrative</option>
              <option value="other">Other</option>
            </Select>
            <Select name="status" label="Lifecycle status" defaultValue="published">
              <option value="published">Published — available to AI now</option>
              <option value="draft">Draft — not used by AI yet</option>
            </Select>
            <Select name="access_level" label="Access level" defaultValue="authenticated">
              <option value="public">Public</option>
              <option value="authenticated">Authenticated users</option>
              <option value="role">Role restricted</option>
              <option value="private">Managers only</option>
            </Select>
            <Input name="tags" label="Tags" placeholder="handbook, admissions, policy" />
            <Input name="effective_from" label="Effective from" type="datetime-local" />
            <Input name="expires_at" label="Expires at" type="datetime-local" />
            <Input name="review_due_at" label="Review due" type="datetime-local" />
            <Input name="change_summary" label="Version note" placeholder="Initial file upload" />
            <label className="switch-row form-span-2">
              <input type="checkbox" name="knowledge_enabled" defaultChecked />
              <span>
                <strong>Use this file for grounded AI answers</strong>
                <small>The extracted text is indexed and only returned to users allowed by the access settings above.</small>
              </span>
            </label>
            {roleChoices}
            <div className="modal-actions form-span-2">
              <Button type="button" variant="secondary" onClick={() => { setUploadOpen(false); resetRoles(); }}>
                Cancel
              </Button>
              <Button disabled={uploadState.isLoading}>
                <FileUp />{uploadState.isLoading ? "Reading and indexing…" : "Upload and index"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}

      {importOpen ? (
        <Modal title="Import documents" onClose={() => setImportOpen(false)} wide>
          <form className="form-stack" onSubmit={importData}>
            <Select name="format" label="Format">
              <option value="json">JSON array</option>
              <option value="csv">CSV</option>
            </Select>
            <Textarea
              name="content"
              label="Import payload"
              rows={15}
              required
              hint="A maximum of 500 rows is validated. Invalid rows are reported without rolling back valid records."
            />
            <div className="modal-actions">
              <Button type="button" variant="secondary" onClick={() => setImportOpen(false)}>Cancel</Button>
              <Button disabled={importState.isLoading}><Upload />Validate and import</Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
