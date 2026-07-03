/** Stores authenticated user state, access tokens, and session lifecycle actions. */

import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import type { RootState } from "./store";
import type { Tokens, User } from "../types";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  sessionExpired: boolean;
}

const emptyState: AuthState = {
  user: null,
  accessToken: null,
  refreshToken: null,
  sessionExpired: false,
};

function loadState(): AuthState {
  try {
    const raw = localStorage.getItem("smart-university-auth");
    if (!raw) return emptyState;
    const parsed = JSON.parse(raw) as Partial<AuthState>;
    return {
      user: parsed.user ?? null,
      accessToken: parsed.accessToken ?? null,
      refreshToken: parsed.refreshToken ?? null,
      sessionExpired: false,
    };
  } catch {
    localStorage.removeItem("smart-university-auth");
    return emptyState;
  }
}

function persist(state: AuthState) {
  localStorage.setItem(
    "smart-university-auth",
    JSON.stringify({
      user: state.user,
      accessToken: state.accessToken,
      refreshToken: state.refreshToken,
    }),
  );
}

const authSlice = createSlice({
  name: "auth",
  initialState: loadState(),
  reducers: {
    setSession(
      state,
      action: PayloadAction<{ user: User; tokens: Tokens }>,
    ) {
      state.user = action.payload.user;
      state.accessToken = action.payload.tokens.access;
      state.refreshToken = action.payload.tokens.refresh;
      state.sessionExpired = false;
      persist(state);
    },
    setTokens(state, action: PayloadAction<Tokens>) {
      state.accessToken = action.payload.access;
      state.refreshToken = action.payload.refresh;
      state.sessionExpired = false;
      persist(state);
    },
    updateUser(state, action: PayloadAction<User>) {
      state.user = action.payload;
      persist(state);
    },
    expireSession(state) {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.sessionExpired = true;
      localStorage.removeItem("smart-university-auth");
    },
    clearSession(state) {
      state.user = null;
      state.accessToken = null;
      state.refreshToken = null;
      state.sessionExpired = false;
      localStorage.removeItem("smart-university-auth");
    },
  },
});

export const { setSession, setTokens, updateUser, expireSession, clearSession } =
  authSlice.actions;
export const selectAuth = (state: RootState) => state.auth;
export const selectUser = (state: RootState) => state.auth.user;
export default authSlice.reducer;
