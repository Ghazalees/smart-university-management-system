// src/pages/DashboardPage.tsx
import { useSelector } from "react-redux";
import { AdminDashboard } from "./Admin";
import { PresidentDashboard } from "./President";
import { ProfessorDashboard } from "./Professor";
import { StudentDashboard } from "./Student";

export const Dashboard = () => {
  const { role } = useSelector((state: any) => state.auth);
  console.log(role);
  return (
    <div className="p-6">
      {role === "AdministrativeStaff" && <AdminDashboard />}
      {role === "UniversityPresident" && <PresidentDashboard />}
      {role === "Professor" && <ProfessorDashboard />}
      {role === "Student" && <StudentDashboard />}
      {!role && <div>Loading...</div>}
    </div>
  );
};
