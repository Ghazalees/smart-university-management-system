import { Navigate, Outlet } from "react-router-dom";
import { useAppSelector } from "../hooks/redux";

export const ProtectedRoute = () => {
  const { accessToken } = useAppSelector((state: any) => state.auth);

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <Outlet />;
};
