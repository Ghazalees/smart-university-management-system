/** Provides the reusable AppShell interface component and accessibility behavior. */

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3, Bell, BookOpen, Bot, CalendarDays, ChevronLeft, ChevronRight,
  FileText, GraduationCap, LayoutDashboard, LogOut, Menu, MessageSquareText,
  Moon, Search, ShieldCheck, Sun, UserRound, Users, Workflow, X,
} from "lucide-react";
import { useTheme } from "next-themes";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { clearSession, selectAuth } from "../app/authSlice";
import { useExperiencePreferencesQuery, useLogoutMutation, useUnreadCountQuery } from "../services/api";
import type { RoleName } from "../types";
import { Button } from "./ui";
import { CommandPalette } from "./CommandPalette";
import { OnboardingTour } from "./OnboardingTour";

interface NavItem { label: string; path: string; icon: typeof LayoutDashboard; roles?: RoleName[]; permission?: string; group: string; }
const navItems: NavItem[] = [
  { label: "Overview", path: "/dashboard", icon: LayoutDashboard, group: "Workspace" },
  { label: "Calendar", path: "/calendar", icon: CalendarDays, group: "Workspace" },
  { label: "Knowledge", path: "/documents", icon: FileText, group: "Knowledge" },
  { label: "AI assistant", path: "/questions", icon: Bot, group: "Knowledge" },
  { label: "Requests", path: "/workflows", icon: Workflow, group: "Operations" },
  { label: "Classes", path: "/academics/classes", icon: CalendarDays, group: "Academics" },
  { label: "Exams", path: "/academics/exams", icon: BookOpen, group: "Academics" },
  { label: "Grades", path: "/academics/grades", icon: GraduationCap, group: "Academics" },
  { label: "AI analytics", path: "/analytics", icon: BarChart3, permission: "reports.view_all", group: "Management" },
  { label: "Users", path: "/admin/users", icon: Users, permission: "users.view", group: "Management" },
  { label: "Feedback", path: "/feedback", icon: MessageSquareText, group: "Experience" },
  { label: "Notifications", path: "/notifications", icon: Bell, group: "Account" },
  { label: "Profile", path: "/profile", icon: UserRound, group: "Account" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const { user, refreshToken } = useAppSelector(selectAuth);
  const dispatch = useAppDispatch(); const navigate = useNavigate(); const location = useLocation();
  const { theme, setTheme } = useTheme();
  const [logoutRequest, { isLoading }] = useLogoutMutation();
  const { data: unreadData } = useUnreadCountQuery(undefined, { pollingInterval: 60000 });
  const { data: preferences } = useExperiencePreferencesQuery();

  useEffect(() => {
    function hotkey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); setSearchOpen(true); }
    }
    document.addEventListener("keydown", hotkey); return () => document.removeEventListener("keydown", hotkey);
  }, []);

  useEffect(() => {
    const root = document.documentElement;
    const value = preferences?.data;
    root.dataset.accent = value?.accent_color || "indigo";
    root.dataset.density = value?.density || "comfortable";
    root.classList.toggle("reduce-motion", Boolean(value?.reduced_motion));
    root.classList.toggle("high-contrast", Boolean(value?.high_contrast));
  }, [preferences]);

  const visibleItems = useMemo(() => navItems.filter((item) => {
    if (item.roles && !item.roles.some((role) => user?.roles.includes(role))) return false;
    if (item.permission && !user?.permissions.includes(item.permission) && !user?.permissions.includes("*")) return false;
    return true;
  }), [user]);
  const groups = useMemo(() => [...new Set(visibleItems.map((item) => item.group))], [visibleItems]);
  const currentItem = visibleItems.find((item) => location.pathname === item.path || location.pathname.startsWith(`${item.path}/`));

  async function handleLogout() {
    try { if (refreshToken) await logoutRequest({ refresh: refreshToken }).unwrap(); }
    finally { dispatch(clearSession()); navigate("/login", { replace: true }); }
  }

  const sidebar = <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
    <div className="brand-row"><div className="brand-mark"><ShieldCheck /></div>{!collapsed ? <div><strong>UniFlow</strong><span>Intelligent campus OS</span></div> : null}<button className="icon-button desktop-only" onClick={() => setCollapsed((value) => !value)} aria-label="Toggle navigation">{collapsed ? <ChevronRight /> : <ChevronLeft />}</button><button className="icon-button mobile-only" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X /></button></div>
    <nav className="sidebar-nav" aria-label="Primary navigation">{groups.map((group) => <div className="nav-group" key={group}>{!collapsed ? <span className="nav-group-label">{group}</span> : null}{visibleItems.filter((item) => item.group === group).map((item) => { const Icon = item.icon; return <NavLink key={item.path} to={item.path} onClick={() => setMobileOpen(false)} title={collapsed ? item.label : undefined} className={({ isActive }) => `nav-link ${isActive ? "nav-link-active" : ""}`}><Icon />{!collapsed ? <span>{item.label}</span> : null}{item.path === "/notifications" && (unreadData?.data.count ?? 0) > 0 ? <b className="nav-count">{unreadData?.data.count}</b> : null}</NavLink>; })}</div>)}</nav>
    <div className="sidebar-footer"><div className="user-mini"><div className="avatar">{user?.profile?.avatar_url ? <img src={user.profile.avatar_url} alt="" /> : (user?.first_name || user?.username || "U").slice(0, 1).toUpperCase()}</div>{!collapsed ? <div><strong>{user?.full_name || user?.username}</strong><span>{user?.roles.join(" · ")}</span></div> : null}</div><Button variant="ghost" onClick={handleLogout} disabled={isLoading} aria-label="Log out"><LogOut />{!collapsed ? "Log out" : null}</Button></div>
  </aside>;

  return <div className="app-frame"><CommandPalette open={searchOpen} onClose={() => setSearchOpen(false)} /><OnboardingTour />
    <div className={`mobile-overlay ${mobileOpen ? "mobile-overlay-open" : ""}`} onClick={() => setMobileOpen(false)} /><div className={`mobile-sidebar ${mobileOpen ? "mobile-sidebar-open" : ""}`}>{sidebar}</div><div className="desktop-sidebar">{sidebar}</div>
    <div className="app-main"><header className="topbar"><button className="icon-button mobile-only" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu /></button><div className="topbar-context"><span>{currentItem?.group || "University operations"}</span><strong>{currentItem?.label || user?.department?.name || "Central campus"}</strong></div><button className="global-search-trigger" onClick={() => setSearchOpen(true)}><Search /><span>Search everything</span><kbd>Ctrl K</kbd></button><div className="topbar-actions"><button className="icon-button" onClick={() => setTheme(theme === "dark" ? "light" : "dark")} aria-label="Toggle theme">{theme === "dark" ? <Sun /> : <Moon />}</button><button className="notification-button" onClick={() => navigate("/notifications")} aria-label="Notifications"><Bell />{(unreadData?.data.count ?? 0) > 0 ? <span>{unreadData?.data.count}</span> : null}</button></div></header>
      <main className="content-area"><nav className="breadcrumb" aria-label="Breadcrumb"><NavLink to="/dashboard">Home</NavLink><span>/</span>{currentItem?.group ? <><span>{currentItem.group}</span><span>/</span></> : null}<strong>{currentItem?.label || "Workspace"}</strong></nav>{children}</main>
    </div>
  </div>;
}
