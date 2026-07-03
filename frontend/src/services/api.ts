/** Defines typed RTK Query endpoints and shared API transport behavior for the frontend. */

import { createApi, fetchBaseQuery, type BaseQueryFn, type FetchArgs, type FetchBaseQueryError } from "@reduxjs/toolkit/query/react";
import type { RootState } from "../app/store";
import { expireSession, setTokens } from "../app/authSlice";
import type {
  AcademicClass, AcademicRecommendation, ActivityItem, AIAnalytics, ApiEnvelope, CalendarEvent,
  ClassPerformanceReport, Course, DegreeProgress, DocumentRecord, DocumentVersion, Enrollment, Exam,
  ExperiencePreference, FeedbackItem, Grade, NotificationPreference, NotificationRecord, Question, Role, SearchResult, Tokens, User,
  WorkflowRequest, WorkflowType,
} from "../types";

const rawBaseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL || "/api/v1/",
  prepareHeaders: (headers, { getState }) => {
    const token = (getState() as RootState).auth.accessToken;
    if (token) headers.set("Authorization", `Bearer ${token}`);
    headers.set("X-Requested-With", "XMLHttpRequest");
    return headers;
  },
});

let refreshPromise: Promise<Tokens | null> | null = null;
const baseQueryWithReauth: BaseQueryFn<string | FetchArgs, unknown, FetchBaseQueryError> = async (args, api, extraOptions) => {
  let result = await rawBaseQuery(args, api, extraOptions);
  const url = typeof args === "string" ? args : args.url;
  if (result.error?.status !== 401 || url.startsWith("auth/")) return result;
  const refresh = (api.getState() as RootState).auth.refreshToken;
  if (!refresh) { api.dispatch(expireSession()); return result; }
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const refreshResult = await rawBaseQuery({ url: "auth/refresh", method: "POST", body: { refresh } }, api, extraOptions);
      if (refreshResult.data) {
        const envelope = refreshResult.data as ApiEnvelope<{ tokens: Tokens }>;
        api.dispatch(setTokens(envelope.data.tokens));
        return envelope.data.tokens;
      }
      api.dispatch(expireSession());
      return null;
    })().finally(() => { refreshPromise = null; });
  }
  if (await refreshPromise) result = await rawBaseQuery(args, api, extraOptions);
  return result;
};

