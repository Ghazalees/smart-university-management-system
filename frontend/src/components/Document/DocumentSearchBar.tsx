import { useState } from "react";
import { Input, Button, Label, Switch } from "@heroui/react";
import { Search, RotateCcw } from "lucide-react";
import {
  useLazySearchDocumentsQuery,
  type DocumentItem,
} from "../../states/api/documentsApi";

interface DocumentSearchBarProps {
  onSearchChange: (
    results: DocumentItem[] | null,
    isSearching: boolean,
  ) => void;
}

export const DocumentSearchBar = ({
  onSearchChange,
}: DocumentSearchBarProps) => {
  const [triggerSearch, { isLoading }] = useLazySearchDocumentsQuery();

  // Local state matching backend query serializing keys
  const [filters, setFilters] = useState({
    title: "",
    document_type: "",
    access_level: "",
    is_knowledge_base_enabled: false,
  });

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // If all fields are unpopulated, consider it an idle/reset state
    if (
      !filters.title &&
      !filters.document_type &&
      !filters.access_level &&
      !filters.is_knowledge_base_enabled
    ) {
      onSearchChange(null, false);
      return;
    }

    try {
      // Build clean payload stripping unselected filters
      const queryParams: Record<string, any> = {};
      if (filters.title) queryParams.title = filters.title;
      if (filters.document_type)
        queryParams.document_type = filters.document_type; // Fixed the filters.filters chain typo
      if (filters.access_level) queryParams.access_level = filters.access_level;
      if (filters.is_knowledge_base_enabled)
        queryParams.is_knowledge_base_enabled = true;

      const response = await triggerSearch(queryParams).unwrap();
      onSearchChange(response.data, true);
    } catch (err) {
      console.error("Knowledge base system search failed:", err);
    }
  };

  const handleReset = () => {
    setFilters({
      title: "",
      document_type: "",
      access_level: "",
      is_knowledge_base_enabled: false,
    });
    onSearchChange(null, false);
  };

  return (
    <form onSubmit={handleSearchSubmit} className="w-full space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        {/* Text Input Context Search */}
        <div className="flex flex-col gap-1 md:col-span-1">
          <label className="text-xs font-semibold text-default-600 uppercase tracking-wider">
            Search Content
          </label>

          {/* Layout composition avoids prop-leaking into primitive HTML nodes */}
          <div className="relative flex items-center w-full">
            <Search
              size={16}
              className="absolute left-3 text-default-400 pointer-events-none z-10"
            />
            <Input
              placeholder="Search by title or topic..."
              className="pl-9 w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all focus:border-primary"
              value={filters.title}
              onChange={(e) =>
                setFilters((prev) => ({ ...prev, title: e.target.value }))
              }
            />
          </div>
        </div>

        {/* Classification Filters */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold text-default-600 uppercase tracking-wider">
            Doc Type
          </label>
          <select
            value={filters.document_type}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, document_type: e.target.value }))
            }
            className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all cursor-pointer focus:border-primary"
          >
            <option value="">All Classifications</option>
            <option value="policy">Policy / Regulation</option>
            <option value="guide">Guide / Curriculum</option>
            <option value="faq">FAQ</option>
            <option value="form">Form</option>
            <option value="announcement">Announcement</option>
          </select>
        </div>

        {/* Access Restriction Rules */}
        <div className="flex flex-col gap-1">
          <label className="text-xs font-semibold text-default-600 uppercase tracking-wider">
            Clearance
          </label>
          <select
            value={filters.access_level}
            onChange={(e) =>
              setFilters((prev) => ({ ...prev, access_level: e.target.value }))
            }
            className="w-full h-10 px-3 rounded-xl border border-default-200 bg-background text-sm outline-none transition-all cursor-pointer focus:border-primary"
          >
            <option value="">All Clearance Levels</option>
            <option value="public">Public</option>
            <option value="student">Student</option>
            <option value="professor">Faculty</option>
            <option value="staff">Staff Administrative</option>
            <option value="president">University President</option>
          </select>
        </div>

        {/* Interactive Action Control Subpanel */}
        <div className="flex items-center gap-3 h-10 pb-1">
          <Switch
            isSelected={filters.is_knowledge_base_enabled}
            onChange={(val) =>
              setFilters((prev) => ({
                ...prev,
                is_knowledge_base_enabled: val,
              }))
            }
          >
            <Switch.Control>
              <Switch.Thumb />
            </Switch.Control>
            <Switch.Content>
              <Label className="text-sm font-medium text-default-700 whitespace-nowrap">
                KB Only
              </Label>
            </Switch.Content>
          </Switch>

          <div className="flex gap-2 ml-auto">
            <Button
              isIconOnly
              variant="flat"
              size="sm"
              type="button"
              onClick={handleReset}
              aria-label="Reset forms"
            >
              <RotateCcw size={16} />
            </Button>
            <Button
              color="primary"
              size="sm"
              type="submit"
              isLoading={isLoading}
            >
              Search
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
};
