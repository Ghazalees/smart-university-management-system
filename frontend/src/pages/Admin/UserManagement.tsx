import { useState } from "react";
import { UserPlus } from "lucide-react";
import { Button, Spinner } from "@heroui/react";

import { UsersTable } from "../../components/Admin/UserTable";
import { UserModal } from "../../components/Admin/UserModal";

import {
  useGetUsersQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useUpdateUserRoleMutation,
  useToggleUserStatusMutation,
  useDeleteUserMutation,
} from "../../states/api/adminApi";

export default function UserManagement() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any | null>(null);

  const { data: usersResponse, isLoading: isLoadingUsers } = useGetUsersQuery();
  const users = usersResponse?.data || [];

  const [createUser] = useCreateUserMutation();
  const [updateUser] = useUpdateUserMutation();
  const [updateUserRole] = useUpdateUserRoleMutation();
  const [toggleStatus] = useToggleUserStatusMutation();
  const [deleteUser] = useDeleteUserMutation();

  const handleOpenCreate = () => {
    setEditingUser(null);
    setIsModalOpen(true);
  };

  const handleOpenEdit = (user: any) => {
    setEditingUser(user);
    setIsModalOpen(true);
  };

  const handleToggleStatus = async (userId: number, currentStatus: boolean) => {
    try {
      await toggleStatus({
        id: userId,
        is_active: !currentStatus,
      }).unwrap();
    } catch (err) {
      console.error("Failed to toggle status", err);
    }
  };

  const handleDeleteUser = async (userId: number) => {
    if (
      window.confirm(
        "Are you certain you want to disable this institutional account? This action alters cross-module session privileges.",
      )
    ) {
      try {
        await deleteUser(userId).unwrap();
      } catch (err) {
        console.error("Failed to disable user node identity", err);
      }
    }
  };

  const handleFormSubmit = async (formData: any) => {
    try {
      if (editingUser) {
        const profilePayload = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          profile: formData.profile,
        };

        const updatePromises: Promise<any>[] = [
          updateUser({ id: editingUser.id, ...profilePayload }).unwrap(),
        ];

        if (formData.role !== editingUser.role) {
          updatePromises.push(
            updateUserRole({
              id: editingUser.id,
              role: formData.role,
            }).unwrap(),
          );
        }

        await Promise.all(updatePromises);
      } else {
        await createUser(formData).unwrap();
      }

      setIsModalOpen(false);
    } catch (err) {
      console.error("Failed to save user", err);
    }
  };

  if (isLoadingUsers) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Spinner size="lg" label="Loading system nodes..." color="primary" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-default-100 pb-5">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-default-900">
            User Account Management
          </h1>
          <p className="text-default-500 text-sm mt-1">
            Provision core institutional identities and modify RBAC tiering
            access definitions.
          </p>
        </div>

        <Button
          color="primary"
          startContent={<UserPlus size={18} />}
          onPress={handleOpenCreate}
        >
          Add New User
        </Button>
      </div>

      <UsersTable
        users={users}
        onEdit={handleOpenEdit}
        onToggleStatus={handleToggleStatus}
        onDelete={handleDeleteUser}
      />

      <UserModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSubmit={handleFormSubmit}
        editingUser={editingUser}
      />
    </div>
  );
}
