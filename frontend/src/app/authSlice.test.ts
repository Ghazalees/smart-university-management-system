/** Verifies the authSlice frontend behavior and regression scenarios. */

import { describe, expect, it, beforeEach } from "vitest";
import reducer, { clearSession, expireSession, setSession, setTokens } from "./authSlice";
import type { User } from "../types";

const user: User = {
  id: 1,
  username: "student",
  email: "student@example.com",
  first_name: "Demo",
  last_name: "Student",
  full_name: "Demo Student",
  department: null,
  roles: ["Student"],
  permissions: ["dashboard.view"],
  profile: null,
  is_active: true,
};

describe("authSlice", () => {
  beforeEach(() => localStorage.clear());

  it("stores a complete session", () => {
    const state = reducer(undefined, setSession({ user, tokens: { access: "access", refresh: "refresh" } }));
    expect(state.user?.username).toBe("student");
    expect(state.refreshToken).toBe("refresh");
    expect(state.sessionExpired).toBe(false);
  });

  it("rotates tokens without losing the user", () => {
    const initial = reducer(undefined, setSession({ user, tokens: { access: "a", refresh: "r" } }));
    const state = reducer(initial, setTokens({ access: "a2", refresh: "r2" }));
    expect(state.user).toEqual(user);
    expect(state.accessToken).toBe("a2");
  });

  it("clears all credentials on logout", () => {
    const initial = reducer(undefined, setSession({ user, tokens: { access: "a", refresh: "r" } }));
    expect(reducer(initial, clearSession())).toEqual({
      user: null,
      accessToken: null,
      refreshToken: null,
      sessionExpired: false,
    });
  });

  it("marks an involuntary logout as an expired session", () => {
    const initial = reducer(undefined, setSession({ user, tokens: { access: "a", refresh: "r" } }));
    expect(reducer(initial, expireSession()).sessionExpired).toBe(true);
  });
});
