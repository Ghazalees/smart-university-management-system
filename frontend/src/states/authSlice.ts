import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";
import type { AuthState, CredentialsPayload } from "../types/auth";

const storedAuth = localStorage.getItem("auth");

const initialState: AuthState = storedAuth
  ? JSON.parse(storedAuth)
  : {
      user: null,
      accessToken: null,
      role: null,
    };

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (state, action: PayloadAction<CredentialsPayload>) => {
      const { user, accessToken, role } = action.payload;

      state.user = user;
      state.accessToken = accessToken;
      state.role = role;

      localStorage.setItem("auth", JSON.stringify(state));
    },

    logout: (state) => {
      state.user = null;
      state.accessToken = null;
      state.role = null;

      localStorage.removeItem("auth");
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
