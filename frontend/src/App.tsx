import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import { ForgotPassword } from "./pages/ForgotPassword";
import Landing from "./pages/Landing/Landing";
import { Dashboard } from "./pages/Dashboard/Dashboard";
import { ProtectedRoute } from "./middleware/ProtectedRoute";
import UserManagement from "./pages/Admin/UserManagement";

// // Sprint 2 Pages (We will create these next)
// import UserManagement from "./pages/Admin/UserManagement";
// import RoleMatrix from "./pages/Admin/RoleMatrix";
// import DocumentsCenter from "./pages/Documents/DocumentsCenter";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />

      {/* Shared Authenticated Routes */}
      <Route element={<ProtectedRoute />}>
        <Route path="/dashboard" element={<Dashboard />} />
        {/* <Route path="/documents" element={<DocumentsCenter />} /> */}
      </Route>

      {/* Highly Restricted Admin Routes */}
      <Route
        element={
          <ProtectedRoute
            allowedRoles={["AdministrativeStaff", "UniversityPresident"]}
          />
        }
      >
        <Route path="/admin/users" element={<UserManagement />} />
        {/* <Route path="/admin/roles" element={<RoleMatrix />} /> */}
      </Route>
    </Routes>
  );
}
