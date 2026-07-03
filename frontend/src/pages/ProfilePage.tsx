/** Renders the ProfilePage workspace and coordinates its API-driven interactions. */

import { useState } from "react";
import { Accessibility, BellRing, Globe2, KeyRound, Palette, Pencil, RotateCcw, ShieldCheck, SlidersHorizontal, Target, UserRound } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../app/hooks";
import { clearSession, selectAuth, updateUser } from "../app/authSlice";
import {
  useAcademicGoalQuery,
  useChangePasswordMutation,
  useExperiencePreferencesQuery,
  useUpdateAcademicGoalMutation,
  useUpdateExperiencePreferencesMutation,
  useUpdateMeMutation,
} from "../services/api";
import { Badge, Button, Card, Input, PageHeader, Select, Textarea } from "../components/ui";
import { getErrorMessage } from "../app/formatters";
import { useToast } from "../app/useToast";

const accents = [
  { id: "indigo", label: "Indigo" }, { id: "violet", label: "Violet" },
  { id: "emerald", label: "Emerald" }, { id: "coral", label: "Coral" },
];

export function ProfilePage() {
  const { user } = useAppSelector(selectAuth);
  const [passwordOpen, setPasswordOpen] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [changePassword, passwordState] = useChangePasswordMutation();
  const [updateMe, profileState] = useUpdateMeMutation();
  const { data: preferenceData } = useExperiencePreferencesQuery();
  const [updatePreferences, preferenceState] = useUpdateExperiencePreferencesMutation();
  const isStudent = Boolean(user?.roles.includes("Student"));
  const { data: goalData } = useAcademicGoalQuery(undefined, { skip: !isStudent });
  const [updateGoal, goalState] = useUpdateAcademicGoalMutation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { show } = useToast();
  const preferences = preferenceData?.data;

  async function submitPassword(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const next = String(form.get("new_password"));
    if (next !== String(form.get("confirm_password"))) { show("New passwords do not match", "error"); return; }
    try {
      await changePassword({ current_password: String(form.get("current_password")), new_password: next }).unwrap();
      show("Password changed. Sign in again."); dispatch(clearSession()); navigate("/login");
    } catch (reason) { show(getErrorMessage(reason), "error"); }
  }

  async function submitProfile(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const response = await updateMe({
        first_name: String(form.get("first_name")), last_name: String(form.get("last_name")), email: String(form.get("email")),
        profile: {
          phone: String(form.get("phone") || ""), student_number: String(form.get("student_number") || ""), employee_number: String(form.get("employee_number") || ""),
          bio: String(form.get("bio") || ""), avatar_url: String(form.get("avatar_url") || ""), job_title: String(form.get("job_title") || ""),
          office_location: String(form.get("office_location") || ""), website: String(form.get("website") || ""), preferred_language: String(form.get("preferred_language") || "en"),
          timezone: String(form.get("timezone") || "UTC"), emergency_contact: { name: String(form.get("emergency_name") || ""), phone: String(form.get("emergency_phone") || "") },
        },
      }).unwrap();
      dispatch(updateUser(response.data)); setEditOpen(false); show("Profile updated");
    } catch (reason) { show(getErrorMessage(reason), "error"); }
  }

  async function savePreference(body: Record<string, unknown>, message = "Experience preference saved") {
    try { await updatePreferences(body).unwrap(); show(message); }
    catch (reason) { show(getErrorMessage(reason), "error"); }
  }

  async function submitGoal(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    try {
      await updateGoal({ target_gpa: Number(form.get("target_gpa")), target_graduation_term: String(form.get("target_graduation_term")), preferred_max_credits: Number(form.get("preferred_max_credits")) }).unwrap();
      show("Academic goal updated");
    } catch (reason) { show(getErrorMessage(reason), "error"); }
  }

  const emergency = (user?.profile?.emergency_contact || {}) as { name?: string; phone?: string };
  return <div className="page-stack">
    <PageHeader title="Profile, goals and experience" description="Manage your university identity, accessibility preferences, personal goals and account security from one place." />

    <section className="profile-overview-grid">
      <Card className="profile-card profile-main-card">
        <div className="profile-hero"><span className="avatar avatar-large">{user?.profile?.avatar_url ? <img src={user.profile.avatar_url} alt="" /> : (user?.first_name || user?.username || "U")[0].toUpperCase()}</span><div><p className="eyebrow">University identity</p><h2>{user?.full_name}</h2><p>{user?.email}</p><div className="badge-row">{user?.roles.map((role) => <Badge key={role} tone="info">{role}</Badge>)}</div></div></div>
        {!editOpen ? <>
          <dl className="profile-detail-list"><div><dt>Username</dt><dd>{user?.username}</dd></div><div><dt>Department</dt><dd>{user?.department?.name || "—"}</dd></div><div><dt>Job title</dt><dd>{user?.profile?.job_title || "—"}</dd></div><div><dt>Office</dt><dd>{user?.profile?.office_location || "—"}</dd></div><div><dt>Phone</dt><dd>{user?.profile?.phone || "—"}</dd></div><div><dt>Student / employee ID</dt><dd>{user?.profile?.student_number || user?.profile?.employee_number || "—"}</dd></div><div><dt>Website</dt><dd>{user?.profile?.website || "—"}</dd></div><div><dt>Timezone</dt><dd>{user?.profile?.timezone || "UTC"}</dd></div><div className="profile-bio-row"><dt>Bio</dt><dd>{user?.profile?.bio || "No biography added yet."}</dd></div></dl>
          <Button variant="secondary" onClick={() => setEditOpen(true)}><Pencil />Edit complete profile</Button>
        </> : <form className="form-grid profile-form" onSubmit={submitProfile}>
          <Input name="first_name" label="First name" defaultValue={user?.first_name} required /><Input name="last_name" label="Last name" defaultValue={user?.last_name} required />
          <Input name="email" label="Email" type="email" defaultValue={user?.email} required /><Input name="phone" label="Phone" defaultValue={user?.profile?.phone} />
          <Input name="job_title" label="Job title" defaultValue={user?.profile?.job_title} /><Input name="office_location" label="Office location" defaultValue={user?.profile?.office_location} />
          <Input name="student_number" label="Student number" defaultValue={user?.profile?.student_number} /><Input name="employee_number" label="Employee number" defaultValue={user?.profile?.employee_number} />
          <Input name="avatar_url" label="Avatar URL" type="url" defaultValue={user?.profile?.avatar_url} /><Input name="website" label="Website" type="url" defaultValue={user?.profile?.website} />
          <Select name="preferred_language" label="Preferred language" defaultValue={user?.profile?.preferred_language || "en"}><option value="en">English</option><option value="fa">فارسی</option></Select>
          <Select name="timezone" label="Timezone" defaultValue={user?.profile?.timezone || "UTC"}><option value="UTC">UTC</option><option value="Asia/Tehran">Asia/Tehran</option><option value="Asia/Baku">Asia/Baku</option><option value="America/Toronto">America/Toronto</option></Select>
          <Input name="emergency_name" label="Emergency contact name" defaultValue={emergency.name} /><Input name="emergency_phone" label="Emergency contact phone" defaultValue={emergency.phone} />
          <div className="form-span-2"><Textarea name="bio" label="Bio" rows={4} defaultValue={user?.profile?.bio} /></div>
          <div className="modal-actions form-span-2"><Button type="button" variant="secondary" onClick={() => setEditOpen(false)}>Cancel</Button><Button disabled={profileState.isLoading}>{profileState.isLoading ? "Saving…" : "Save profile"}</Button></div>
        </form>}
      </Card>

      <div className="profile-side-stack">
        <Card className="security-card"><span><ShieldCheck /></span><h2>Account security</h2><p>Short-lived access tokens, rotating refresh tokens, lockout protection and server-side authorization protect every privileged action.</p><div className="security-note"><UserRound /><span><strong>Role-protected access</strong><small>{user?.permissions.length ?? 0} effective permissions are enforced by the API.</small></span></div><Button variant="secondary" onClick={() => setPasswordOpen((value) => !value)}><KeyRound />{passwordOpen ? "Close password form" : "Change password"}</Button>{passwordOpen ? <form className="form-stack security-form" onSubmit={submitPassword}><Input name="current_password" type="password" label="Current password" required /><Input name="new_password" type="password" label="New password" minLength={8} required /><Input name="confirm_password" type="password" label="Confirm new password" minLength={8} required /><Button disabled={passwordState.isLoading}>{passwordState.isLoading ? "Changing…" : "Change password"}</Button></form> : null}</Card>

        {isStudent ? <Card className="goal-card"><div className="card-title-row"><span className="soft-icon"><Target /></span><div><h2>Academic target</h2><p>Recommendations adapt to this goal.</p></div></div><form className="form-stack" onSubmit={submitGoal}><Input name="target_gpa" label="Target average (0–100)" type="number" min={0} max={100} step="0.1" defaultValue={goalData?.data.target_gpa || "75"} /><Input name="target_graduation_term" label="Target graduation term" defaultValue={goalData?.data.target_graduation_term || ""} placeholder="Spring 2027" /><Input name="preferred_max_credits" label="Preferred maximum credits" type="number" min={3} max={30} defaultValue={goalData?.data.preferred_max_credits || 15} /><Button disabled={goalState.isLoading}>{goalState.isLoading ? "Saving…" : "Update goal"}</Button></form></Card> : null}
      </div>
    </section>

    <Card className="preference-card">
      <div className="card-title-row"><span className="soft-icon"><SlidersHorizontal /></span><div><h2>Experience preferences</h2><p>Personalize density, accessibility, language and notification digests. Preferences follow your account.</p></div></div>
      <div className="preference-grid">
        <div className="preference-group"><div className="preference-heading"><Palette /><div><strong>Accent color</strong><span>Choose the visual identity of your workspace.</span></div></div><div className="accent-picker">{accents.map((accent) => <button type="button" key={accent.id} className={`accent-option accent-${accent.id} ${preferences?.accent_color === accent.id ? "accent-active" : ""}`} onClick={() => void savePreference({ accent_color: accent.id })}><i /><span>{accent.label}</span></button>)}</div></div>
        <div className="preference-group"><div className="preference-heading"><Accessibility /><div><strong>Accessibility</strong><span>Reduce motion and increase visual contrast.</span></div></div><label className="toggle-setting"><input type="checkbox" checked={Boolean(preferences?.reduced_motion)} onChange={(event) => void savePreference({ reduced_motion: event.target.checked })} /><span><strong>Reduced motion</strong><small>Minimizes decorative animations.</small></span></label><label className="toggle-setting"><input type="checkbox" checked={Boolean(preferences?.high_contrast)} onChange={(event) => void savePreference({ high_contrast: event.target.checked })} /><span><strong>High contrast</strong><small>Strengthens borders and readable contrast.</small></span></label></div>
        <div className="preference-group"><div className="preference-heading"><Globe2 /><div><strong>Language and density</strong><span>Control interface spacing and language direction.</span></div></div><Select label="Interface density" value={preferences?.density || "comfortable"} onChange={(event) => void savePreference({ density: event.target.value })}><option value="comfortable">Comfortable</option><option value="compact">Compact</option></Select><Select label="Interface language" value={preferences?.language || "en"} onChange={(event) => void savePreference({ language: event.target.value })}><option value="en">English</option><option value="fa">فارسی</option></Select></div>
        <div className="preference-group"><div className="preference-heading"><BellRing /><div><strong>Digest and onboarding</strong><span>Choose summary frequency or restart the guided tour.</span></div></div><Select label="Notification digest" value={preferences?.digest_frequency || "daily"} onChange={(event) => void savePreference({ digest_frequency: event.target.value })}><option value="off">Off</option><option value="daily">Daily</option><option value="weekly">Weekly</option></Select><Button type="button" variant="secondary" onClick={() => void savePreference({ onboarding_completed: false }, "Onboarding tour will restart on the next page load")} disabled={preferenceState.isLoading}><RotateCcw />Restart onboarding tour</Button></div>
      </div>
    </Card>
  </div>;
}
