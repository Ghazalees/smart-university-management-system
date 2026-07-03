/** Declares the application route tree and permission-protected workspaces. */

import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { UsersPage } from "./pages/UsersPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { QuestionsPage } from "./pages/QuestionsPage";
import { WorkflowsPage } from "./pages/WorkflowsPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { ClassesPage } from "./pages/ClassesPage";
import { ExamsPage } from "./pages/ExamsPage";
import { GradesPage } from "./pages/GradesPage";
import { ProfilePage } from "./pages/ProfilePage";
import { CalendarPage } from "./pages/CalendarPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { FeedbackPage } from "./pages/FeedbackPage";
import { DesignSystemPage } from "./pages/DesignSystemPage";
import { ForbiddenPage, NotFoundPage } from "./pages/ErrorPages";

function ShellRoute({ children }: { children: React.ReactNode }) { return <AppShell>{children}</AppShell>; }
export default function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/403" element={<ForbiddenPage />} />
    <Route element={<ProtectedRoute />}>
      <Route path="/dashboard" element={<ShellRoute><DashboardPage /></ShellRoute>} />
      <Route path="/calendar" element={<ShellRoute><CalendarPage /></ShellRoute>} />
      <Route path="/documents" element={<ShellRoute><DocumentsPage /></ShellRoute>} />
      <Route path="/documents/:id" element={<ShellRoute><DocumentsPage /></ShellRoute>} />
      <Route path="/questions" element={<ShellRoute><QuestionsPage /></ShellRoute>} />
      <Route path="/workflows" element={<ShellRoute><WorkflowsPage /></ShellRoute>} />
      <Route path="/workflows/:id" element={<ShellRoute><WorkflowsPage /></ShellRoute>} />
      <Route path="/notifications" element={<ShellRoute><NotificationsPage /></ShellRoute>} />
      <Route path="/academics/classes" element={<ShellRoute><ClassesPage /></ShellRoute>} />
      <Route path="/academics/exams" element={<ShellRoute><ExamsPage /></ShellRoute>} />
      <Route path="/academics/grades" element={<ShellRoute><GradesPage /></ShellRoute>} />
      <Route path="/profile" element={<ShellRoute><ProfilePage /></ShellRoute>} />
      <Route path="/feedback" element={<ShellRoute><FeedbackPage /></ShellRoute>} />
      <Route path="/design-system" element={<ShellRoute><DesignSystemPage /></ShellRoute>} />
    </Route>
    <Route element={<ProtectedRoute permission="users.view" />}><Route path="/admin/users" element={<ShellRoute><UsersPage /></ShellRoute>} /></Route>
    <Route element={<ProtectedRoute permission="reports.view_all" />}><Route path="/analytics" element={<ShellRoute><AnalyticsPage /></ShellRoute>} /></Route>
    <Route path="/" element={<Navigate to="/dashboard" replace />} />
    <Route path="*" element={<NotFoundPage />} />
  </Routes>;
}
