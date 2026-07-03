/** Verifies the ProtectedRoute frontend behavior and regression scenarios. */

import { afterEach, describe, expect, it } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { Provider } from "react-redux";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { store } from "../app/store";
import { clearSession, setSession } from "../app/authSlice";
import type { User } from "../types";
import { ProtectedRoute } from "./ProtectedRoute";

const baseUser: User = {
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

function renderRoute(permission?: string) {
  return render(
    <Provider store={store}>
      <MemoryRouter initialEntries={["/secure"]}>
        <Routes>
          <Route path="/login" element={<div>Login screen</div>} />
          <Route path="/403" element={<div>Forbidden screen</div>} />
          <Route element={<ProtectedRoute permission={permission} />}>
            <Route path="/secure" element={<div>Protected content</div>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </Provider>,
  );
}

describe("ProtectedRoute", () => {
  afterEach(() => { act(() => { store.dispatch(clearSession()); }); });

  it("redirects an anonymous visitor to login", () => {
    renderRoute();
    expect(screen.getByText("Login screen")).toBeInTheDocument();
  });

  it("redirects an authenticated user without permission to 403", () => {
    act(() => { store.dispatch(setSession({ user: baseUser, tokens: { access: "a", refresh: "r" } })); });
    renderRoute("users.view");
    expect(screen.getByText("Forbidden screen")).toBeInTheDocument();
  });

  it("renders a protected page for a permitted user", () => {
    act(() => {
      store.dispatch(setSession({
        user: { ...baseUser, permissions: ["users.view"] },
        tokens: { access: "a", refresh: "r" },
      }));
    });
    renderRoute("users.view");
    expect(screen.getByText("Protected content")).toBeInTheDocument();
  });
});
