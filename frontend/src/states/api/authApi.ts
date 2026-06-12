import type { MeResponse } from "../../types/auth";
import { logout, setCredentials } from "../authSlice";
import { baseApi } from "./baseApi";

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    login: builder.mutation({
      query: (credentials) => ({
        url: "api/v1/auth/login",
        method: "POST",
        body: credentials,
      }),
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        try {
          const { data } = await queryFulfilled;

          if (data.success) {
            const { user, token, role } = data.data;

            dispatch(
              setCredentials({
                user,
                accessToken: token,
                role,
              }),
            );
          }
        } catch (error) {
          console.error("Login failed:", error);
        }
      },
    }),

    logout: builder.mutation({
      query: () => ({
        url: "api/v1/auth/logout",
        method: "POST",
      }),
      async onQueryStarted(arg, { dispatch, queryFulfilled }) {
        try {
          await queryFulfilled;
        } finally {
          dispatch(logout());
        }
      },
    }),

    getMe: builder.query<MeResponse, void>({
      query: () => ({
        url: "api/v1/auth/me",
        method: "GET",
      }),
      providesTags: ["User"],
    }),
  }),
});

export const { useLoginMutation, useLogoutMutation, useGetMeQuery } = authApi;
