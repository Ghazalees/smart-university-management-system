import { useState } from "react";
import { Button } from "@heroui/react";
import { Plus } from "lucide-react";
import {
  useGetDocumentsQuery,
  type DocumentItem,
} from "../states/api/documentsApi";
import { useAuth } from "../hooks/useAuth";

import { DocumentTable } from "../components/Document/DocumentTable";
import { DocumentSearchBar } from "../components/Document/DocumentSearchBar";
import { AddDocumentModal } from "../components/Document/AddDocumentModal";
import { ViewDocumentModal } from "../components/Document/ViewDocumentModal";

export const DocumentDashboard = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentItem | null>(
    null,
  );

  // Search State Managers
  const [searchResults, setSearchResults] = useState<DocumentItem[] | null>(
    null,
  );
  const [isSearching, setIsSearching] = useState(false);

  const { role, user } = useAuth();

  // Role verification checks
  const canManageDocuments =
    role === "staff" ||
    role === "president" ||
    user?.email?.endsWith("@university.local");

  // Default fetch hooks skip execution automatically if an active query is managed by searchBar parameters
  const { data: defaultDocuments, isLoading: isLoadingDefault } =
    useGetDocumentsQuery(undefined, {
      skip: isSearching,
    });

  // Pick dataset layer depending on active operational mode flags
  const activeDocuments = isSearching
    ? searchResults || []
    : defaultDocuments?.data || [];

  const isLoading = !isSearching && isLoadingDefault;
  console.log(activeDocuments);
  const handleSearchSync = (
    results: DocumentItem[] | null,
    searching: boolean,
  ) => {
    setSearchResults(results);
    setIsSearching(searching);
  };

  const handleOpenViewModal = (doc: DocumentItem) => {
    setSelectedDocument(doc);
    setIsViewOpen(true);
  };

  const handleCloseViewModal = () => {
    setIsViewOpen(false);
    setSelectedDocument(null);
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Title Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-sm text-default-500">
            Manage institutional documents and system parameters for AI query
            mapping.
          </p>
        </div>

        {canManageDocuments && (
          <Button
            color="primary"
            startContent={<Plus size={18} />}
            onPress={() => setIsOpen(true)}
          >
            Add Document
          </Button>
        )}
      </div>

      {/* Advanced Filtering Form Container */}
      <div className="bg-default-50 p-4 rounded-xl border border-default-200/60">
        <DocumentSearchBar onSearchChange={handleSearchSync} />
      </div>

      {/* Main Grid View */}
      <DocumentTable
        documents={activeDocuments}
        isLoading={isLoading}
        onView={handleOpenViewModal}
        canManage={canManageDocuments}
      />

      {/* Upload Sheet */}
      {canManageDocuments && (
        <AddDocumentModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
      )}

      {/* Dual Inspection and Edit Mode Context Sheet */}
      <ViewDocumentModal
        document={selectedDocument}
        isOpen={isViewOpen}
        onClose={handleCloseViewModal}
        canManage={canManageDocuments}
      />
    </div>
  );
};
