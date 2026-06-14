import React, { useCallback } from "react";
import { Edit2, Trash2 } from "lucide-react";
import { Table, Chip, Button, Switch } from "@heroui/react";

interface UsersTableProps {
  users: any[];
  onEdit: (user: any) => void;
  onToggleStatus: (userId: number, currentStatus: boolean) => void;
  onDelete: (userId: number) => void;
}

const roleMap: Record<
  string,
  {
    label: string;
    color: "success" | "secondary" | "primary" | "warning" | "default";
  }
> = {
  Student: { label: "Student", color: "success" },
  Professor: { label: "Professor", color: "secondary" },
  AdministrativeStaff: { label: "Administrative Staff", color: "primary" },
  UniversityPresident: { label: "University President", color: "warning" },
};

export function UsersTable({
  users,
  onEdit,
  onToggleStatus,
  onDelete,
}: UsersTableProps) {
  const renderCell = useCallback(
    (user: any, columnKey: React.Key) => {
      switch (columnKey) {
        case "identity": {
          const computedName =
            user.profile?.full_name ||
            `${user.first_name} ${user.last_name}`.trim() ||
            user.username;
          const initials = computedName.substring(0, 2).toUpperCase();

          return (
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-8 h-8 rounded-full bg-default-100 font-semibold text-xs text-default-600 shrink-0 select-none">
                {initials}
              </div>
              <div className="flex flex-col text-left">
                <span className="text-sm font-medium text-default-800 leading-tight">
                  {computedName}
                </span>
                <span className="text-xs text-default-400 mt-0.5">
                  {user.email}
                </span>
              </div>
            </div>
          );
        }

        case "identifier": {
          const institutionalId =
            user.profile?.student_number ||
            user.profile?.employee_number ||
            "—";
          return (
            <span className="font-mono text-xs text-default-600 bg-default-50 px-2 py-1 rounded-md border border-default-100">
              {institutionalId}
            </span>
          );
        }

        case "role": {
          const currentRole = user.role
            ? roleMap[user.role]
            : { label: "Unassigned", color: "default" as const };
          return (
            <Chip size="sm" variant="flat" color={currentRole.color}>
              {currentRole.label}
            </Chip>
          );
        }

        case "status": {
          return (
            <div className="flex items-center gap-3">
              <Switch
                size="sm"
                isSelected={user.is_active}
                onValueChange={() => onToggleStatus(user.id, user.is_active)}
              />
              <span
                className={`text-sm ${
                  user.is_active
                    ? "text-success-600 font-medium"
                    : "text-default-400"
                }`}
              >
                {user.is_active ? "Active" : "Disabled"}
              </span>
            </div>
          );
        }

        case "actions": {
          return (
            <div className="flex justify-end gap-2">
              <Button
                size="sm"
                variant="light"
                color="primary"
                startContent={<Edit2 size={14} />}
                onPress={() => onEdit(user)}
              >
                Edit
              </Button>
              <Button
                size="sm"
                variant="light"
                color="danger"
                startContent={<Trash2 size={14} />}
                onPress={() => onDelete(user.id)}
              >
                Delete
              </Button>
            </div>
          );
        }

        default:
          return null;
      }
    },
    [onEdit, onToggleStatus, onDelete],
  );

  return (
    <Table aria-label="Institutional accounts management table" removeWrapper>
      <Table.ScrollContainer>
        <Table.Content className="min-w-[600px]">
          <Table.Header>
            <Table.Column isRowHeader key="identity">
              IDENTITY CORE
            </Table.Column>
            <Table.Column key="identifier">CAMPUS IDENTIFIER</Table.Column>
            <Table.Column key="role">SYSTEM ROLE</Table.Column>
            <Table.Column key="status">ACCOUNT STATUS</Table.Column>
            <Table.Column key="actions" align="end">
              ACTIONS
            </Table.Column>
          </Table.Header>

          <Table.Body
            items={users || []}
            emptyContent="No active system records discovered within current cluster nodes."
          >
            {(item: any) => (
              <Table.Row key={String(item.id)}>
                <Table.Cell>{renderCell(item, "identity")}</Table.Cell>
                <Table.Cell>{renderCell(item, "identifier")}</Table.Cell>
                <Table.Cell>{renderCell(item, "role")}</Table.Cell>
                <Table.Cell>{renderCell(item, "status")}</Table.Cell>
                <Table.Cell>{renderCell(item, "actions")}</Table.Cell>
              </Table.Row>
            )}
          </Table.Body>
        </Table.Content>
      </Table.ScrollContainer>
    </Table>
  );
}
