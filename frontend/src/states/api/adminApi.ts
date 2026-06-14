import { baseApi } from "./baseApi";

export const adminApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getUsers: builder.query<any[], void>({
      query: () => "users",
      providesTags: ["User"],
    }),
    getRoles: builder.query<any[], void>({
      query: () => "roles",
      providesTags: ["Role"],
    }),
    createUser: builder.mutation<any, Partial<any>>({
      query: (body) => ({
        url: "users",
        method: "POST",
        body,
      }),
      invalidatesTags: ["User"], // Forces the table to refresh
    }),
    updateUser: builder.mutation<any, { id: number; [key: string]: any }>({
      query: ({ id, ...body }) => ({
        url: `users/${id}`,
        method: "PATCH",
        body,
      }),
      invalidatesTags: ["User"],
    }),
    updateUserRole: builder.mutation<any, { id: number; role: string }>({
      query: ({ id, role }) => ({
        url: `users/${id}/role`,
        method: "PATCH",
        body: { role },
      }),
      invalidatesTags: ["User"],
    }),
    toggleUserStatus: builder.mutation<any, { id: number; is_active: boolean }>(
      {
        query: ({ id, is_active }) => ({
          url: `users/${id}`,
          method: "PATCH",
          body: { is_active },
        }),
        invalidatesTags: ["User"],
      },
    ),
    deleteUser: builder.mutation<any, number | string>({
      query: (id) => ({
        url: `users/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: ["User"],
    }),
  }),
});

export const {
  useGetUsersQuery,
  useGetRolesQuery,
  useCreateUserMutation,
  useUpdateUserMutation,
  useUpdateUserRoleMutation,
  useToggleUserStatusMutation,
  useDeleteUserMutation,
} = adminApi;