export const api = createApi({
  reducerPath: "api",
  baseQuery: baseQueryWithReauth,
  tagTypes: ["Me", "Users", "Roles", "Documents", "Questions", "Workflows", "Notifications", "Academics", "Dashboard", "Experience", "Feedback", "Analytics"],
  endpoints: (builder) => ({
    login: builder.mutation<ApiEnvelope<{ user: User; tokens: Tokens }>, { identifier: string; password: string }>({ query: (body) => ({ url: "auth/login", method: "POST", body }) }),
    logout: builder.mutation<ApiEnvelope<null>, { refresh: string }>({ query: (body) => ({ url: "auth/logout", method: "POST", body }) }),
    changePassword: builder.mutation<ApiEnvelope<null>, { current_password: string; new_password: string }>({ query: (body) => ({ url: "auth/change-password", method: "POST", body }) }),
    me: builder.query<ApiEnvelope<User>, void>({ query: () => "auth/me", providesTags: ["Me"] }),
    updateMe: builder.mutation<ApiEnvelope<User>, Record<string, unknown>>({ query: (body) => ({ url: "auth/me", method: "PATCH", body }), invalidatesTags: ["Me"] }),

    users: builder.query<ApiEnvelope<User[]>, { page?: number; search?: string; role?: string; is_active?: string }>({ query: (params) => ({ url: "users", params }), providesTags: ["Users"] }),
    createUser: builder.mutation<ApiEnvelope<User>, Record<string, unknown>>({ query: (body) => ({ url: "users", method: "POST", body }), invalidatesTags: ["Users", "Dashboard"] }),
    updateUser: builder.mutation<ApiEnvelope<User>, { id: number; body: Record<string, unknown> }>({ query: ({ id, body }) => ({ url: `users/${id}`, method: "PATCH", body }), invalidatesTags: ["Users", "Dashboard"] }),
    deactivateUser: builder.mutation<ApiEnvelope<null>, number>({ query: (id) => ({ url: `users/${id}`, method: "DELETE" }), invalidatesTags: ["Users", "Dashboard"] }),
    reactivateUser: builder.mutation<ApiEnvelope<User>, number>({ query: (id) => ({ url: `users/${id}/reactivate`, method: "POST" }), invalidatesTags: ["Users", "Dashboard"] }),
    assignRoles: builder.mutation<ApiEnvelope<User>, { id: number; role_ids: number[] }>({ query: ({ id, role_ids }) => ({ url: `users/${id}/roles`, method: "PATCH", body: { role_ids } }), invalidatesTags: ["Users", "Roles"] }),
    roles: builder.query<ApiEnvelope<Role[]>, void>({ query: () => "roles", providesTags: ["Roles"] }),

    documents: builder.query<ApiEnvelope<DocumentRecord[]>, { page?: number; search?: string; status?: string; document_type?: string; access_level?: string; include_archived?: string; ordering?: string; governance?: string }>({ query: (params) => ({ url: "documents", params }), providesTags: ["Documents"] }),
    document: builder.query<ApiEnvelope<DocumentRecord>, number>({ query: (id) => `documents/${id}`, providesTags: (_r, _e, id) => [{ type: "Documents", id }] }),
    documentVersions: builder.query<ApiEnvelope<DocumentVersion[]>, number>({ query: (id) => `documents/${id}/versions`, providesTags: (_r, _e, id) => [{ type: "Documents", id }] }),
    createDocument: builder.mutation<ApiEnvelope<DocumentRecord>, Record<string, unknown>>({ query: (body) => ({ url: "documents", method: "POST", body }), invalidatesTags: ["Documents", "Dashboard"] }),
    updateDocument: builder.mutation<ApiEnvelope<DocumentRecord>, { id: number; body: Record<string, unknown> }>({ query: ({ id, body }) => ({ url: `documents/${id}`, method: "PATCH", body }), invalidatesTags: ["Documents"] }),
    archiveDocument: builder.mutation<ApiEnvelope<null>, number>({ query: (id) => ({ url: `documents/${id}`, method: "DELETE" }), invalidatesTags: ["Documents"] }),
    publishDocument: builder.mutation<ApiEnvelope<DocumentRecord>, number>({ query: (id) => ({ url: `documents/${id}/publish`, method: "POST" }), invalidatesTags: ["Documents", "Notifications"] }),
    restoreDocument: builder.mutation<ApiEnvelope<DocumentRecord>, number>({ query: (id) => ({ url: `documents/${id}/restore`, method: "POST" }), invalidatesTags: ["Documents"] }),
    restoreDocumentVersion: builder.mutation<ApiEnvelope<DocumentRecord>, { id: number; version: number }>({ query: ({ id, version }) => ({ url: `documents/${id}/versions/${version}/restore`, method: "POST" }), invalidatesTags: ["Documents"] }),
    reindexDocument: builder.mutation<ApiEnvelope<DocumentRecord>, number>({ query: (id) => ({ url: `documents/${id}/reindex`, method: "POST" }), invalidatesTags: ["Documents"] }),
    importDocuments: builder.mutation<ApiEnvelope<{ created: number; created_ids: number[]; errors: unknown[] }>, { format: string; content: string | unknown[] }>({ query: (body) => ({ url: "documents/import", method: "POST", body }), invalidatesTags: ["Documents", "Dashboard"] }),
    uploadDocument: builder.mutation<ApiEnvelope<DocumentRecord>, FormData>({ query: (body) => ({ url: "documents/upload", method: "POST", body }), invalidatesTags: ["Documents", "Dashboard"] }),

    questions: builder.query<ApiEnvelope<Question[]>, { page?: number; search?: string; status?: string }>({ query: (params) => ({ url: "questions", params }), providesTags: ["Questions"] }),
    createQuestion: builder.mutation<ApiEnvelope<Question>, { text: string }>({ query: (body) => ({ url: "questions", method: "POST", body }), invalidatesTags: ["Questions", "Dashboard"] }),
    generateAnswer: builder.mutation<ApiEnvelope<unknown>, number>({ query: (id) => ({ url: `questions/${id}/answer`, method: "POST" }), invalidatesTags: ["Questions", "Dashboard", "Analytics"] }),
    humanAnswer: builder.mutation<ApiEnvelope<unknown>, { id: number; answer: string; source_ids?: number[] }>({ query: ({ id, ...body }) => ({ url: `questions/${id}/human-answer`, method: "POST", body }), invalidatesTags: ["Questions", "Analytics"] }),
    rateAnswer: builder.mutation<ApiEnvelope<unknown>, { id: number; rating: -1 | 1; comment?: string }>({ query: ({ id, ...body }) => ({ url: `questions/${id}/feedback`, method: "POST", body }), invalidatesTags: ["Questions", "Analytics"] }),

    workflowTypes: builder.query<ApiEnvelope<WorkflowType[]>, void>({ query: () => "workflow-types", providesTags: ["Workflows"] }),
    workflows: builder.query<ApiEnvelope<WorkflowRequest[]>, { page?: number; status?: string; search?: string }>({ query: (params) => ({ url: "workflow-requests", params }), providesTags: ["Workflows"] }),
    createWorkflow: builder.mutation<ApiEnvelope<WorkflowRequest>, Record<string, unknown>>({ query: (body) => ({ url: "workflow-requests", method: "POST", body }), invalidatesTags: ["Workflows", "Dashboard"] }),
    assignWorkflow: builder.mutation<ApiEnvelope<WorkflowRequest>, { id: number; assigned_to: number; expected_version: number }>({ query: ({ id, ...body }) => ({ url: `workflow-requests/${id}/assign`, method: "POST", body }), invalidatesTags: ["Workflows"] }),
    transitionWorkflow: builder.mutation<ApiEnvelope<WorkflowRequest>, { id: number; action: string; note?: string; expected_version: number }>({ query: ({ id, ...body }) => ({ url: `workflow-requests/${id}/transition`, method: "POST", body }), invalidatesTags: ["Workflows", "Notifications", "Dashboard"] }),

    notifications: builder.query<ApiEnvelope<NotificationRecord[]>, { page?: number; unread?: string; category?: string; priority?: string; pinned?: string; include_snoozed?: string }>({ query: (params) => ({ url: "notifications", params }), providesTags: ["Notifications"] }),
    unreadCount: builder.query<ApiEnvelope<{ count: number }>, void>({ query: () => "notifications/unread-count", providesTags: ["Notifications"] }),
    readNotification: builder.mutation<ApiEnvelope<NotificationRecord>, number>({ query: (id) => ({ url: `notifications/${id}/read`, method: "POST" }), invalidatesTags: ["Notifications"] }),
    notificationAction: builder.mutation<ApiEnvelope<NotificationRecord>, { id: number; action: string; snoozed_until?: string }>({ query: ({ id, ...body }) => ({ url: `notifications/${id}/action`, method: "POST", body }), invalidatesTags: ["Notifications"] }),
    readAllNotifications: builder.mutation<ApiEnvelope<{ updated: number }>, void>({ query: () => ({ url: "notifications/read-all", method: "POST" }), invalidatesTags: ["Notifications"] }),
    notificationPreferences: builder.query<ApiEnvelope<NotificationPreference>, void>({ query: () => "notifications/preferences", providesTags: ["Notifications"] }),
    updateNotificationPreferences: builder.mutation<ApiEnvelope<NotificationPreference>, Partial<NotificationPreference>>({ query: (body) => ({ url: "notifications/preferences", method: "PATCH", body }), invalidatesTags: ["Notifications"] }),
    notificationDigest: builder.query<ApiEnvelope<{ period: string; total: number; unread: number; urgent: number; categories: Record<string, number>; highlights: NotificationRecord[] }>, { period?: string }>({ query: (params) => ({ url: "notifications/digest", params }), providesTags: ["Notifications"] }),
    broadcastNotification: builder.mutation<ApiEnvelope<{ created: number }>, { title: string; message: string; category: string; priority?: string; link?: string; role_ids: number[] }>({ query: (body) => ({ url: "notifications/broadcast", method: "POST", body }), invalidatesTags: ["Notifications"] }),

    dashboard: builder.query<ApiEnvelope<Record<string, unknown>>, void>({ query: () => "reports/dashboard", providesTags: ["Dashboard"] }),
    aiAnalytics: builder.query<ApiEnvelope<AIAnalytics>, void>({ query: () => "reports/ai-analytics", providesTags: ["Analytics"] }),
    activityFeed: builder.query<ApiEnvelope<{ items: ActivityItem[] }>, { limit?: number }>({ query: (params) => ({ url: "activity-feed", params }), providesTags: ["Dashboard"] }),

    courses: builder.query<ApiEnvelope<Course[]>, { page?: number; search?: string }>({ query: (params) => ({ url: "courses", params }), providesTags: ["Academics"] }),
    classes: builder.query<ApiEnvelope<AcademicClass[]>, { page?: number; term?: string }>({ query: (params) => ({ url: "classes", params }), providesTags: ["Academics"] }),
    classDetail: builder.query<ApiEnvelope<{ class: AcademicClass; report: ClassPerformanceReport }>, number>({ query: (id) => `classes/${id}`, providesTags: (_r, _e, id) => [{ type: "Academics", id }] }),
    createClass: builder.mutation<ApiEnvelope<AcademicClass>, Record<string, unknown>>({ query: (body) => ({ url: "classes", method: "POST", body }), invalidatesTags: ["Academics", "Dashboard"] }),
    updateClass: builder.mutation<ApiEnvelope<AcademicClass>, { id: number; body: Record<string, unknown> }>({ query: ({ id, body }) => ({ url: `classes/${id}`, method: "PATCH", body }), invalidatesTags: (_r, _e, { id }) => ["Academics", "Dashboard", { type: "Academics", id }] }),
    enrollments: builder.query<ApiEnvelope<Enrollment[]>, { class_id: number; page_size?: number }>({ query: (params) => ({ url: "enrollments", params }), providesTags: ["Academics"] }),
    scheduleSuggestions: builder.mutation<ApiEnvelope<{ suggestions: Array<{ weekday: number; start_time: string; end_time: string; score: number; reason: string }> }>, Record<string, unknown>>({ query: (body) => ({ url: "academics/schedule-suggestions", method: "POST", body }) }),
    exams: builder.query<ApiEnvelope<Exam[]>, { page?: number }>({ query: (params) => ({ url: "exams", params }), providesTags: ["Academics"] }),
    createExam: builder.mutation<ApiEnvelope<Exam>, Record<string, unknown>>({ query: (body) => ({ url: "exams", method: "POST", body }), invalidatesTags: ["Academics", "Notifications", "Dashboard"] }),
    grades: builder.query<ApiEnvelope<Grade[]>, { page?: number; class_id?: number }>({ query: (params) => ({ url: "grades", params }), providesTags: ["Academics"] }),
    saveGrade: builder.mutation<ApiEnvelope<Grade>, Record<string, unknown>>({ query: (body) => ({ url: "grades", method: "POST", body }), invalidatesTags: ["Academics", "Notifications", "Dashboard"] }),
    degreeProgress: builder.query<ApiEnvelope<DegreeProgress>, { student_id?: number } | void>({ query: (params) => ({ url: "academics/degree-progress", params: params || {} }), providesTags: ["Academics"] }),
    academicRecommendations: builder.query<ApiEnvelope<{ progress: DegreeProgress; recommendations: AcademicRecommendation[] }>, { student_id?: number } | void>({ query: (params) => ({ url: "academics/recommendations", params: params || {} }), providesTags: ["Academics"] }),
    academicGoal: builder.query<ApiEnvelope<{ target_gpa: string; target_graduation_term: string; preferred_max_credits: number; updated_at: string }>, void>({ query: () => "academics/goals", providesTags: ["Academics"] }),
    updateAcademicGoal: builder.mutation<ApiEnvelope<unknown>, Record<string, unknown>>({ query: (body) => ({ url: "academics/goals", method: "PATCH", body }), invalidatesTags: ["Academics", "Dashboard"] }),
    calendar: builder.query<ApiEnvelope<{ start: string; end: string; events: CalendarEvent[] }>, { start?: string; end?: string }>({ query: (params) => ({ url: "calendar", params }), providesTags: ["Academics", "Workflows", "Documents"] }),

    globalSearch: builder.query<ApiEnvelope<{ query: string; results: SearchResult[] }>, { q: string; limit?: number }>({ query: (params) => ({ url: "search", params }) }),
    experiencePreferences: builder.query<ApiEnvelope<ExperiencePreference>, void>({ query: () => "experience/preferences", providesTags: ["Experience"] }),
    updateExperiencePreferences: builder.mutation<ApiEnvelope<ExperiencePreference>, Partial<ExperiencePreference>>({ query: (body) => ({ url: "experience/preferences", method: "PATCH", body }), invalidatesTags: ["Experience"] }),
    feedback: builder.query<ApiEnvelope<FeedbackItem[]>, { page?: number; status?: string; type?: string }>({ query: (params) => ({ url: "feedback", params }), providesTags: ["Feedback"] }),
    createFeedback: builder.mutation<ApiEnvelope<FeedbackItem>, Record<string, unknown>>({ query: (body) => ({ url: "feedback", method: "POST", body }), invalidatesTags: ["Feedback"] }),
    manageFeedback: builder.mutation<ApiEnvelope<FeedbackItem>, { id: number; body: Record<string, unknown> }>({ query: ({ id, body }) => ({ url: `feedback/${id}`, method: "PATCH", body }), invalidatesTags: ["Feedback"] }),
  }),
});

