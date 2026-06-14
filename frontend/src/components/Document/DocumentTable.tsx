import {
  Table,
  Button,
  Chip,
  Spinner,
  EmptyState,
  Switch,
  Label,
} from "@heroui/react";
import { Trash2, Eye, Box } from "lucide-react";
import {
  useDeleteDocumentMutation,
  useUpdateDocumentMutation,
  type DocumentItem,
} from "../../states/api/documentsApi";

interface DocumentTableProps {
  documents: DocumentItem[];
  isLoading: boolean;
  onView: (document: DocumentItem) => void;
  canManage: boolean;
}

export const DocumentTable = ({
  documents,
  isLoading,
  onView,
  canManage,
}: DocumentTableProps) => {
  const [deleteDocument, { isLoading: isDeleting }] =
    useDeleteDocumentMutation();
  const [updateDocument] = useUpdateDocumentMutation();

  const handleDelete = async (id: number) => {
    const confirmSystemArchive = window.confirm(
      "Are you sure you want to archive this institutional record? This action soft-deletes the row.",
    );
    if (!confirmSystemArchive) return;

    try {
      await deleteDocument(id).unwrap();
    } catch (error: any) {
      alert(error?.data?.message || "Failed to delete document entry.");
      console.error("Failed to delete document entry:", error);
    }
  };

  const handleToggleKnowledgeBase = async (
    id: number,
    currentStatus: boolean,
  ) => {
    try {
      await updateDocument({
        id,
        data: { is_knowledge_base_enabled: !currentStatus },
      }).unwrap();
    } catch (error: any) {
      alert(
        error?.data?.message ||
          "Failed to update search engine indexing parameter.",
      );
      console.error("Failed to toggle knowledge base setting:", error);
    }
  };

  const safeDocuments = Array.isArray(documents) ? documents : [];

  return (
    <Table aria-label="University knowledge base registry documents table">
      <Table.ScrollContainer>
        <Table.Content aria-label="Institutional documents registry datagrid">
          <Table.Header>
            <Table.Column key="title" isRowHeader>
              DOCUMENT TITLE
            </Table.Column>
            <Table.Column key="type">TYPE</Table.Column>
            <Table.Column key="access">ACCESS LEVEL</Table.Column>
            <Table.Column key="kb_status" align="center">
              KB SYNCED
            </Table.Column>
            <Table.Column key="updated">LAST UPDATED</Table.Column>
            <Table.Column key="actions" align="center">
              ACTIONS
            </Table.Column>
          </Table.Header>

          <Table.Body
            isLoading={isLoading}
            loadingContent={
              <Spinner label="Syncing dataset indexing files..." />
            }
            renderEmptyState={() => (
              <EmptyState className="flex h-full w-full flex-col items-center justify-center gap-4 text-center py-10">
                <Box className="size-8 text-default-400" />
                <span className="text-sm text-default-500 font-medium">
                  No institutional records found matching the criteria.
                </span>
              </EmptyState>
            )}
          >
            {safeDocuments.map((doc) => (
              <Table.Row
                key={String(doc.id)}
                className="hover:bg-default-50 transition-colors"
              >
                {/* Title Context cell */}
                <Table.Cell className="font-medium text-default-900 max-w-xs truncate">
                  {doc.title}
                </Table.Cell>

                {/* Classification cell */}
                <Table.Cell>
                  <Chip
                    size="sm"
                    variant="flat"
                    radius="sm"
                    className="capitalize"
                  >
                    {doc.document_type}
                  </Chip>
                </Table.Cell>

                {/* Security Access level cell */}
                <Table.Cell>
                  <Chip
                    size="sm"
                    variant="dot"
                    className="capitalize"
                    color={
                      doc.access_level?.toLowerCase() === "public"
                        ? "success"
                        : "warning"
                    }
                  >
                    {doc.access_level}
                  </Chip>
                </Table.Cell>

                {/* Custom Compound Switch Column Cell */}
                <Table.Cell>
                  <div className="flex justify-center">
                    <Switch
                      isSelected={doc.is_knowledge_base_enabled}
                      isDisabled={!canManage}
                      onChange={() =>
                        handleToggleKnowledgeBase(
                          doc.id,
                          doc.is_knowledge_base_enabled,
                        )
                      }
                    >
                      <Switch.Control>
                        <Switch.Thumb />
                      </Switch.Control>
                      <Switch.Content>
                        {/* Using 'sr-only' hides the label text visually so it doesn't distort row spaces,
                          while preserving access tokens cleanly for assistive technologies.
                        */}
                        <Label className="sr-only">
                          Enable knowledge base indexation for {doc.title}
                        </Label>
                      </Switch.Content>
                    </Switch>
                  </div>
                </Table.Cell>

                {/* Audit Timestamp Cell */}
                <Table.Cell className="text-default-500 text-sm whitespace-nowrap">
                  {doc.updated_at
                    ? new Date(doc.updated_at).toLocaleDateString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })
                    : "Not Indexed"}
                </Table.Cell>

                {/* User Interactivity Actions Cell */}
                <Table.Cell>
                  <div className="flex items-center justify-center gap-2">
                    <Button
                      isIconOnly
                      size="sm"
                      variant="light"
                      onPress={() => onView(doc)}
                      aria-label="View asset details"
                    >
                      <Eye size={16} className="text-default-500" />
                    </Button>

                    {canManage && (
                      <Button
                        isIconOnly
                        size="sm"
                        variant="light"
                        color="danger"
                        isDisabled={isDeleting}
                        onPress={() => handleDelete(doc.id)}
                        aria-label="Remove asset file record"
                      >
                        <Trash2 size={16} />
                      </Button>
                    )}
                  </div>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table.Body>
        </Table.Content>
      </Table.ScrollContainer>
    </Table>
  );
};
