import { useState, useEffect } from "react";
import { X, AlertCircle } from "lucide-react";
import { Modal, TextField, Input, Button, Label } from "@heroui/react";
import { useCreateDocumentMutation } from "../../states/api/documentsApi";

interface AddDocumentModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const AddDocumentModal = ({
  isOpen,
  onClose,
}: AddDocumentModalProps) => {
  const [createDocument, { isLoading }] = useCreateDocumentMutation();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    title: "",
    document_type: "",
    access_level: "",
    content: "",
  });

  // Wipe previous validation or auth errors every time the modal visibility changes
  useEffect(() => {
    if (!isOpen) {
      setErrorMessage(null);
      setFormData({
        title: "",
        document_type: "",
        access_level: "",
        content: "",
      });
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!formData.title || !formData.document_type || !formData.access_level) {
      setErrorMessage("Please populate all required system fields.");
      return;
    }

    try {
      await createDocument(formData).unwrap();
      onClose();
    } catch (err: any) {
      // Direct extraction of custom messages processed by your Django views
      const serverMessage =
        err?.data?.message ||
        "An unexpected error occurred while indexing this document.";
      setErrorMessage(serverMessage);
      console.error("Failed to save institutional document:", err);
    }
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className="sm:max-w-[600px] relative">
            <Modal.CloseTrigger>
              <button
                type="button"
                aria-label="Close modal"
                onClick={onClose}
                className="absolute top-4 right-4 text-default-400 hover:text-default-600 transition-colors"
              >
                <X size={18} />
              </button>
            </Modal.CloseTrigger>

            <Modal.Header className="pb-2">
              <Modal.Heading className="text-xl font-bold text-default-900 tracking-tight">
                Index New Document
              </Modal.Heading>
            </Modal.Header>

            <form onSubmit={handleSubmit}>
              <Modal.Body className="space-y-4 max-h-[70vh] overflow-y-auto px-1">
                <p className="text-sm text-default-500">
                  Add institutional records to feed the AI context mapping
                  layers.
                </p>

                {/* Server Error Notification Context Banner */}
                {errorMessage && (
                  <div className="flex gap-2 p-3 bg-danger-50 text-danger border border-danger-200/60 rounded-xl items-start animate-fade-in">
                    <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                    <div className="text-xs font-medium leading-relaxed">
                      {errorMessage}
                    </div>
                  </div>
                )}

                {/* Document Title Input */}
                <TextField
                  isRequired
                  validationBehavior="aria"
                  value={formData.title}
                  onChange={(val) => {
                    if (errorMessage) setErrorMessage(null);
                    setFormData((prev) => ({ ...prev, title: val }));
                  }}
                  className="flex flex-col gap-1"
                >
                  <Label className="text-sm font-medium text-default-700">
                    Document Title
                  </Label>
                  <Input placeholder="e.g., Undergraduate Academic Regulations 2026" />
                </TextField>

                {/* Dropdowns Configuration Layout */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Classification Type Selector */}
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-default-700">
                      Document Classification Type{" "}
                      <span className="text-danger">*</span>
                    </label>
                    <div className="relative">
                      <select
                        value={formData.document_type}
                        onChange={(e) => {
                          if (errorMessage) setErrorMessage(null);
                          setFormData((prev) => ({
                            ...prev,
                            document_type: e.target.value,
                          }));
                        }}
                        className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all appearance-none cursor-pointer focus:border-primary focus:ring-1 focus:ring-primary hover:border-default-400"
                      >
                        <option value="" disabled hidden>
                          Select type
                        </option>
                        <option value="policy">Policy / Regulation</option>
                        <option value="guide">Guide / Curriculum</option>
                        <option value="faq">FAQ</option>
                        <option value="form">Form</option>
                        <option value="announcement">Announcement</option>
                        <option value="other">Other</option>
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-default-400">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>

                  {/* RBAC Visibility Selector */}
                  <div className="flex flex-col gap-1">
                    <label className="text-sm font-medium text-default-700">
                      RBAC Minimum Visibility Group{" "}
                      <span className="text-danger">*</span>
                    </label>
                    <div className="relative">
                      <select
                        value={formData.access_level}
                        onChange={(e) => {
                          if (errorMessage) setErrorMessage(null);
                          setFormData((prev) => ({
                            ...prev,
                            access_level: e.target.value,
                          }));
                        }}
                        className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all appearance-none cursor-pointer focus:border-primary focus:ring-1 focus:ring-primary hover:border-default-400"
                      >
                        <option value="" disabled hidden>
                          Select clearance restriction
                        </option>
                        <option value="public">Public Access</option>
                        <option value="student">Restricted to Students</option>
                        <option value="professor">Restricted to Faculty</option>
                        <option value="staff">Staff Administrative Only</option>
                        <option value="president">University President</option>
                      </select>
                      <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-default-400">
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth="2"
                            d="M19 9l-7 7-7-7"
                          />
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Custom Native Textarea Layout */}
                <div className="flex flex-col gap-1">
                  <label className="text-sm font-medium text-default-700">
                    Document Content Context Layer
                  </label>
                  <textarea
                    placeholder="Paste structural raw document text sentences or regulation articles processed for vector generation pipelines..."
                    rows={5}
                    value={formData.content}
                    onChange={(e) =>
                      setFormData((prev) => ({
                        ...prev,
                        content: e.target.value,
                      }))
                    }
                    className="w-full p-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all resize-y hover:border-default-400 focus:border-primary focus:ring-1 focus:ring-primary"
                  />
                </div>
              </Modal.Body>

              <Modal.Footer className="mt-6 border-t border-default-100 pt-3">
                <Button
                  variant="secondary"
                  type="button"
                  onPress={onClose}
                  isDisabled={isLoading}
                >
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  type="submit"
                  isLoading={isLoading}
                  isDisabled={isLoading}
                >
                  Confirm Upload
                </Button>
              </Modal.Footer>
            </form>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
};
