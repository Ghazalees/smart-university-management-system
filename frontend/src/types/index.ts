/** Defines shared TypeScript contracts for API entities, roles, and interface state. */

export type RoleName = "Student" | "Professor" | "AdministrativeStaff" | "UniversityPresident";

export interface Department { id: number; name: string; code: string; is_active: boolean; }
export interface Profile {
  phone: string; student_number: string; employee_number: string; bio: string;
  avatar_url: string; job_title: string; office_location: string; website: string;
  preferred_language: string; timezone: string; emergency_contact: Record<string, unknown>;
}
export interface User {
  id: number; username: string; email: string; first_name: string; last_name: string;
  full_name: string; department: Department | null; roles: RoleName[]; permissions: string[];
  profile: Profile | null; is_active: boolean; date_joined?: string; deactivated_at?: string | null;
}
export interface Tokens { access: string; refresh: string; }
export interface Pagination { count: number; page: number; page_size: number; pages: number; next: string | null; previous: string | null; }
export interface ApiEnvelope<T> { success: boolean; message: string; data: T; pagination?: Pagination; }
export interface Role { id: number; name: RoleName; description: string; is_system: boolean; permissions: Array<{ id: number; code: string; name: string; description: string }>; }

export interface DocumentRecord {
  id: number; title: string; document_type: string; content: string;
  access_level: "public" | "authenticated" | "role" | "private"; allowed_roles: RoleName[];
  status: "draft" | "published" | "active" | "archived"; knowledge_enabled: boolean;
  created_by: string; last_updated_by: string | null; created_at: string; updated_at: string;
  published_at: string | null; archived_at: string | null; indexed_at: string | null; index_version: number;
  effective_from: string | null; expires_at: string | null; review_due_at: string | null;
  review_owner: number | null; review_owner_name: string | null; tags: string[];
  version_count: number; is_expired: boolean; governance_status: "current" | "expired" | "review_overdue" | "review_due_soon";
}
export interface DocumentVersion { id: number; version_number: number; snapshot: Record<string, unknown>; content_checksum: string; change_summary: string; created_by_name: string; created_at: string; }

export interface QuestionSource {
  id: number; title: string; document_type: string; updated_at: string; index_version: number;
  effective_from: string | null; expires_at: string | null; is_expired: boolean; excerpt: string; url: string;
}
export interface Question {
  id: number; user: string; text: string; status: "Pending" | "Answered" | "Escalated" | "Failed";
  category: string; priority: string; analysis_confidence: number | null; suggested_workflow: string;
  error_message: string; response: null | {
    answer: string; confidence: number; provider: string; model_name: string; is_documented: boolean;
    sources: QuestionSource[]; citations: Array<Record<string, unknown>>; retrieval_metadata: Record<string, unknown>;
    safety_status: string; latency_ms: number | null; user_rating: -1 | 1 | null; user_feedback: string;
    created_at: string; updated_at: string;
  }; created_at: string; updated_at: string; processed_at: string | null;
}

export interface WorkflowType { id: number; code: string; name: string; description: string; schema: Record<string, unknown>; is_active: boolean; allowed_roles: RoleName[]; }
export interface WorkflowHistory { id: number; event: string; from_status: string; to_status: string; note: string; actor_name: string; created_at: string; }
export interface WorkflowRequest {
  id: number; request_number: string; request_type: number; request_type_detail: WorkflowType;
  requester_detail: User; title: string; description: string; payload: Record<string, unknown>;
  status: string; current_step: string; assigned_to: number | null; assigned_to_detail: User | null;
  decision_reason: string; version: number; submitted_at: string | null; decided_at: string | null;
  created_at: string; updated_at: string; history: WorkflowHistory[];
}

export interface NotificationRecord {
  id: number; title: string; message: string; category: string; priority: "low" | "normal" | "high" | "urgent";
  link: string; metadata: Record<string, unknown>; is_read: boolean; read_at: string | null;
  is_pinned: boolean; pinned_at: string | null; is_snoozed: boolean; snoozed_until: string | null; created_at: string;
}
export interface NotificationPreference { enabled_categories: string[]; in_app_enabled: boolean; email_enabled: boolean; quiet_hours_start: string | null; quiet_hours_end: string | null; muted_until: string | null; updated_at: string; }

export interface Course { id: number; code: string; title: string; credits: number; department?: number | null; is_active?: boolean; }
export interface AcademicClass { id: number; course: number; course_detail: Course; professor: number; professor_name: string; term: string; section: string; weekday: number; start_time: string; end_time: string; location: string; capacity: number; enrolled_count: number; is_active: boolean; }
export interface Enrollment { id: number; academic_class: number; student: number; student_name: string; created_at: string; }
export interface Exam { id: number; academic_class: number; course_title: string; title: string; scheduled_at: string; duration_minutes: number; location: string; instructions: string; }
export interface Grade { id: number; academic_class: number; course_title: string; student: number; student_name: string; score: string; feedback: string; graded_by: number; updated_at: string; }
export interface ClassPerformanceStudent { enrollment_id: number; student_id: number; student_name: string; score: number | null; feedback: string; graded_at: string | null; has_grade: boolean; }
export interface ClassPerformanceReport { average: number | null; minimum: number | null; maximum: number | null; graded_count: number; ungraded_count: number; students: ClassPerformanceStudent[]; }

export interface DegreeRequirement { course_id: number; code: string; title: string; credits: number; category: string; status: "completed" | "in_progress" | "remaining"; score: number | null; minimum_score: number; recommended_term: number | null; }
export interface DegreeProgress { completed_credits: number; total_credits: number; percentage: number; average_score: number | null; categories: Record<string, { total: number; completed: number; credits: number; completed_credits: number }>; requirements: DegreeRequirement[]; }
export interface AcademicRecommendation { code: string; title: string; description: string; priority: string; action_url: string; metadata: Record<string, unknown>; }
export interface CalendarEvent { id: string; type: "class" | "exam" | "workflow" | "review"; title: string; subtitle?: string; start: string; end: string; location?: string; url: string; status: string; }
export interface SearchResult { result_type: string; identifier: number; title: string; subtitle: string; url: string; metadata: Record<string, unknown>; }
export interface ActivityItem { id: number; action: string; entity_type: string; entity_id: string; actor: string; metadata: Record<string, unknown>; created_at: string; }
export interface ExperiencePreference { accent_color: string; density: string; reduced_motion: boolean; high_contrast: boolean; language: string; dashboard_layout: string[]; onboarding_completed: boolean; digest_frequency: string; updated_at: string; }
export interface FeedbackItem { id: number; feedback_type: string; title: string; message: string; page: string; rating: number | null; metadata: Record<string, unknown>; status: string; created_by_name: string; assigned_to: number | null; assigned_to_name: string | null; admin_note: string; created_at: string; updated_at: string; }
export interface AIAnalytics { total_questions: number; answered: number; escalated: number; failed: number; documented_rate: number; escalation_rate: number; average_confidence: number | null; confidence_bands: Record<string, number>; categories: Record<string, number>; top_sources: Array<{ document_id: number; title: string; uses: number }>; trend: Array<{ date: string; value: number }>; }
