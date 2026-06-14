import { useState, useEffect } from "react";
import { X, Calendar, User, ShieldCheck, Tag, Edit3, Save } from "lucide-react";
import {
  Modal,
  Button,
  Chip,
  Spinner,
  TextField,
  Input,
  Label,
} from "@heroui/react";
import { skipToken } from "@reduxjs/toolkit/query";
import {
  useGetDocumentQuery,
  useUpdateDocumentMutation,
  type DocumentItem,
} from "../../states/api/documentsApi";

interface ViewDocumentModalProps {
  document: DocumentItem | null;
  isOpen: boolean;
  onClose: () => void;
  canManage: boolean; // Managed by RBAC check downstream
}

export const ViewDocumentModal = ({
  document,
  isOpen,
  onClose,
  canManage,
}: ViewDocumentModalProps) => {
  const {
    data: response,
    isLoading,
    error,
  } = useGetDocumentQuery(isOpen && document?.id ? document.id : skipToken);
  const [updateDocument, { isLoading: isUpdating }] =
    useUpdateDocumentMutation();

  const detailedDocument = response?.data;

  // Local state layers handling layout mutations
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    title: "",
    document_type: "",
    access_level: "",
    content: "",
  });

  // Seed form parameters when backend data streams in cleanly
  useEffect(() => {
    if (detailedDocument) {
      setEditForm({
        title: detailedDocument.title,
        document_type: detailedDocument.document_type,
        access_level: detailedDocument.access_level,
        content: detailedDocument.content || "",
      });
    }
    setIsEditing(false); // Reset form state if switching targets
  }, [detailedDocument, isOpen]);

  if (!isOpen || !document) return null;

  const handleSaveChanges = async () => {
    try {
      await updateDocument({
        id: document.id,
        data: editForm,
      }).unwrap();
      setIsEditing(false);
    } catch (err) {
      console.error("Backend document modification rejection:", err);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "N/A";
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <Modal isOpen={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className="sm:max-w-[700px] relative">
            <Modal.CloseTrigger>
              <button
                onClick={onClose}
                className="absolute top-4 right-4 text-default-400 hover:text-default-600"
              >
                <X size={18} />
              </button>
            </Modal.CloseTrigger>

            <Modal.Header className="flex flex-col gap-2 items-start pr-8 pb-3 border-b border-default-100">
              {isEditing ? (
                <span className="text-sm font-bold text-primary uppercase tracking-wide">
                  Editing Record Context
                </span>
              ) : (
                <div className="flex items-center gap-2 flex-wrap">
                  <Modal.Heading className="text-xl font-bold text-default-900 tracking-tight">
                    {document.title}
                  </Modal.Heading>
                  <Chip
                    size="sm"
                    variant="flat"
                    color="primary"
                    radius="sm"
                    className="font-semibold"
                  >
                    v{detailedDocument?.version || 1}
                  </Chip>
                </div>
              )}
            </Modal.Header>

            <Modal.Body className="space-y-5 max-h-[65vh] overflow-y-auto px-1 mt-4">
              {isLoading ? (
                <div className="flex flex-col items-center justify-center h-48 gap-3">
                  <Spinner
                    label="Streaming full record contextual layer..."
                    size="md"
                  />
                </div>
              ) : error ? (
                <div className="p-4 text-center bg-danger-50 rounded-xl border border-danger-200/60">
                  <p className="text-sm text-danger font-medium">
                    Failed to sync deep record content.
                  </p>
                </div>
              ) : isEditing ? (
                /* ================= ACTIVE EDITING LAYOUT STATE ================= */
                <div className="space-y-4">
                  <TextField
                    isRequired
                    value={editForm.title}
                    onChange={(val) =>
                      setEditForm((p) => ({ ...p, title: val }))
                    }
                    className="flex flex-col gap-1"
                  >
                    <Label className="text-sm font-medium text-default-700">
                      Document Title
                    </Label>
                    <Input />
                  </TextField>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-default-700">
                        Classification Type
                      </label>
                      <select
                        value={editForm.document_type}
                        onChange={(e) =>
                          setEditForm((p) => ({
                            ...p,
                            document_type: e.target.value,
                          }))
                        }
                        className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none focus:border-primary"
                      >
                        <option value="policy">Policy / Regulation</option>
                        <option value="guide">Guide / Curriculum</option>
                        <option value="faq">FAQ</option>
                        <option value="form">Form</option>
                        <option value="announcement">Announcement</option>
                      </select>
                    </div>

                    <div className="flex flex-col gap-1">
                      <label className="text-sm font-medium text-default-700">
                        Visibility Clearance
                      </label>
                      <select
                        value={editForm.access_level}
                        onChange={(e) =>
                          setEditForm((p) => ({
                            ...p,
                            access_level: e.target.value,
                          }))
                        }
                        className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none focus:border-primary"
                      >
                        <option value="public">Public Access</option>
                        <option value="student">Restricted to Students</option>
                        <option value="professor">Restricted to Faculty</option>
                        <option value="staff">Staff Administrative</option>
                        <option value="president">University President</option>
                      </select>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-default-700">
                      Document Body Content
                    </label>
                    <textarea
                      rows={6}
                      value={editForm.content}
                      onChange={(e) =>
                        setEditForm((p) => ({ ...p, content: e.target.value }))
                      }
                      className="w-full p-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all resize-y focus:border-primary"
                    />
                  </div>
                </div>
              ) : (
                /* ================= STANDARD STATIC INSPECTION VIEW ================= */
                <>
                  {detailedDocument?.summary && (
                    <div className="flex flex-col gap-1.5 bg-primary-50/40 p-4 rounded-xl border border-primary-100/60">
                      <span className="text-xs font-semibold tracking-wider uppercase text-primary-600">
                        AI Generated Summary
                      </span>
                      <p className="text-sm text-primary-900 leading-relaxed">
                        {detailedDocument.summary}
                      </p>
                    </div>
                  )}

                  <div className="flex flex-col gap-1.5 bg-default-50 p-4 rounded-xl border border-default-200/60">
                    <span className="text-xs font-semibold tracking-wider uppercase text-default-400">
                      Document Content Content Layer
                    </span>
                    <p className="text-sm text-default-800 whitespace-pre-wrap leading-relaxed max-h-[250px] overflow-y-auto pr-1">
                      {detailedDocument?.content ||
                        "This document contains no text body content."}
                    </p>
                  </div>

                  {detailedDocument?.keywords && (
                    <div className="flex flex-col gap-1.5">
                      <span className="text-xs font-semibold tracking-wider uppercase text-default-400 flex items-center gap-1">
                        <Tag size={12} /> Keywords
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {detailedDocument.keywords
                          .split(",")
                          .map((word, idx) => (
                            <Chip
                              key={idx}
                              size="sm"
                              variant="bordered"
                              radius="sm"
                            >
                              {word.trim()}
                            </Chip>
                          ))}
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-default-100 text-xs text-default-500">
                    <div className="space-y-1 bg-default-50/50 p-2.5 rounded-lg border border-default-100">
                      <span className="font-medium text-default-700 block mb-1">
                        Author Details
                      </span>
                      <div className="flex items-center gap-1.5">
                        <User size={13} className="text-default-400" />
                        <span className="truncate">
                          {detailedDocument?.created_by_email}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar size={13} className="text-default-400" />
                        <span>
                          Created: {formatDate(detailedDocument?.created_at)}
                        </span>
                      </div>
                    </div>
                    <div className="space-y-1 bg-default-50/50 p-2.5 rounded-lg border border-default-100">
                      <span className="font-medium text-default-700 block mb-1">
                        Modifier Details
                      </span>
                      <div className="flex items-center gap-1.5">
                        <User size={13} className="text-default-400" />
                        <span className="truncate">
                          {detailedDocument?.last_updated_by_email}
                        </span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <Calendar size={13} className="text-default-400" />
                        <span>
                          Modified:{" "}
                          {formatDate(detailedDocument?.last_updated_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                </>
              )}
            </Modal.Body>

            <Modal.Footer className="mt-4 border-t border-default-100 pt-3 flex justify-between items-center">
              <div>
                {/* Render Edit toggle switcher solely to authorized personnel pools */}
                {canManage && !isLoading && !error && (
                  <Button
                    size="sm"
                    variant="flat"
                    color={isEditing ? "danger" : "primary"}
                    startContent={
                      isEditing ? <X size={14} /> : <Edit3 size={14} />
                    }
                    onPress={() => setIsEditing(!isEditing)}
                  >
                    {isEditing ? "Discard Changes" : "Edit Document"}
                  </Button>
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  type="button"
                  onPress={onClose}
                >
                  Close Viewer
                </Button>
                {isEditing && (
                  <Button
                    color="success"
                    size="sm"
                    startContent={<Save size={14} />}
                    isLoading={isUpdating}
                    onPress={handleSaveChanges}
                  >
                    Save Changes
                  </Button>
                )}
              </div>
            </Modal.Footer>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
};
