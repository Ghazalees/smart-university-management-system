import { useEffect, useMemo } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ShieldAlert, X } from "lucide-react";

import {
  Modal,
  TextField,
  Input,
  Button,
  Label,
  FieldError,
} from "@heroui/react";

interface UserModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  editingUser: any | null;
}

const roles = [
  { id: "Student", name: "Student" },
  { id: "Professor", name: "Professor" },
  { id: "AdministrativeStaff", name: "Administrative Staff" },
  { id: "UniversityPresident", name: "University President" },
];

export function UserModal({
  isOpen,
  onClose,
  onSubmit,
  editingUser,
}: UserModalProps) {
  const userSchema = useMemo(() => {
    return z.object({
      email: z.string().email("Invalid email address"),
      username: z.string().min(3, "Username must be at least 3 characters"),
      role: z.enum(
        ["Student", "Professor", "AdministrativeStaff", "UniversityPresident"],
        {
          errorMap: () => ({ message: "Please select a valid system role" }),
        },
      ),
      password: editingUser
        ? z
            .string()
            .min(8, "Password must be at least 8 characters")
            .or(z.literal(""))
        : z.string().min(8, "Password must be at least 8 characters"),
      first_name: z.string().min(1, "First name is required"),
      last_name: z.string().min(1, "Last name is required"),
      profile: z.object({
        phone: z.string().optional().default(""),
        student_number: z.string().optional().default(""),
        employee_number: z.string().optional().default(""),
      }),
    });
  }, [editingUser]);

  type UserFormValues = z.infer<typeof userSchema>;

  const defaultValues: UserFormValues = {
    email: "",
    username: "",
    password: "",
    role: "Student",
    first_name: "",
    last_name: "",
    profile: {
      phone: "",
      student_number: "",
      employee_number: "",
    },
  };

  const form = useForm<UserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues,
  });

  const currentRole = form.watch("role");

  useEffect(() => {
    if (editingUser) {
      form.reset({
        email: editingUser.email || "",
        username: editingUser.username || "",
        password: "",
        role: editingUser.role || "Student",
        first_name: editingUser.first_name || "",
        last_name: editingUser.last_name || "",
        profile: {
          phone: editingUser.profile?.phone || "",
          student_number: editingUser.profile?.student_number || "",
          employee_number: editingUser.profile?.employee_number || "",
        },
      });
    } else {
      form.reset(defaultValues);
    }
  }, [editingUser, form]);

  const handleFormSubmit = (values: UserFormValues) => {
    const computedFullName = `${values.first_name} ${values.last_name}`.trim();

    const APIPayload = {
      ...values,
      profile: {
        ...values.profile,
        full_name: computedFullName,
      },
    };

    onSubmit(APIPayload);
  };

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onOpenChange={(open) => !open && onClose()}>
      <Modal.Backdrop>
        <Modal.Container>
          <Modal.Dialog className="sm:max-w-[600px] relative">
            <Modal.CloseTrigger>
              <button type="button" aria-label="Close modal">
                <X size={18} />
              </button>
            </Modal.CloseTrigger>

            <Modal.Header>
              <Modal.Heading>
                {editingUser
                  ? "Modify Authorization Profile"
                  : "Register Institutional Account"}
              </Modal.Heading>
            </Modal.Header>

            <form onSubmit={form.handleSubmit(handleFormSubmit)}>
              <Modal.Body className="space-y-4 max-h-[70vh] overflow-y-auto px-1">
                <p className="text-sm text-default-500">
                  Ensure attributes align with legal campus domain identity
                  requirements.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Controller
                    name="first_name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        isRequired
                        validationBehavior="aria"
                        isInvalid={!!fieldState.error}
                        value={field.value}
                        onChange={field.onChange}
                        className="flex flex-col gap-1"
                      >
                        <Label>First Name</Label>
                        <Input placeholder="Jane" />
                        <FieldError>{fieldState.error?.message}</FieldError>
                      </TextField>
                    )}
                  />

                  <Controller
                    name="last_name"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        isRequired
                        validationBehavior="aria"
                        isInvalid={!!fieldState.error}
                        value={field.value}
                        onChange={field.onChange}
                        className="flex flex-col gap-1"
                      >
                        <Label>Last Name</Label>
                        <Input placeholder="Doe" />
                        <FieldError>{fieldState.error?.message}</FieldError>
                      </TextField>
                    )}
                  />

                  <Controller
                    name="username"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        isRequired
                        isDisabled={!!editingUser}
                        validationBehavior="aria"
                        isInvalid={!!fieldState.error}
                        value={field.value}
                        onChange={field.onChange}
                        className="flex flex-col gap-1"
                      >
                        <Label>Username</Label>
                        <Input placeholder="janedoe99" />
                        <FieldError>{fieldState.error?.message}</FieldError>
                      </TextField>
                    )}
                  />

                  <Controller
                    name="email"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        isRequired
                        isDisabled={!!editingUser}
                        validationBehavior="aria"
                        isInvalid={!!fieldState.error}
                        value={field.value}
                        onChange={field.onChange}
                        className="flex flex-col gap-1"
                      >
                        <Label>Campus Email Address</Label>
                        <Input
                          type="email"
                          placeholder="username@university.edu"
                        />
                        <FieldError>{fieldState.error?.message}</FieldError>
                      </TextField>
                    )}
                  />

                  <Controller
                    name="password"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <TextField
                        isRequired={!editingUser}
                        validationBehavior="aria"
                        isInvalid={!!fieldState.error}
                        value={field.value}
                        onChange={field.onChange}
                        className="flex flex-col gap-1"
                      >
                        <Label>
                          {editingUser
                            ? "New Password (Optional)"
                            : "Account Password"}
                        </Label>
                        <Input
                          type="password"
                          placeholder="••••••••"
                          autoComplete="new-password"
                        />
                        <FieldError>{fieldState.error?.message}</FieldError>
                      </TextField>
                    )}
                  />

                  <Controller
                    name="role"
                    control={form.control}
                    render={({ field, fieldState }) => (
                      <div className="flex flex-col gap-1">
                        <label className="text-sm font-medium text-default-700">
                          Assigned Domain Role{" "}
                          <span className="text-danger">*</span>
                        </label>
                        <div className="relative">
                          <select
                            value={field.value}
                            onChange={(e) => field.onChange(e.target.value)}
                            className={`w-full h-10 px-3 rounded-xl border bg-background text-sm outline-none transition-all appearance-none cursor-pointer
                              ${
                                fieldState.error
                                  ? "border-danger focus:ring-1 focus:ring-danger"
                                  : "border-default-200 focus:border-primary focus:ring-1 focus:ring-primary hover:border-default-400"
                              }`}
                          >
                            {roles.map((role) => (
                              <option key={role.id} value={role.id}>
                                {role.name}
                              </option>
                            ))}
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
                        {fieldState.error && (
                          <span className="text-xs text-danger">
                            {fieldState.error.message}
                          </span>
                        )}
                      </div>
                    )}
                  />
                </div>

                <div className="pt-2 border-t border-default-100">
                  <h4 className="text-sm font-semibold text-default-800 mb-3">
                    Identity Profile Details
                  </h4>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Controller
                      name="profile.phone"
                      control={form.control}
                      render={({ field, fieldState }) => (
                        <TextField
                          validationBehavior="aria"
                          isInvalid={!!fieldState.error}
                          value={field.value}
                          onChange={field.onChange}
                          className="flex flex-col gap-1"
                        >
                          <Label>Phone Number</Label>
                          <Input placeholder="+1 (555) 000-0000" />
                          <FieldError>{fieldState.error?.message}</FieldError>
                        </TextField>
                      )}
                    />

                    {currentRole === "Student" && (
                      <Controller
                        name="profile.student_number"
                        control={form.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            validationBehavior="aria"
                            isInvalid={!!fieldState.error}
                            value={field.value}
                            onChange={field.onChange}
                            className="flex flex-col gap-1"
                          >
                            <Label>Student ID Number</Label>
                            <Input placeholder="STU-987654" />
                            <FieldError>{fieldState.error?.message}</FieldError>
                          </TextField>
                        )}
                      />
                    )}

                    {currentRole !== "Student" && (
                      <Controller
                        name="profile.employee_number"
                        control={form.control}
                        render={({ field, fieldState }) => (
                          <TextField
                            validationBehavior="aria"
                            isInvalid={!!fieldState.error}
                            value={field.value}
                            onChange={field.onChange}
                            className="flex flex-col gap-1"
                          >
                            <Label>Employee Card Number</Label>
                            <Input placeholder="EMP-123456" />
                            <FieldError>{fieldState.error?.message}</FieldError>
                          </TextField>
                        )}
                      />
                    )}
                  </div>
                </div>

                {editingUser && (
                  <div className="flex gap-3 rounded-lg border border-warning-200 bg-warning-50/20 p-3 text-warning-800">
                    <ShieldAlert size={18} className="shrink-0 mt-0.5" />
                    <div>
                      <div className="font-semibold text-sm">
                        Privilege Alteration Notice
                      </div>
                      <div className="text-xs text-default-600">
                        Updating structural system roles forces instant
                        permission profile migrations across modules.
                      </div>
                    </div>
                  </div>
                )}
              </Modal.Body>

              <Modal.Footer className="mt-4">
                <Button variant="secondary" type="button" onPress={onClose}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit">
                  {editingUser ? "Apply Mutation" : "Register Account"}
                </Button>
              </Modal.Footer>
            </form>
          </Modal.Dialog>
        </Modal.Container>
      </Modal.Backdrop>
    </Modal>
  );
}
