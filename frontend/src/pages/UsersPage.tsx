/** Renders the UsersPage workspace and coordinates its API-driven interactions. */

import { useMemo, useState } from "react";
import { Pencil, Plus, Search, UserCheck, UserMinus } from "lucide-react";
import {
  useAssignRolesMutation,
  useCreateUserMutation,
  useDeactivateUserMutation,
  useReactivateUserMutation,
  useRolesQuery,
  useUpdateUserMutation,
  useUsersQuery,
} from "../services/api";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import type { User } from "../types";
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
import { getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

export function UsersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [createRoleId, setCreateRoleId] = useState("");
  const [editing, setEditing] = useState<User | null>(null);
  const [selectedRoleIds, setSelectedRoleIds] = useState<number[]>([]);
  const { user: currentUser } = useAppSelector(selectAuth);
  const { data, isLoading, error } = useUsersQuery({ page, search });
  const { data: rolesData } = useRolesQuery();
  const [createUser, createState] = useCreateUserMutation();
  const [updateUser, updateState] = useUpdateUserMutation();
  const [assignRoles, roleState] = useAssignRolesMutation();
  const [deactivate] = useDeactivateUserMutation();
  const [reactivate] = useReactivateUserMutation();
  const { show } = useToast();

  const rolesByName = useMemo(
    () => new Map(rolesData?.data.map((role) => [role.name, role.id]) ?? []),
    [rolesData],
  );
  const createRole = rolesData?.data.find((role) => role.id === Number(createRoleId));
  const isStudentAccount = createRole?.name === "Student";

  function closeCreate() {
    setShowCreate(false);
    setCreateRoleId("");
  }

  function openEdit(target: User) {
    setEditing(target);
    setSelectedRoleIds(
      target.roles
        .map((role) => rolesByName.get(role))
        .filter((id): id is number => Boolean(id)),
    );
  }

  function toggleRole(roleId: number, checked: boolean) {
    setSelectedRoleIds((current) =>
      checked
        ? Array.from(new Set([...current, roleId]))
        : current.filter((id) => id !== roleId),
    );
  }

  async function create(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const roleId = Number(createRoleId || form.get("role_id"));
    const password = String(form.get("password") || "");
    const passwordConfirmation = String(form.get("password_confirmation") || "");
    const studentNumber = String(form.get("student_number") || "").trim();

    if (!roleId) {
      show("Choose a role for the account.", "error");
      return;
    }
    if (password !== passwordConfirmation) {
      show("Password and confirmation do not match.", "error");
      return;
    }
    if (isStudentAccount && !studentNumber) {
      show("Student number is required for a student account.", "error");
      return;
    }

    try {
      await createUser({
        username: String(form.get("username") || "").trim(),
        email: String(form.get("email") || "").trim().toLowerCase(),
        first_name: String(form.get("first_name") || "").trim(),
        last_name: String(form.get("last_name") || "").trim(),
        password,
        role_ids: [roleId],
        profile: {
          phone: String(form.get("phone") || "").trim(),
          student_number: studentNumber,
          employee_number: String(form.get("employee_number") || "").trim(),
          bio: "",
        },
      }).unwrap();
      show(isStudentAccount ? "Student account registered successfully" : "User account created");
      closeCreate();
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function saveEdit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const form = new FormData(event.currentTarget);
    if (editing.id !== currentUser?.id && !selectedRoleIds.length) {
      show("At least one role must remain assigned.", "error");
      return;
    }
    try {
      await updateUser({
        id: editing.id,
        body: {
          email: String(form.get("email") || "").trim().toLowerCase(),
          first_name: String(form.get("first_name") || "").trim(),
          last_name: String(form.get("last_name") || "").trim(),
          profile: {
            phone: String(form.get("phone") || "").trim(),
            student_number: String(form.get("student_number") || "").trim(),
            employee_number: String(form.get("employee_number") || "").trim(),
            bio: String(form.get("bio") || "").trim(),
          },
        },
      }).unwrap();
      if (editing.id !== currentUser?.id) {
        await assignRoles({ id: editing.id, role_ids: selectedRoleIds }).unwrap();
      }
      show("User profile and access updated");
      setEditing(null);
      setSelectedRoleIds([]);
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  async function toggle(id: number, active: boolean) {
    if (!window.confirm(active ? "Deactivate this account?" : "Reactivate this account?")) return;
    try {
      if (active) await deactivate(id).unwrap();
      else await reactivate(id).unwrap();
      show(active ? "Account deactivated" : "Account reactivated");
    } catch (reason) {
      show(getErrorMessage(reason), "error");
    }
  }

  return (
    <div className="page-stack">
      <PageHeader
        title="People and access"
        description="Create accounts, maintain identity records and assign role-based access safely."
        action={<Button onClick={() => setShowCreate(true)}><Plus />New user</Button>}
      />
      <Card className="toolbar">
        <div className="search-box">
          <Search />
          <input
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
            }}
            placeholder="Search name, email or university ID"
          />
        </div>
      </Card>

      {isLoading ? (
        <LoadingState label="Loading people" />
      ) : error ? (
        <ErrorState />
      ) : !data?.data.length ? (
        <EmptyState title="No matching users" />
      ) : (
        <Card className="table-card">
          <div className="table-scroll">
            <table>
              <thead><tr><th>User</th><th>Roles</th><th>Department</th><th>Status</th><th aria-label="Actions" /></tr></thead>
              <tbody>
                {data.data.map((user) => (
                  <tr key={user.id}>
                    <td>
                      <div className="person-cell">
                        <span className="avatar">{(user.first_name || user.username)[0].toUpperCase()}</span>
                        <div><strong>{user.full_name}</strong><span>{user.email}</span></div>
                      </div>
                    </td>
                    <td><div className="badge-row">{user.roles.map((role) => <Badge key={role} tone="info">{role}</Badge>)}</div></td>
                    <td>{user.department?.name || "—"}</td>
                    <td><Badge tone={user.is_active ? "success" : "danger"}>{user.is_active ? "Active" : "Inactive"}</Badge></td>
                    <td>
                      <div className="table-actions">
                        <Button variant="ghost" onClick={() => openEdit(user)}><Pencil />Edit</Button>
                        <Button
                          variant="ghost"
                          onClick={() => void toggle(user.id, user.is_active)}
                          disabled={user.id === currentUser?.id}
                        >
                          {user.is_active ? <UserMinus /> : <UserCheck />}
                          {user.is_active ? "Deactivate" : "Reactivate"}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={page} pages={data.pagination?.pages ?? 1} onChange={setPage} />
        </Card>
      )}

      {showCreate ? (
        <Modal title="Create university account" onClose={closeCreate}>
          <form className="form-grid" onSubmit={create}>
            <Input name="first_name" label="First name" autoComplete="given-name" required />
            <Input name="last_name" label="Last name" autoComplete="family-name" required />
            <Input name="username" label="Username" autoComplete="off" required />
            <Input name="email" label="Email" type="email" autoComplete="email" required />
            <Input
              name="password"
              label="Temporary password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              hint="Use at least 8 characters and avoid common or fully numeric passwords."
              required
            />
            <Input
              name="password_confirmation"
              label="Confirm password"
              type="password"
              autoComplete="new-password"
              minLength={8}
              required
            />
            <Select
              name="role_id"
              label="Role"
              value={createRoleId}
              onChange={(event) => setCreateRoleId(event.target.value)}
              required
            >
              <option value="">Choose a role</option>
              {rolesData?.data.map((role) => <option key={role.id} value={role.id}>{role.name}</option>)}
            </Select>
            <Input name="phone" label="Phone" autoComplete="tel" />
            {isStudentAccount ? (
              <div className="form-span-2">
                <Input
                  name="student_number"
                  label="Student number"
                  hint="Required and unique for student accounts."
                  required
                />
              </div>
            ) : (
              <div className="form-span-2">
                <Input
                  name="employee_number"
                  label="Employee number"
                  hint="Optional, but must be unique when provided."
                />
              </div>
            )}
            <div className="modal-actions form-span-2">
              <Button type="button" variant="secondary" onClick={closeCreate}>Cancel</Button>
              <Button type="submit" disabled={createState.isLoading}>
                {createState.isLoading ? "Creating…" : isStudentAccount ? "Register student" : "Create account"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}

      {editing ? (
        <Modal
          title={`Edit ${editing.full_name}`}
          onClose={() => {
            setEditing(null);
            setSelectedRoleIds([]);
          }}
        >
          <form className="form-grid" onSubmit={saveEdit}>
            <Input name="first_name" label="First name" defaultValue={editing.first_name} required />
            <Input name="last_name" label="Last name" defaultValue={editing.last_name} required />
            <Input name="email" label="Email" type="email" defaultValue={editing.email} required />
            <Input name="phone" label="Phone" defaultValue={editing.profile?.phone} />
            <Input name="student_number" label="Student number" defaultValue={editing.profile?.student_number} />
            <Input name="employee_number" label="Employee number" defaultValue={editing.profile?.employee_number} />
            <label className="field form-span-2">
              <span className="field-label">Profile notes</span>
              <textarea className="input textarea" name="bio" rows={3} defaultValue={editing.profile?.bio} />
            </label>
            <div className="form-span-2">
              <span className="field-label">Assigned roles</span>
              <div className="choice-grid">
                {rolesData?.data.map((role) => (
                  <label
                    key={role.id}
                    className={`choice-card ${editing.id === currentUser?.id ? "choice-disabled" : ""}`}
                  >
                    <input
                      type="checkbox"
                      disabled={editing.id === currentUser?.id}
                      checked={selectedRoleIds.includes(role.id)}
                      onChange={(event) => toggleRole(role.id, event.target.checked)}
                    />
                    <span>{role.name}</span>
                  </label>
                ))}
              </div>
              {editing.id === currentUser?.id ? (
                <small className="field-hint">For safety, administrators cannot change their own roles.</small>
              ) : null}
            </div>
            <div className="modal-actions form-span-2">
              <Button type="button" variant="secondary" onClick={() => { setEditing(null); setSelectedRoleIds([]); }}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateState.isLoading || roleState.isLoading}>
                {updateState.isLoading || roleState.isLoading ? "Saving…" : "Save changes"}
              </Button>
            </div>
          </form>
        </Modal>
      ) : null}
    </div>
  );
}