export const {
  useLoginMutation, useLogoutMutation, useChangePasswordMutation, useMeQuery, useUpdateMeMutation,
  useUsersQuery, useCreateUserMutation, useUpdateUserMutation, useDeactivateUserMutation, useReactivateUserMutation, useAssignRolesMutation, useRolesQuery,
  useDocumentsQuery, useDocumentQuery, useDocumentVersionsQuery, useCreateDocumentMutation, useUpdateDocumentMutation, useArchiveDocumentMutation, usePublishDocumentMutation, useRestoreDocumentMutation, useRestoreDocumentVersionMutation, useReindexDocumentMutation, useImportDocumentsMutation, useUploadDocumentMutation,
  useQuestionsQuery, useCreateQuestionMutation, useGenerateAnswerMutation, useHumanAnswerMutation, useRateAnswerMutation,
  useWorkflowTypesQuery, useWorkflowsQuery, useCreateWorkflowMutation, useAssignWorkflowMutation, useTransitionWorkflowMutation,
  useNotificationsQuery, useUnreadCountQuery, useReadNotificationMutation, useNotificationActionMutation, useReadAllNotificationsMutation, useNotificationPreferencesQuery, useUpdateNotificationPreferencesMutation, useNotificationDigestQuery, useBroadcastNotificationMutation,
  useDashboardQuery, useAiAnalyticsQuery, useActivityFeedQuery,
  useCoursesQuery, useClassesQuery, useClassDetailQuery, useCreateClassMutation, useUpdateClassMutation, useEnrollmentsQuery, useScheduleSuggestionsMutation, useExamsQuery, useCreateExamMutation, useGradesQuery, useSaveGradeMutation, useDegreeProgressQuery, useAcademicRecommendationsQuery, useAcademicGoalQuery, useUpdateAcademicGoalMutation, useCalendarQuery,
  useGlobalSearchQuery, useExperiencePreferencesQuery, useUpdateExperiencePreferencesMutation,
  useFeedbackQuery, useCreateFeedbackMutation, useManageFeedbackMutation,
} = api;
