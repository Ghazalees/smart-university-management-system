import { Navigate, Outlet } from "react-router-dom";
import { useAppSelector } from "../hooks/redux";
import { DashboardLayout } from "../components/layout/DashboardLayout"; // <-- 1. Import it here

interface ProtectedRouteProps {
  allowedRoles?: string[];
}

export const ProtectedRoute = ({ allowedRoles }: ProtectedRouteProps) => {
  const { accessToken, role } = useAppSelector((state: any) => state.auth);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && (!role || !allowedRoles.includes(role))) {
    return <Navigate to="/dashboard" replace />;
  }

  // 2. Wrap the Outlet! Every child route now automatically gets the layout.
  return (
    <DashboardLayout>
      <Outlet />
    </DashboardLayout>
  );
};
