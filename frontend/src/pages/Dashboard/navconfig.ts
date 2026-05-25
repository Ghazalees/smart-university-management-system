export const navConfig = {
  AdministrativeStaff: [
    { name: "Dashboard", path: "/dashboard", icon: "LayoutDashboard" },
    { name: "User Management", path: "/admin/users", icon: "Users" },
    { name: "Workflow", path: "/admin/workflow", icon: "Workflow" },
  ],
  UniversityPresident: [
    { name: "Overview", path: "/dashboard", icon: "PieChart" },
    { name: "Analytics", path: "/president/analytics", icon: "TrendingUp" },
    { name: "Approvals", path: "/president/approvals", icon: "CheckCircle" },
  ],
  Professor: [
    { name: "My Classes", path: "/dashboard", icon: "BookOpen" },
    { name: "Students", path: "/professor/students", icon: "GraduationCap" },
    { name: "Submissions", path: "/professor/submissions", icon: "FileText" },
  ],
  Student: [
    { name: "Dashboard", path: "/dashboard", icon: "LayoutDashboard" },
    { name: "My Courses", path: "/student/courses", icon: "BookOpen" },
    { name: "Grades", path: "/student/grades", icon: "GraduationCap" },
  ],
};
