/** Provides the reusable ProtectedRoute interface component and accessibility behavior. */

import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAppSelector } from "../app/hooks";
import { selectAuth } from "../app/authSlice";
import type { RoleName } from "../types";

export function ProtectedRoute({ roles, permission }: { roles?: RoleName[]; permission?: string }) {
  const { user, accessToken } = useAppSelector(selectAuth);
  const location = useLocation();
  if (!accessToken || !user) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  const hasRole = !roles || roles.some((role) => user.roles.includes(role));
  const hasPermission = !permission || user.permissions.includes(permission) || user.permissions.includes("*");
  if (!hasRole || !hasPermission) return <Navigate to="/403" replace />;
  return <Outlet />;
}
